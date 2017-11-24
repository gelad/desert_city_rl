"""
    This file contains game logic objects.
"""
import actions
import raycasting
import fov
import los
import pathfinding
import effects
import events
import abilities
import dataset
import generation

import random
import pickle
import copy
import threading
from math import hypot
from math import ceil

# profiling code

#import cProfile


# class ProfiledThread(threading.Thread):
#     # Overrides threading.Thread.run()
#     def run(self):
#         profiler = cProfile.Profile()
#         try:
#             return profiler.runcall(threading.Thread.run, self)
#         finally:
#             profiler.dump_stats('myprofile-%d.profile' % (self.ident,))

class Cell:
    """
        Class represents a single cell in location grid
    """

    def __init__(self, tile_id, blocks_move=False, blocks_los=False, explored=False, pass_cost=1):
        self.explored = explored  # is tile explored?
        self.tile = tile_id  # tile type for drawing purposes (i.e. 'WALL', 'FLOOR')
        self.pass_cost = pass_cost  # movement cost coefficient (for creating difficult terrain)
        self.blocks_move = blocks_move  # is tile blocking movement?
        self.blocks_los = blocks_los  # is tile blocking line of sight?
        self.entities = []  # entities, positioned in this tile

    def is_movement_allowed(self):
        """ Method returns if tile is passable """
        if self.blocks_move:
            return False
        for ent in self.entities:
            if ent.occupies_tile:
                return False
        return True

    def get_occupying_entity(self):
        """ Method returns occupying entity """
        ent_oc = None
        for ent in self.entities:
            if ent.occupies_tile:
                ent_oc = ent
                break
        return ent_oc

    def get_move_cost(self):
        """ Method returns movement cost coefficient to cell """
        mc = 1
        mc *= self.pass_cost
        for ent in self.entities:
            mc *= ent.pass_cost
        return mc

    def get_cell_graphics(self):
        """ Method returns graphical representation of a tile """
        tile = dataset.get_tile(self.tile)
        char = tile[0]
        color = tile[1]
        bgcolor = tile[2]
        brk = False
        for ent in self.entities:  # iterate through list of entities,if there are any, display them instead of tile
            char = ent.char
            color = ent.color
            if not color:
                color = [255, 255, 255]
            if ent.occupies_tile:  # check if there is entity, occupying tile - display it on top
                color = ent.color
                brk = True
            if len(self.entities) > 1:  # if there are multiple items, replace bgcolor
                bgcolor = self.entities[0].color
                if color == bgcolor:
                    bgcolor = [c - 50 for c in bgcolor]
                    i = 0
                    for c in bgcolor:
                        if c < 0:
                            bgcolor[i] = 0
                        i += 1
            if brk:
                break
        return [char, color, bgcolor]

    def is_there_a(self, thing):
        """ Method for checking some kind of entity present in cell(monster, door, item, etc) """
        for ent in self.entities:
            if isinstance(ent, thing):
                return ent
        return False

    def is_transparent(self):
        """ Method that returns if the cell is transparent for light """
        if self.blocks_los:  # check if tile blocks los itself
            return False
        for ent in self.entities:  # check if any of placed entities blocks los
            if ent.blocks_los:
                return False
        return True


class Entity:
    """
        Base class for all game entities - monsters, items, walls, etc.
    """

    def __init__(self, name='', data_id='', description='', char=' ', color=None, location=None, position=None,
                 weight=0, pass_cost=1, occupies_tile=False, blocks_los=False, blocks_shots=0):
        self.name = name  # entity name
        self.data_id = data_id  # id in Entity data(base)
        self.description = description  # entity's description
        self.location = location  # Location object, where entity is placed
        self.position = position  # (x, y) tuple, represents position in the location
        self._weight = weight  # weight of an entity, to calculate various things
        self.occupies_tile = occupies_tile  # entity occupy tile? (no other occupying entity can be placed there)
        self.blocks_los = blocks_los  # is it blocking line of sight? walls do, monsters (usually) don't
        self.blocks_shots = blocks_shots  # is it blocking shots? if yes, percent of shots blocked
        self.pass_cost = pass_cost  # movement cost coefficient (for creating difficult terrain)
        self.char = char  # char that represents entity in graphics ('@')
        self.color = color  # entity char color
        self.effects = []  # entity effects

    @property
    def weight(self):
        """ Weight property - overridden in some classes """
        return self._weight

    def __str__(self):
        """ Method returns string representation of an entity - it's name """
        return self.name

    def relocate(self, x, y):
        """ Movement method, just moves entity to (x, y). """
        # checks if entity is positioned in location
        if self.position:
            # check if new position is in the location boundaries
            if self.location.is_in_boundaries(x, y):
                # remove from old cell
                old_x = self.position[0]  # remember old position to update path map
                old_y = self.position[1]
                self.location.cells[self.position[0]][self.position[1]].entities.remove(self)
                self.location.cells[x][y].entities.append(self)  # add to new cell
                self.position = (x, y)  # update entity position
                if self.occupies_tile or self.pass_cost != 1:  # if entity blocks or impairs movement
                    self.location.path_map_update(x, y)
                    self.location.path_map_update(old_x, old_y)  # update path map
                events.Event('location', {'type': 'entity_moved', 'entity': self})  # fire an event
                msg = self.name + 'relocated to ' + str(x) + ':' + str(y)
                Game.add_message(msg, 'DEBUG', [255, 255, 255])
                return True
        else:
            raise Exception('Attempted to relocate entity not positioned in any location. ', self.name)
        return False

    def get_effect(self, effect):
        """ Get resulting effect magnitude (if many effects of same type present - sum of them) """
        magn = 0  # resulting effect magnitude
        for ef in self.effects:  # iterate through effects and calculate resulting magnitude
            if ef.eff == effect:
                magn += ef.magnitude
        return magn


class Strike:
    """ Class for strike - damage, dmg_type, strike type, modificators """
    def __init__(self, strike_type, damage=0, dmg_type='pure', mods=None):
        self.strike_type = strike_type  # type of strike - melee, projectile, dot_tick etc
        self.damage = damage  # damage value
        self.dmg_type = dmg_type  # damage type
        if mods:  # strike modificators dict
            self.mods = mods
        else:
            self.mods = {}


class BattleEntity(Entity):
    """
        Mixin class, adds combat related functionality to the Entity.
        Hp, taking/inflicting damage, that kind of stuff.
    """

    def __init__(self, hp, armor=None, resist=None, dead=False, corpse=''):
        self._hp = hp  # current hitpoints
        self._maxhp = hp  # maximum hitpoints
        self.corpse = corpse  # corpse entity, generated when BE dies. If empty - generic corpse is generated.
        if armor:  # physical armor
            self.armor = armor
        else:
            self.armor = {'bashing': 0, 'slashing': 0, 'piercing': 0}
        if resist:  # magic resistances
            self.resist = resist
        else:
            self.resist = {'fire': 0, 'cold': 0, 'lightning': 0, 'poison': 0, 'acid': 0,
                           'mental': 0, 'death': 0, 'strange': 0}
        self.dead = dead  # is BE dead

    @property
    def maxhp(self):
        """ Maximum hp getter (with effects) """
        return self._maxhp

    @property
    def hp(self):
        """ Current hp getter """
        return self._hp

    @hp.setter
    def hp(self, value):
        """ Current hp setter """
        result_hp = value
        if result_hp > self.maxhp:  # if hp raised higher than max - lower it to max
            self._hp = self.maxhp
        else:
            self._hp = result_hp

    def take_damage(self, damage, dmg_type='pure', attacker=None):
        """ This method should be called if entity is damaged """
        self.hp -= damage
        # fire an Entity event
        events.Event(self, {'type': 'damaged', 'attacker': attacker, 'damage': damage, 'dmg_type': dmg_type})
        if self.location:  # fire location event
            events.Event(self.location, {'type': 'entity_damaged', 'attacker': attacker,
                                         'target': self, 'damage': damage, 'dmg_type': dmg_type})
        if self.hp <= 0 and not self.dead:  # check if self is < 0 hp and not dead
            self.dead = True
            self.location.dead.append(self)  # add BE to dead list, waiting for removal
        return damage

    def deal_damage(self, target, damage, dmg_type):
        """ Method for dealing damage """
        if isinstance(target, BattleEntity):
            damage = determine_number(damage)
            return target.take_damage(damage=damage, dmg_type=dmg_type, attacker=self)  # inflict that damage to target
        else:
            raise Exception('Attempted to damage non-BattleEntity entity. ', self.name)

    def take_strike(self, strike, attacker=None):
        """ Method that is called when BattleEntity receives a strike """
        strike.damage = determine_number(strike.damage) # determine exact damage before striking
        if strike.dmg_type == 'pure':  # if 'pure' damage inflict it without any protection
            resulting_damage = strike.damage
        else:
            damage = strike.damage
            dmg_type = strike.dmg_type
            if strike.strike_type == 'melee' or strike.strike_type == 'projectile':
                if isinstance(self, Equipment):  # shield blocking if BE has equipment
                    if 'ignore_shield' not in strike.mods:
                        shield = None
                        for item in self.equipment.values():  # check if any shields equipped
                            if item:
                                if isinstance(item, ItemShield):
                                    if item.durability > 0:
                                        shield = item
                                        break  # shield found - break
                        if shield:  # if valid shield found
                            dmg_before_block = damage  # remember damage before block
                            # damage is damage passed through shield
                            damage = shield.block(damage=damage, dmg_type=dmg_type)
                            if damage != dmg_before_block and isinstance(self, Player):
                                msg = 'Your ' + shield.name + ' blocks ' + str(dmg_before_block - damage) + ' damage.'
                                Game.add_message(msg, 'PLAYER', [255, 255, 255])
            protection = self.get_protection(dmg_type)  # get (armor, block) tuple
            if protection[0] > 0 and 'ignore_protection' in strike.mods:
                protection = (0, 0)
            # at 100 armor - 50% reduction
            if protection[0] == -100:  # to prevent division by zero
                reduce = protection[0]
            elif protection[0] < 0:  # if vulnerability instead of reduction
                reduce = -1 * protection[0] / (100 + protection[0])
            else:
                reduce = protection[0] / (100 + protection[0])
            resulting_damage = ceil(damage * (1 - reduce) - protection[1])
        if resulting_damage < 0:
            resulting_damage = 0
        # if resulting_damage > 0:  # if resulting damage above 0
        return self.take_damage(damage=resulting_damage, dmg_type=strike.dmg_type, attacker=attacker)  # take damage

    def land_strike(self, strike, target):
        """ Method that lands a strike on target """
        if isinstance(target, BattleEntity):
            strike.damage = determine_number(strike.damage)  # determine exact damage before striking
            # fire an Entity event before strike - can be modified by abilities
            events.Event(self, {'type': 'before_strike', 'target': target, 'strike': strike})
            res_dmg = target.take_strike(strike=strike, attacker=self)  # inflict that strike to target
            events.Event(self, {'type': 'after_strike', 'target': target, 'strike': strike, 'damage': res_dmg})
            return res_dmg
        else:
            raise Exception('Attempted to damage non-BattleEntity entity. ', self.name)

    def heal(self, heal, healer=None):
        """ This method should be called if entity is healed  """
        heal = determine_number(heal)  # determine exact healing before striking
        hp_before = self.hp  # remember hp before heal to calculate actual healed ammount
        self.hp += heal  # add hp
        healed_hp = self.hp - hp_before
        msg = self.name + ' is healed for ' + str(healed_hp) + ' HP.'
        Game.add_message(msg, 'PLAYER', [0, 255, 0])
        # fire an Entity event
        events.Event(self, {'type': 'healed', 'healer': healer, 'heal': healed_hp})
        if self.location:  # fire location event
            events.Event(self.location, {'type': 'entity_healed', 'healer': healer,
                                         'target': self, 'heal': healed_hp})
        return healed_hp

    def get_protection(self, dmg_type):
        """ Method to get protection (both armor and block) to specific damage type """
        # TODO: add immunity effects, and return 'immune' ?
        prot = 0  # protection  mitigation (% reduce)
        if dmg_type in self.armor.keys():
            prot = self.armor[dmg_type]
        if dmg_type in self.resist.keys():
            prot = self.resist[dmg_type]
        prot += self.get_effect('RESIST_' + dmg_type.upper())  # add resistance/armor effects if any
        block = self.get_effect('BLOCK_' + dmg_type.upper())  # damage block ammount
        return prot, block  # return protection parameters

    def death(self):
        """ Abstract method that is called when BattleEntity dies """
        raise NotImplementedError

    def get_corpse(self):
        """ Method to get corpse Entity """
        if self.corpse == '':  # if default corpse
            corpse = Item(name=self.name + "'s corpse.", data_id=self.name + '_corpse',
                          description='A dead ' + self.name + '.', char='%', color=self.color, weight=self.weight)
        elif self.corpse == 'no corpse':  # if no corpse
            return None
        else:  # if corpse entity_id specified
            corpse = dataset.get_entity(self.corpse)
        return corpse


class Seer(Entity):
    """
        Mixin class, adds visibility (FOV & LOS) functionality to Entity.
    """

    def __init__(self, sight_radius):
        self.sight_radius = sight_radius  # sight radius in tiles
        self.fov_set = set()  # field of view - set of (x, y) points

    def compute_fov(self):
        """ Method that calculates FOV """
        if self.fov_set:  # clear FOV
            self.fov_set.clear()
        else:
            self.fov_set = set()
        fov.fieldOfView(self.position[0], self.position[1], self.location.width, self.location.height,
                        self.sight_radius, self.fov_visit_cell, self.location.cell_blocks_sight)
        if isinstance(self, Player):
            for point in self.fov_set:
                if self.location.is_in_boundaries(point[0], point[1]):
                    self.location.cells[point[0]][point[1]].explored = True
                    # update visited cells map (for displaying grey out of vision explored tiles)
                    self.location.out_of_sight_map[(point[0], point[1])] =\
                        self.location.cells[point[0]][point[1]].get_cell_graphics()

    def fov_visit_cell(self, x, y):
        """ Method for FOV "visit" - adds visible cell coords to FOV set """
        self.fov_set.add((x, y))

    def is_in_fov(self, x, y):
        """ Method that determines is a cell in Seer's FOV """
        return (x, y) in self.fov_set


class Actor(Entity):
    """
        Mixin class, adds acting functionality to the Entity.
        Time-system related stuff.
    """

    def __init__(self, speed, state='ready', ai=None):
        self.base_speed = speed  # overall speed factor of actions
        self.state = state  # actor state - ready, acting or withdrawal (for now)
        self.not_moved = 0  # number of turns that Entity not moved
        self.actions = []  # list of actions
        self.ai = ai  # ai component

    @property
    def speed(self):
        """ Actor speed getter (with all effects applied) """
        haste = self.get_effect('HASTE')
        if haste == 0:  # if no haste effect
            haste = 100  # set haste coefficient to 1
        slow = self.get_effect('SLOWED')
        if slow == 0:  # if no slow effect
            slow = 100  # set slow coefficient to 1
        return int(self.base_speed * (haste / 100) * (slow / 100))

    def move(self, dx, dy):
        """ Movement method, checks if it is allowed to move. For player, monster movement. """
        # checks if entity is positioned in location
        if self.position:
            new_x = self.position[0] + dx
            new_y = self.position[1] + dy
            # check if new position is in the location boundaries
            if self.location.is_in_boundaries(new_x, new_y):
                # checks if tile allows movement
                if self.location.cells[new_x][new_y].is_movement_allowed():
                    # remove from old cell
                    old_x = self.position[0]  # remember old position to update path map
                    old_y = self.position[1]
                    self.location.cells[self.position[0]][self.position[1]].entities.remove(self)
                    self.location.cells[new_x][new_y].entities.append(self)  # add to new cell
                    self.position = (new_x, new_y)  # update entity position
                    if self.occupies_tile or self.pass_cost != 1:  # if entity blocks or impairs movement
                        self.location.path_map_update(new_x, new_y)  # update path map
                        self.location.path_map_update(old_x, old_y)  # update path map
                    events.Event(self.location, {'type': 'entity_moved', 'entity': self})  # fire an event
                    msg = self.name + 'moved to ' + str(new_x) + ':' + str(new_y)
                    Game.add_message(msg, 'DEBUG', [255, 255, 255])
                    self.not_moved = 0
                    return True
        else:
            raise Exception('Attempted to move entity not positioned in any location. ', self.name)
        return False

    def close(self, door):
        """ Door closing method """
        if door:
            return door.close()
        else:
            raise Exception('Attempted to close non-existing door. ', self.name)

    def open(self, door):
        """ Door opening method """
        if door:
            return door.open()
        else:
            raise Exception('Attempted to open non-existing door. ', self.name)

    def perform(self, action_function, *args, **kwargs):
        """ Method for voluntarily performing an action in a location (maybe in future will be actions outside) """
        if self.location:
            if self.state == 'ready':
                # register action and add it on actor's action list
                self.actions.append(
                    self.location.action_mgr.register_action(self.speed, action_function, *args, **kwargs))
                self.state = 'performing'
                return True
            return False
        else:
            raise Exception('Attempted to perform action with entity not positioned in any location. ', self.name)


class Abilities(Entity):
    """
        Mixin class, adds Abilities to Entity.
    """

    def __init__(self):
        self.abilities = []  # abilities list

    def add_ability(self, ability):
        """ Ability adding method """
        ability.set_owner(self)  # set owner of ability
        self.abilities.append(ability)  # add it to list

    def abilities_set_owner(self, owner):
        """ Set owner of all abilities - used in Item equip/take """
        for ability in self.abilities:
            ability.set_owner(owner)

    def abilities_reobserve(self):
        """ A method that reobserves abilities """
        for abil in self.abilities:
            abil.reobserve()


class Inventory(Entity):
    """
        Mixin class, adds inventory to Entity.
    """

    def __init__(self):
        self.inventory = []  # a list of Item objects

    @property
    def inv_weight(self):
        """ Property that returns total weight of items in inventory """
        w = 0
        for item in self.inventory:
            w += item.weight
        return w

    def add_item(self, item):
        """ Item adding method """
        if isinstance(item, str):  # if item ID instead of item
            if self.location:
                item = self.location.reg_entity(item)
            else:
                item = dataset.get_entity(item)
        if isinstance(item, ItemCharges):  # if item is stackable
            if 'stackable' in item.categories:
                if isinstance(self, Equipment):  # first try add to equipment
                    for i in self.equipment.values():
                        if i:
                            if i.name == item.name:  # add a charge number to existing stack
                                i.charges += item.charges
                                if item.position:  # if it's placed somewhere in location
                                    item.location.cells[item.position[0]][item.position[1]].entities.remove(item)
                                    item.position = None
                                return
                for i in self.inventory:
                    if i.name == item.name:  # add a charge number to existing stack
                        i.charges += item.charges
                        if item.position:  # if it's placed somewhere in location
                            item.location.cells[item.position[0]][item.position[1]].entities.remove(item)
                            item.position = None
                        return
        self.inventory.append(item)  # add item to inventory
        item.owner = self  # set item's owner
        item.abilities_set_owner(self)  # if it has abilities - set their owner
        if item.position:  # if it's placed somewhere in location
            item.location.cells[item.position[0]][item.position[1]].entities.remove(item)
            item.position = None

    def drop_item(self, item):
        """ Item dropping method (in a location) """
        if isinstance(self, Player):
            msg = 'You drop ' + str(item) + ' on the ground.'
            Game.add_message(msg, 'PLAYER', [255, 255, 255])
        item.owner = None
        item.abilities_set_owner(item)  # if it has abilities - set their owner
        self.location.place_entity(item, self.position[0], self.position[1])  # place it on the map
        self.inventory.remove(item)

    def discard_item(self, item):
        """ Method that removes item from inventory, without placing it anywhere """
        if item in self.inventory:
            item.owner = None
            item.abilities_set_owner(item)  # if it has abilities - set their owner to item
            self.inventory.remove(item)

    def use_item(self, item, target=None):
        """ Item use on self or target method """
        item.use(user=self, target=target)

    def throw(self, item, target, power):
        """ Method that throws the Item """
        if isinstance(item, ItemCharges) and 'stackable' in item.categories:
            if item.charges > 0:
                orig_item = item
                item = copy.copy(item)  # create a copy of item with quantity 1
                item.charges = 1
                orig_item.decrease()
        else:
            if isinstance(self, Equipment):
                self.unequip_item(item)  # unequip if equipped
            self.discard_item(item)  # discard item from inventory
        if 'thrown_speed' in item.properties:  # get weapon shot speed, if no - use default 5
            thrown_speed = item.properties['thrown_speed']
        else:
            thrown_speed = 5  # 5 - default thrown speed
        # TODO: may need further refactoring - entity reobserves 2 times
        throw = UnguidedThrown(thrower=self, thrown=item, power=power, speed=thrown_speed, target=target)
        self.location.reg_entity(throw)  # register throw entity to location
        throw.launch(self.position[0], self.position[1])  # launch thrown from thrower position


class Equipment(Entity):
    """
        Mixin class for character equipment.
    """

    def __init__(self, layout='humanoid'):
        self.equipment = {}  # equipment dict
        if not isinstance(self, Inventory):  # check if entity has no inventory
            raise Exception('An Entity with Equipment mixin must have also Inventory one.')
        if layout == 'humanoid':  # standard equipment layout for humanoids
            self.equipment = dict.fromkeys(['RIGHT_HAND', 'LEFT_HAND', 'RIGHT_RING', 'LEFT_RING', 'ARMS', 'SHOULDERS',
                                            'BODY', 'HEAD', 'FACE', 'LEFT_EAR', 'RIGHT_EAR', 'NECK', 'WAIST', 'LEGS',
                                            'FEET'])

    @property
    def eq_weight(self):
        """ Property that returns total weight of equipped items """
        w = 0
        for item in self.equipment.values():
            if item:
                w += item.weight
        return w

    def equip_item(self, item, slot):
        """ Method for equipping items """
        if self.equipment[slot]:
            self.add_item(self.equipment[slot])  # add old item to inventory
        if item in self.inventory:  # if item is in inventory - remove it
            self.discard_item(item)
        item.owner = self  # set item owner
        item.abilities_set_owner(self)  # if it has abilities - set their owner
        self.equipment[slot] = item  # fill equipment slot with item

    def unequip_item(self, item):
        """ Method for unequipping items """
        if item in self.equipment.values():
            self.add_item(item)  # add item to inventory
            for sl, it in self.equipment.items():  # remove item from all slots occupied
                if it == item:
                    self.equipment[sl] = None

    def drop_equipped_item(self, item):
        """ Method for dropping equipped items """
        if item in self.equipment.values():
            self.location.place_entity(item, self.position[0], self.position[1])  # place item at location
            for sl, it in self.equipment.items():  # remove item from all slots occupied
                if it == item:
                    self.equipment[sl] = None
            item.owner = None
            item.abilities_set_owner(None)  # if it has abilities - set their owner


class AI(events.Observer):
    """ Base class that represents monster AI """

    def __init__(self, state, owner=None):
        self.state = state  # state of AI, i.e. 'sleeping', 'wandering', 'chasing'
        self.owner = owner  # owner Entity of ai object.
        self.reobserve()

    def reobserve(self):
        """ Method that registers AI to observe events """
        events.Observer.__init__(self)  # register self as observer
        if self.owner:
            if self.owner.location:
                self.observe(self.owner.location, self.on_event_location)
        #else:
        #    raise Exception('Attempted to reobserve AI of Entity without a location')

    def act(self):
        """ Abstract method of AI class that is called when AI should decide what to do """
        raise NotImplementedError

    def on_event_location(self, data):
        """ Abstract method of location event handler """
        raise NotImplementedError


class SimpleMeleeChaserAI(AI):
    """ A simple melee chaser monster AI """

    def __init__(self, state='idle'):
        AI.__init__(self, state)
        self.seen = False  # if player has been seen - set to true. For chasing
        self.seen_x = -1
        self.seen_y = -1

    def on_event_location(self, data):
        """ Method handling location-related events """
        if data['type'] == 'entity_moved':
            if isinstance(data['entity'], Player):  # if player moved - remember its position
                pl_x = data['entity'].position[0]
                pl_y = data['entity'].position[1]
                if hypot(pl_x - self.owner.position[0], pl_y - self.owner.position[1]) <= self.owner.sight_radius:
                    self.state = 'alert'  # if player new position is within sight radius - switch to 'alert' state

    def act(self):
        """ Method called when monster is ready to act """
        moved = False  # flag if Actor moves this turn - for A* pathfinding optimisation
        if self.state == 'alert':
            x = self.owner.position[0]
            y = self.owner.position[1]
            for point in self.owner.fov_set:  # check for player in FOV
                player = self.owner.location.cells[point[0]][point[1]].is_there_a(Player)
                if player:  # if there is one
                    self.seen = True
                    self.seen_x = player.position[0]  # update last seen position of player
                    self.seen_y = player.position[1]
                    # if in melee range - attack
                    if hypot(point[0] - self.owner.position[0], point[1] - self.owner.position[1]) <= 1.42:
                        self.owner.perform(actions.act_attack_melee_basic, self.owner, player)
                        break  # action is performed - stop iterating through FOV
                    else:  # if not - obtain path
                        path = pathfinding.get_path(self.owner.location, x, y, point[0], point[1])  # using pathfinding
                        if len(path) > 0:  # if there are path
                            step_cell = path[0]  # move closer
                            self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
                            moved = True
                            break  # action is performed - stop iterating through FOV
            if self.seen and self.owner.state == 'ready':  # check if still ready to act, and player was seen
                if not ((x == self.seen_x) and (y == self.seen_y)):  # if not in last player seen position
                    path = pathfinding.get_path(self.owner.location, x, y, self.seen_x, self.seen_y)  # get a path there
                    if len(path) > 0:  # if there are path
                        step_cell = path[0]  # move closer to last known player position
                        self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
                        moved = True
                    else:  # if no path for 3 turns - go idle
                        if self.owner.not_moved > 3:
                            self.seen = False
                            self.seen_x = -1
                            self.seen_y = -1
                            self.state = 'idle'
                else:  # if in last seen player position, and no player in FOV - stop searching, go idle
                    self.seen = False
                    self.seen_x = -1
                    self.seen_y = -1
                    self.state = 'idle'
        if self.owner.state == 'ready':  # if no action is performed - wait
            self.owner.perform(actions.act_wait, self.owner, self.owner.speed)
        if not moved:
            self.owner.not_moved += 1


class AbilityUserAI(AI):
    """ A simple AI for monster, that uses abilities """

    def __init__(self, state='idle', behavior='melee', properties=None):
        AI.__init__(self, state)
        self.behavior = behavior  # overall monster behavior
        self.properties = properties  # properties of selected behavior (i.e. preferred range for ranged)
        self.seen = False  # if player has been seen - set to true. For chasing
        self.seen_x = -1
        self.seen_y = -1

    def on_event_location(self, data):
        """ Method handling location-related events """
        if data['type'] == 'entity_moved':
            if isinstance(data['entity'], Player):
                pl_x = data['entity'].position[0]
                pl_y = data['entity'].position[1]
                if hypot(pl_x - self.owner.position[0], pl_y - self.owner.position[1]) <= self.owner.sight_radius:
                    self.state = 'alert'

    def act(self):
        """ Method called when monster is ready to act """
        if self.state == 'alert':
            if self.behavior == 'melee':
                self.melee()
            elif self.behavior == 'ranged':
                self.ranged()
        if self.owner.state == 'ready':  # if no action is performed - wait
            self.owner.perform(actions.act_wait, self.owner, self.owner.speed)

    def melee(self):
        """ Method what to do in alert state if melee behavior """
        x = self.owner.position[0]
        y = self.owner.position[1]
        acted = False  # acted flag
        moved = False  # flag if Actor moves this turn - for A* pathfinding optimisation
        for point in self.owner.fov_set:  # check for player in FOV
            player = self.owner.location.cells[point[0]][point[1]].is_there_a(Player)
            if player:  # if there is one
                self.seen = True
                self.seen_x = player.position[0]  # update last seen position of player
                self.seen_y = player.position[1]
                if len(self.owner.abilities) > 0:  # if there are abilities - try to use them
                    # get a list of ai-usable abilities
                    ai_abilities = [a for a in self.owner.abilities if a.ai_info and a.ability_on_cd is False]
                    ai_abilities.sort(key=lambda abil: abil.ai_info['priority'])  # sort list by ability priority
                    for ability in ai_abilities:  # list of abilities with ai_info
                        data = {}  # gather data, needed to determine if ability can be used now
                        if ability.ai_info['type'] == 'ranged_attack':  # if ranged attack - add range info
                            data['range'] = ability.ai_info['range']
                        # determine target of ability
                        if ability.ai_info['target'] == 'player':
                            target = player
                        elif ability.ai_info['target'] == 'self':
                            target = self.owner
                        else:
                            raise Exception('Need to specify target of ability!')
                        data['target'] = target  # add target info to data
                        data['type'] = ability.trigger  # set event type to ability trigger
                        if ability.conditions_met(data):
                            # use ability action
                            self.owner.perform(actions.act_use_ability, self.owner, target, ability,
                                               ability.ai_info['whole_time'], ability.ai_info['use_offset'])
                            acted = True
                            break  # one action at a time
                if not acted and hypot(point[0] - self.owner.position[0], point[1] - self.owner.position[1]) <= 1.42:
                    # if in melee range - attack
                    self.owner.perform(actions.act_attack_melee_basic, self.owner, player)
                    acted = True
                    break  # action is performed - stop iterating through FOV
                else:  # if not - obtain path
                    path = pathfinding.get_path(self.owner.location, x, y, point[0], point[1])  # using pathfinding
                    if len(path) > 0:  # if there are path
                        step_cell = path[0]  # move closer
                        acted = True
                        self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
                        moved = True
                        break  # action is performed - stop iterating through FOV
        if self.seen and not acted:  # check if still ready to act, and player was seen
            if not ((x == self.seen_x) and (y == self.seen_y)):  # if not in last player seen position
                path = pathfinding.get_path(self.owner.location, x, y, self.seen_x, self.seen_y)  # get a path there
                if len(path) > 0:  # if there are path
                    step_cell = path[0]  # move closer to last known player position
                    acted = True
                    self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
                    moved = True
                else:  # if no path for 3 turns - go idle
                    if self.owner.not_moved > 3:
                        self.seen = False
                        self.seen_x = -1
                        self.seen_y = -1
                        self.state = 'idle'
            else:  # if in last seen player position, and no player in FOV - stop searching, go idle
                self.seen = False
                self.seen_x = -1
                self.seen_y = -1
                self.state = 'idle'
        if not moved:
            self.owner.not_moved += 1

    def ranged(self):
        """ Method what to do in alert state if ranged behavior """
        x = self.owner.position[0]
        y = self.owner.position[1]
        pref_range = self.properties['preferred_range']
        acted = False  # acted flag
        moved = False  # flag if Actor moves this turn - for A* pathfinding optimisation
        for point in self.owner.fov_set:  # check for player in FOV
            player = self.owner.location.cells[point[0]][point[1]].is_there_a(Player)
            if player:  # if there is one
                self.seen = True
                self.seen_x = player.position[0]  # update last seen position of player
                self.seen_y = player.position[1]
                range_to_player = hypot(point[0] - self.owner.position[0], point[1] - self.owner.position[1])
                # TODO: move abilities usage to separate method
                if len(self.owner.abilities) > 0:  # if there are abilities - try to use them
                    # get a list of ai-usable abilities
                    ai_abilities = [a for a in self.owner.abilities if a.ai_info and a.ability_on_cd is False]
                    ai_abilities.sort(key=lambda abil: abil.ai_info['priority'])  # sort list by ability priority
                    for ability in ai_abilities:  # list of abilities with ai_info
                        data = {}  # gather data, needed to determine if ability can be used now
                        if ability.ai_info['type'] == 'ranged_attack':  # if ranged attack - add range info
                            data['range'] = ability.ai_info['range']
                        # determine target of ability
                        if ability.ai_info['target'] == 'player':
                            target = player
                        elif ability.ai_info['target'] == 'self':
                            target = self.owner
                        else:
                            raise Exception('Need to specify target of ability!')
                        data['target'] = target  # add target info to data
                        data['type'] = ability.trigger  # set event type to ability trigger
                        if ability.conditions_met(data):
                            # use ability action
                            self.owner.perform(actions.act_use_ability, self.owner, target, ability,
                                               ability.ai_info['whole_time'], ability.ai_info['use_offset'])
                            acted = True
                            break  # one action at a time
                if not acted and range_to_player > pref_range:  # if farther than in preferred range - move closer
                    path = pathfinding.get_path(self.owner.location, x, y, point[0], point[1])  # using pathfinding
                    if len(path) > 0:  # if there are path
                        step_cell = path[0]  # move closer
                        acted = True
                        self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
                        moved = True
                        break  # action is performed - stop iterating through FOV
                if not acted and range_to_player <= 1.42:
                    # if in melee range - attack
                    self.owner.perform(actions.act_attack_melee_basic, self.owner, player)
                    acted = True
                    break  # action is performed - stop iterating through FOV
                else:  # if within preferred range - stand still
                    # TODO: make ranged mob backpedal if too close
                    acted = True
                    self.owner.perform(actions.act_wait, self.owner, self.owner.speed)
                    break  # action is performed - stop iterating through FOV
        if self.seen and not acted:  # check if still ready to act, and player was seen
            if not ((x == self.seen_x) and (y == self.seen_y)):  # if not in last player seen position
                path = pathfinding.get_path(self.owner.location, x, y, self.seen_x, self.seen_y)  # get a path there
                if len(path) > 0:  # if there are path
                    step_cell = path[0]  # move closer to last known player position
                    acted = True
                    self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
                    moved = True
                else:  # if no path for 3 turns - go idle
                    if self.owner.not_moved > 3:
                        self.seen = False
                        self.seen_x = -1
                        self.seen_y = -1
                        self.state = 'idle'
            else:  # if in last seen player position, and no player in FOV - stop searching, go idle
                self.seen = False
                self.seen_x = -1
                self.seen_y = -1
                self.state = 'idle'
        if not moved:
            self.owner.not_moved += 1


class UnguidedProjectileAI(AI):
    """ An unguided projectile AI """
    def __init__(self, power, target, owner, state='flying'):
        AI.__init__(self, state, owner)
        self.route = None
        self.next = None
        self.power = power
        self.target = target

    def on_event_location(self, data):
        """ Method handling location-related events """
        if data['type'] == 'entity_moved':  # if something moved
            if self.owner.position == data['entity'].position:  # on projectile - check for hit
                self._check_if_hit()

    def enroute(self):
        """ Method to calculate route """
        self.route = raycasting.ray(self.owner.position[0], self.owner.position[1], self.target[0], self.target[1],
                                    self.owner.location.width, self.owner.location.height, self.power)
        self.next = iter(self.route)
        self._fly_next()  # fly to next cell (or stop if out of power or route end)

    def act(self):
        """ Method called when projectile is ready to act """
        if self.state == 'flying':
            if not self._check_if_hit():  # if nothing is hit - fly farther
                self._fly_next()  # fly to next cell (or stop if out of power or route end)

    def _fly_next(self):
        """ Method to attempt fly to next cell in route """
        x, y = self.owner.position
        try:
            next_cell = next(self.next)
        except StopIteration:  # if end of route
            self._hit((x, y))  # hit ending cell
            return
        if self.power <= 0:
            self._hit((x, y))  # hit last cell
            return
        self.owner.perform(actions.act_relocate, self.owner, next_cell[0], next_cell[1])  # if not stopped - fly next
        self.power -= 1

    def _check_if_hit(self):
        """ Method that checks current position for acceptable target to hit """
        x, y = self.owner.position
        enemy = self.owner.location.cells[x][y].get_occupying_entity()
        if enemy:
            # TODO: make projectile property for traveling through some kinds of Entities ( and opposite too)
            if enemy.blocks_shots < 1:  # check if projectile pass through (for windows, grates, etc)
                enemy = weighted_choice([(enemy, enemy.blocks_shots * 100), (None, 100 - enemy.blocks_shots * 100)])
        if enemy:
            if isinstance(enemy, BattleEntity):  # if enemy can be damaged
                # fire an event that triggers ability
                self._hit(enemy)
                return True
        return False

    def _hit(self, something):
        """ Method called when projectile hit something """
        events.Event(self.owner, {'type': 'projectile_hit', 'target': something, 'attacker': self.owner.launcher})
        self.state = 'stopped'
        self.owner.dead = True
        self.owner.location.dead.append(self.owner)  # add to dead list, waiting for removal


class UnguidedShotAI(UnguidedProjectileAI):
    """ An unguided shot AI (based on projectile ai)
    Differences from base projectile: has some damage (weapon + ammo), contains ammo dropped if not broken
    """

    def __init__(self, power, target, owner, state='flying'):
        super(UnguidedShotAI, self).__init__(power=power, target=target, owner=owner, state=state)

    def _hit(self, something):
        """ Method called when shot hit something """
        x = self.owner.position[0]
        y = self.owner.position[1]
        if isinstance(something, Entity):  # if entity is hit
            if random.uniform(0, 1) < self.owner.ammo.properties['break_chance']:  # determine if ammo broken
                ammo_broken = True
            else:
                ammo_broken = False
            if not ammo_broken:
                if isinstance(something, Inventory) and 'sticks_to_target' in self.owner.ammo.categories:
                    something.add_item(self.owner.ammo)
                else:
                    self.owner.location.place_entity(self.owner.ammo, x, y)
        else:  # must be a point tuple then
            self.owner.location.place_entity(self.owner.ammo, x, y)
        if isinstance(something, BattleEntity):  # if enemy can be damaged
            dmg = 0
            dmg_type = 'pure'
            # UGLY as hell..
            ammo = self.owner.ammo
            if 'bashing' in ammo.properties.keys():
                dmg = ammo.properties['bashing']
                dmg_type = 'bashing'
            elif 'slashing' in ammo.properties.keys():
                dmg = ammo.properties['slashing']
                dmg_type = 'slashing'
            elif 'piercing' in ammo.properties.keys():
                dmg = ammo.properties['piercing']
                dmg_type = 'piercing'
            elif 'fire' in ammo.properties.keys():
                dmg = ammo.properties['fire']
                dmg_type = 'fire'
            elif 'cold' in ammo.properties.keys():
                dmg = ammo.properties['cold']
                dmg_type = 'cold'
            elif 'lightning' in ammo.properties.keys():
                dmg = ammo.properties['lightning']
                dmg_type = 'lightning'
            elif 'poison' in ammo.properties.keys():
                dmg = ammo.properties['poison']
                dmg_type = 'poison'
            elif 'acid' in ammo.properties.keys():
                dmg = ammo.properties['acid']
                dmg_type = 'acid'
            elif 'mental' in ammo.properties.keys():
                dmg = ammo.properties['mental']
                dmg_type = 'mental'
            elif 'death' in ammo.properties.keys():
                dmg = ammo.properties['death']
                dmg_type = 'death'
            elif 'strange' in ammo.properties.keys():
                dmg = ammo.properties['strange']
                dmg_type = 'strange'
            try:  # if damage is (min, max) tuple
                random.seed()
                min_dmg = dmg[0]
                max_dmg = dmg[1]
                dmg = random.randint(min_dmg, max_dmg)
            except TypeError:
                pass
            for ef in self.owner.weapon.effects:
                if ef.eff == 'INCREASE_RANGED_DAMAGE':
                    dmg += ef.magnitude
            strike = Strike(strike_type='projectile', damage=dmg,
                            dmg_type=dmg_type)
            res_dmg = self.owner.launcher.land_strike(strike=strike, target=something)  # land strike
            events.Event(self.owner, {'type': 'shot_hit', 'target': something, 'strike': strike,
                                      'attacker': self.owner.launcher, 'damage': res_dmg})
            Game.add_message(self.owner.name + ' hits ' + something.name + ' for ' + str(res_dmg) + ' damage!',
                             'PLAYER', [255, 255, 255])
        super(UnguidedShotAI, self)._hit(something)  # call parent _hit function


class UnguidedThrownAI(UnguidedProjectileAI):
    """ An unguided throw AI (based on projectile ai)
    Differences from Shot: flies to a selected cell, instead of trajectory crossing it, has some damage and contains
    Entity.
    """

    def __init__(self, power, target, owner, state='flying'):
        super(UnguidedThrownAI, self).__init__(power=power, target=target, owner=owner, state=state)

    def enroute(self):
        """ Method to calculate route (overridden: line to target instead of trajectory that crosses it) """
        self.route = los.get_line(self.owner.position[0], self.owner.position[1], self.target[0], self.target[1])
        self.route.pop(0)  # pop first item from path, it's thrower position
        self.next = iter(self.route)
        self._fly_next()  # fly to next cell (or stop if out of power or route end)

    def _hit(self, something):
        """ Method called when thrown hit something """
        x = self.owner.position[0]
        y = self.owner.position[1]
        if isinstance(something, Entity):  # if entity is hit
            thrown_broken = False
            if 'break_chance' in self.owner.thrown.properties:  # if thrown item has chance to break
                if random.uniform(0, 1) < self.owner.thrown.properties['break_chance']:  # determine if thrown broken
                    thrown_broken = True
            if not thrown_broken:
                if isinstance(something, Inventory) and 'sticks_to_target' in self.owner.thrown.categories:
                    something.add_item(self.owner.thrown)
                else:
                    self.owner.location.place_entity(self.owner.thrown, x, y)
        else:  # must be a point tuple then
            self.owner.location.place_entity(self.owner.thrown, x, y)
        super(UnguidedThrownAI, self)._hit(something)  # call parent _hit function


class Item(Abilities, Entity):
    """
        Mixed class, simple Item.
    """

    def __init__(self, name, data_id, description, char, color, weight=0, pass_cost=1,
                 equip_slots=None, categories=None, properties=None):
        # calling constructors
        Entity.__init__(self, name=name, data_id=data_id, description=description, weight=weight, pass_cost=pass_cost,
                        char=char, color=color, occupies_tile=False, blocks_shots=0)
        self.owner = None  # owner of item - entity with inventory
        if categories:
            self.categories = categories  # item categories - a potion, a sword, etc
        else:
            self.categories = set()
        if properties:
            self.properties = properties  # item properties - armor values, accuracy for weapons, etc
        else:
            self.properties = {}
        if equip_slots:  # equipment slots, in which item can be placed
            self.equip_slots = equip_slots
        else:  # by default - can be taken to hands
            self.equip_slots = dict.fromkeys(['RIGHT_HAND', 'LEFT_HAND'])
        Abilities.__init__(self)

    def use(self, user, target):
        """ Call this method when item is used - return True if successiful """
        if target == user:  # if no target specified or target is user - use on self
            events.Event(user, {'type': 'used_on_self', 'item': self})  # fire an event
        else:
            events.Event(user, {'type': 'used_on_target', 'item': self, 'target': target})  # fire an event
        return True


class ItemCharges(Item):
    """
        Child class of item that has charges
    """

    def __init__(self, name, data_id, description, char, color, charges, weight=0, pass_cost=1,
                 categories=None, properties=None, destroyed_after_use=True, equip_slots=None):
        super(ItemCharges, self).__init__(name=name, data_id=data_id, description=description, categories=categories,
                                          properties=properties, weight=weight, pass_cost=pass_cost,
                                          char=char, color=color, equip_slots=equip_slots)
        self.destroyed_after_use = destroyed_after_use  # if True, item is destroyed when charges are depleted
        self.charges = charges  # number of uses

    @property
    def weight(self):
        """ Overridden method that returns weight according to charges number """
        if 'weight_per_charge' in self.categories:
            return self._weight * self.charges
        else:
            return self._weight

    def __str__(self):
        """ Method returns string representation of ItemCharges - it's name with charges """
        return self.name + '[[' + str(self.charges) + ']]'

    def use(self, user, target):
        """ Overrides the use() method, to manage charges and item destruction """
        if self.charges > 0:
            result = super(ItemCharges, self).use(user=user, target=target)
            if result:
                self.decrease()
            return result
        else:
            msg = self.name + ' is depleted!'
            Game.add_message(msg, 'PLAYER', [255, 255, 255])
            return False

    def decrease(self):
        """ Decrease charges by 1 """
        if self.charges > 0:  # if there are remaining charges
            self.charges -= 1  # use 1 charge
        if self.destroyed_after_use and self.charges == 0:
            if isinstance(self.owner, Equipment):
                self.owner.unequip_item(self)  # unequip if equipped
            if isinstance(self.owner, Inventory):
                self.owner.discard_item(self)  # if item is depleted and destroys when empty - remove it from inventory


class ItemShield(Item):
    """
        Child class of shield item. Has durability and armor
    """

    def __init__(self, name, data_id, description, char, color, weight=0, pass_cost=1, durability=1,
                 categories=None, properties=None, equip_slots=None):
        super(ItemShield, self).__init__(name=name, data_id=data_id, description=description, categories=categories,
                                         properties=properties, weight=weight, pass_cost=pass_cost,
                                         char=char, color=color, equip_slots=equip_slots)
        self.max_durability = durability  # durability of shield, its 'hp'
        self.durability = durability

    def __str__(self):
        """ Method returns string representation of ItemShield - it's name with durability """
        return self.name + '(' + str(self.durability) + ')'

    def block(self, damage, dmg_type):
        """ Method is called when shield blocks damage. Returns damage that passed through shield """
        block = 0  # shield blocking ammount
        self_prot = 0  # shield protection from damage (used to calculate durability damage)
        if 'armor_' + dmg_type in self.properties.keys():
            self_prot += self.properties['armor_' + dmg_type]  # add armor protection
        if 'block_' + dmg_type in self.properties.keys():
            block += self.properties['block_' + dmg_type]  # add armor protection
        if block == 0:  # TODO: PLACEHOLDER - makes shield ignore damage type it can't block. Must have conditions.
            return damage
        # at 100 armor - 50% reduction
        if self_prot == -100:  # to prevent division by zero
            reduce = self_prot
        else:
            reduce = self_prot / (100 + self_prot)
        shield_damage = ceil(damage * (1 - reduce))  # calculate durability damage
        if shield_damage < 0:  # if shield damage negative - do not heal shield ;)
            shield_damage = 0
        if shield_damage <= self.durability:  # if shield still holds - absorb full block
            blocked = block
            self.durability -= shield_damage
        else:  # if shield is destroyed by attack - absorb only part of damage
            blocked = shield_damage - self.durability
            if blocked > block:
                blocked = block
            self.durability = 0
        passed = damage - blocked
        if passed > damage:
            passed = damage
        elif passed < 0:
            passed = 0
        return passed  # return damage, passed through shield


class ItemRangedWeapon(Item):
    """
        Child class for a ranged weapon.
    """

    def __init__(self, name, data_id, description, char, color, range, weight=0, pass_cost=1, ammo_max=1,
                 ammo_type=None, ammo=None, categories=None, properties=None, equip_slots=None):
        super(ItemRangedWeapon, self).__init__(name=name, data_id=data_id,
                                               description=description, categories=categories, weight=weight,
                                               pass_cost=pass_cost, properties=properties, char=char, color=color,
                                               equip_slots=equip_slots)
        self.range = range  # max range for ranged weapon
        self.ammo_type = ammo_type  # acceptable type of ammo ( Item.category)
        if ammo:
            self.ammo = ammo  # currently loaded ammo
        else:
            self.ammo = []
        self.ammo_max = ammo_max  # maximum ammo ammount

    @property
    def weight(self):
        """ Overridden method that returns weight according to ammo loaded """
        ammo_weight = 0
        for ammo in self.ammo:
            ammo_weight += ammo.weight
        return self._weight + ammo_weight

    def __str__(self):
        """ Method returns string representation of ItemRangedWeapon - it's name with number of ammo loaded """
        return self.name + '[[' + str(len(self.ammo)) + ']]'

    def shoot(self, target):
        """ Method that shoots the weapon """
        if self.owner:  # if someone holds a weapon - set him as shooter
            shooter = self.owner
        else:
            shooter = self
        if 'shot_speed' in self.properties:  # get weapon shot speed, if no - use default 1
            shot_speed = self.properties['shot_speed']
        else:
            shot_speed = 1
        ammo = self.ammo[0]
        self.ammo.remove(ammo)  # remove ammo item from weapon
        # TODO: may need further refactoring - entity reobserves 2 times
        shot = UnguidedShot(shooter=shooter, weapon=self, ammo=ammo, speed=shot_speed, target=target)
        shooter.location.reg_entity(shot)  # register shot entity to location
        shot.launch(shooter.position[0], shooter.position[1])


class Fighter(BattleEntity, Equipment, Inventory, Abilities, Actor, Seer, Entity):
    """
        Mixed class, basic monster, that can participate in combat and perform actions.
    """

    def __init__(self, name, data_id, description, char, color, hp, speed, sight_radius,
                 damage, weight=0, dmg_type='bashing', categories=None, properties=None,
                 armor=None, resist=None, corpse='', equip_layout='humanoid', ai=None):
        # calling constructors of mixins
        Entity.__init__(self, name=name, data_id=data_id, description=description, char=char, color=color,
                        weight=weight, pass_cost=1, occupies_tile=True, blocks_shots=1)
        BattleEntity.__init__(self, hp=hp, armor=armor, resist=resist, corpse=corpse)
        if ai:  # set AI owner
            ai.owner = self
        Actor.__init__(self, speed=speed, ai=ai)
        Seer.__init__(self, sight_radius=sight_radius)
        Inventory.__init__(self)
        Equipment.__init__(self, layout=equip_layout)
        Abilities.__init__(self)
        self.damage = damage  # damage from basic melee 'punch in da face' attack
        self.dmg_type = dmg_type  # damage type of basic attack
        if categories:
            self.categories = categories  # monster categories - living, undead, magical etc
        else:
            self.categories = set()
        if properties:
            self.properties = properties  # monster properties - stats, etc
        else:
            self.properties = {}

    @property
    def weight(self):
        """ Property that returns total weight of Fighter - with inventory and equipment """
        return self._weight + self.eq_weight + self.inv_weight

    @property
    def carried_weight(self):
        """ Property that returns total carried weight - equipment + inventory """
        return self.eq_weight + self.inv_weight

    @property
    def speed(self):
        """ Fighter speed (with burden applied) """
        sp = super(Fighter, self).speed
        burden_mod = 1
        if 'max_carry_weight' in self.properties:
            if self.carried_weight > self.properties['max_carry_weight']:
                burden_mod = self.carried_weight / self.properties['max_carry_weight']
                if burden_mod > 3:  # not too high, 3 times longer actions is enough
                    burden_mod = 3
        return int(sp * burden_mod)

    def attack_melee_basic(self, target):
        """ Attack in melee with basic attack method (mostly for monsters)"""
        # check if target is in melee range
        if target:  # check if target exists
            dist_to_target = hypot(target.position[0] - self.position[0], target.position[1] - self.position[1])
            if dist_to_target <= 1.42:
                strike = Strike(strike_type='melee', damage=self.damage, dmg_type=self.dmg_type)
                damage_dealt = self.land_strike(strike=strike, target=target)  # land melee strike
                # fire Entity event
                events.Event(self, {'type': 'hit_basic_attack', 'target': target, 'attacker': self,
                                    'damage': damage_dealt, 'dmg_type': self.dmg_type})
                msg = self.name + ' attacks ' + target.name + ' and deals ' + str(damage_dealt) + ' damage!'
                Game.add_message(msg, 'PLAYER', [255, 255, 255])
                msg = self.name + '/' + target.name + 'for' + str(damage_dealt) + 'dmg@' + str(
                    target.position[0]) + ':' + str(target.position[1])
                Game.add_message(msg, 'DEBUG', [255, 255, 255])
            else:
                msg = self.name + 'misses,dist=' + str(dist_to_target)
                Game.add_message(msg, 'DEBUG', [255, 255, 255])

    def attack_melee_weapon(self, weapon, target):
        """ Attack in melee with weapon method """
        if target:  # check if target exists
            dist_to_target = hypot(target.position[0] - self.position[0], target.position[1] - self.position[1])
            if dist_to_target <= 1.42:  # check if target is in melee range
                dmg = 0
                dmg_type = 'pure'
                # TODO: make multiple damage type weapons
                # UGLY as hell..
                if 'bashing' in weapon.properties.keys():
                    dmg = weapon.properties['bashing']
                    dmg_type = 'bashing'
                elif 'slashing' in weapon.properties.keys():
                    dmg = weapon.properties['slashing']
                    dmg_type = 'slashing'
                elif 'piercing' in weapon.properties.keys():
                    dmg = weapon.properties['piercing']
                    dmg_type = 'piercing'
                elif 'fire' in weapon.properties.keys():
                    dmg = weapon.properties['fire']
                    dmg_type = 'fire'
                elif 'cold' in weapon.properties.keys():
                    dmg = weapon.properties['cold']
                    dmg_type = 'cold'
                elif 'lightning' in weapon.properties.keys():
                    dmg = weapon.properties['lightning']
                    dmg_type = 'lightning'
                elif 'poison' in weapon.properties.keys():
                    dmg = weapon.properties['poison']
                    dmg_type = 'poison'
                elif 'acid' in weapon.properties.keys():
                    dmg = weapon.properties['acid']
                    dmg_type = 'acid'
                elif 'mental' in weapon.properties.keys():
                    dmg = weapon.properties['mental']
                    dmg_type = 'mental'
                elif 'death' in weapon.properties.keys():
                    dmg = weapon.properties['death']
                    dmg_type = 'death'
                elif 'strange' in weapon.properties.keys():
                    dmg = weapon.properties['strange']
                    dmg_type = 'strange'
                try:  # if damage is (min, max) tuple
                    random.seed()
                    min_dmg = dmg[0]
                    max_dmg = dmg[1]
                    dmg = random.randint(min_dmg, max_dmg)
                except TypeError:
                    pass
                strike = Strike(strike_type='melee', damage=dmg, dmg_type=dmg_type)
                damage_dealt = self.land_strike(strike=strike, target=target)  # land melee strike
                # fire Entity event
                events.Event(self, {'type': 'hit_weapon_attack', 'target': target,
                                    'damage': damage_dealt, 'dmg_type': dmg_type, 'weapon': weapon})
                msg = self.name + ' attacks ' + target.name + ' with ' \
                      + weapon.name + ' and deals ' + str(damage_dealt) + ' damage!'
                Game.add_message(msg, 'PLAYER', [255, 255, 255])
                msg = self.name + '/' + target.name + 'for' + str(damage_dealt) + 'dmg@' + str(
                    target.position[0]) + ':' + str(target.position[1])
                Game.add_message(msg, 'DEBUG', [255, 255, 255])
            else:
                msg = self.name + 'misses,dist=' + str(dist_to_target)
                Game.add_message(msg, 'DEBUG', [255, 255, 255])

    def attack_ranged_weapon(self, weapon, target):
        """ Attack with ranged weapon method """
        # check if target is a cell or a monster
        if isinstance(target, BattleEntity):
            if target.position:
                tx = target.position[0]  # set projectile target to target current position
                ty = target.position[1]
            else:
                return  # if target has no position - stop shooting, it might be dead
        else:  # if a cell - set tx:ty as target cell
            tx = target[0]
            ty = target[1]
        if 'accuracy_ranged' in weapon.properties:  # get weapon accuracy, if no - use default 1
            acc_weapon = weapon.properties['accuracy_ranged']
        else:
            acc_weapon = 1
        range_to_target = hypot(tx - self.position[0], ty - self.position[1])
        hit = ranged_hit_probability(acc_weapon, weapon.range, range_to_target)
        if not hit:  # if not hit - determine where to miss
            if range_to_target > 3:  # if range too small - make miss circle 3 cell wide
                radius = range_to_target / 2
            else:  # if missed
                radius = 1.5
            miss_circle = circle_points(radius, False)  # get points around target location
            cell = random.sample(miss_circle, 1)[0]  # select random point
            tx += cell[0]
            ty += cell[1]
            msg = self.name + 'ranged_miss,hit_cell=' + str((tx, ty))
            Game.add_message(msg, 'DEBUG', [255, 255, 255])
        weapon.shoot((tx, ty))

    def attack_throw(self, thrown, target):
        """ Throw item method """
        # check if target is a cell or a monster
        if isinstance(target, BattleEntity):
            if target.position:
                tx = target.position[0]  # set projectile target to target current position
                ty = target.position[1]
            else:
                return  # if target has no position - stop shooting, it might be dead
        else:  # if a cell - set tx:ty as target cell
            tx = target[0]
            ty = target[1]
        if 'accuracy_thrown' in thrown.properties:  # get thrown accuracy, if no - use default 0.5
            acc = thrown.properties['accuracy_thrown']
        else:
            acc = 0.5
        range_to_target = hypot(tx - self.position[0], ty - self.position[1])
        hit = ranged_hit_probability(acc, self.get_throw_range(thrown), range_to_target)
        if not hit:  # if not hit - determine where to miss
            if range_to_target > 3:  # if range too small - make miss circle 3 cell wide
                radius = range_to_target / 2
            else:  # if missed
                radius = 1.5
            miss_circle = circle_points(radius, False)  # get points around target location
            cell = random.sample(miss_circle, 1)[0]  # select random point
            tx += cell[0]
            ty += cell[1]
            msg = self.name + 'throw_miss,hit_cell=' + str((tx, ty))
            Game.add_message(msg, 'DEBUG', [255, 255, 255])
        self.throw(thrown, (tx, ty), self.get_throw_range(thrown))

    def get_throw_range(self, item):
        """ PLACEHOLDER method, until some role system will be implemented (must be based on strength) """
        if isinstance(item, ItemCharges):  # throwing one item from a stack (for now)
            w = item._weight  # so obtain single item weight
        else:
            w = item.weight
        return round(12 - w * 2)  # some MAGIC number

    def reload(self, weapon, ammo):
        """ Reload a ranged weapon """
        if weapon.ammo_type in ammo.categories:
            if len(weapon.ammo) < weapon.ammo_max:
                # ammo_copy = pickle.loads(pickle.dumps(ammo, -1))
                ammo_copy = copy.copy(ammo)  # make a copy of ammo object
                ammo_copy.charges = 1  # with one charge
                ammo.decrease()  # decrease ammount of ammo left
                weapon.ammo.append(ammo_copy)  # add copy to weapon.ammo

    def unload(self, weapon):
        """ Unload a ranged weapon """
        if weapon.ammo:  # if there are ammo
            for am in weapon.ammo[:]:  # add ammo to inventory
                self.add_item(am)
                weapon.ammo.remove(am)

    def death(self):
        """ Death method """
        Game.add_message(self.name + ' dies!', 'PLAYER', [255, 255, 255])
        Game.add_message(self.name + 'die', 'DEBUG', [255, 255, 255])
        events.Event(self.location, {'type': 'entity_died', 'entity': self})  # fire an event
        corpse = self.get_corpse()  # get corpse entity
        if corpse:
            self.location.place_entity(corpse, self.position[0], self.position[1])
        for item in self.equipment.values():  # drop all equipped items
            if item:
                self.drop_equipped_item(item)
        for item in self.inventory:  # drop all inventory items
            self.drop_item(item)
        self.location.remove_entity(self)
        self.ai.close()  # unregister Observer


class UnguidedProjectile(Actor, Abilities, Entity):
    """ Mixed base class for unguided projectile (thrown, magic, etc) """

    def __init__(self, launcher, speed, power, target, name='', description='', char=' ', color=None):
        self.launcher = launcher  # Entity, that launched projectile
        self.target = target  # target (x, y) tuple
        Entity.__init__(self, name=name, description=description, char=char, color=color)
        Abilities.__init__(self)
        Actor.__init__(self, speed=speed, ai=UnguidedProjectileAI(power=power, target=target, owner=self))

    def launch(self, origin_x, origin_y):
        """ Method that launches a projectile from (origin_x, origin_y) to target """
        self.location.place_entity(self, origin_x, origin_y)
        self.ai.reobserve()
        self.abilities_set_owner(self)  # refresh abilities owner at launch (in case if projectile was loaded or copied)
        self.abilities_reobserve()  # refresh abilities as observer at launch
        self.ai.enroute()

    def death(self):
        """ Death function """
        self.location.remove_entity(self)
        self.ai.close()  # unregister Observer


class UnguidedShot(UnguidedProjectile):
    """ Child class for unguided shot (from a weapon) """

    def __init__(self, shooter, weapon, ammo, speed, target):
        super(UnguidedShot, self).__init__(launcher=shooter, speed=speed, power=weapon.range, target=target,
                                           name=ammo.name, description=ammo.description, char=ammo.char,
                                           color=ammo.color)
        self.ai.close()  # replace AI with Shot AI
        self.ai = UnguidedShotAI(power=weapon.range, target=target, owner=self)
        self.weapon = weapon  # weapon that fired projectile
        self.ammo = ammo  # ammo piece

    def launch(self, origin_x, origin_y):
        """ Method that launches a projectile from (origin_x, origin_y) to target """
        self.abilities = pickle.loads(pickle.dumps(self.ammo.abilities))  # copy abilities from ammo to projectile
        super(UnguidedShot, self).launch(origin_x=origin_x, origin_y=origin_y)  # call parent class method


class UnguidedThrown(UnguidedProjectile):
    """ Child class for unguided thrown (weapon or entity) """

    def __init__(self, thrower, thrown, power, speed, target):
        super(UnguidedThrown, self).__init__(launcher=thrower, speed=speed, power=power, target=target,
                                             name=thrown.name, description=thrown.description, char=thrown.char,
                                             color=thrown.color)
        self.ai.close()  # replace AI with Shot AI
        self.ai = UnguidedThrownAI(power=power, target=target, owner=self)
        self.thrown = thrown  # ammo piece

    def launch(self, origin_x, origin_y):
        """ Method that launches a projectile from (origin_x, origin_y) to target """
        self.abilities = pickle.loads(pickle.dumps(self.thrown.abilities))  # copy abilities from thrown to projectile
        super(UnguidedThrown, self).launch(origin_x=origin_x, origin_y=origin_y)  # call parent class method


class Player(Fighter):
    """
        Child class, adds player-specific functionality to Fighter.
    """

    def __init__(self, name, data_id, description, char, color, hp, speed, sight_radius, damage, categories,
                 properties, weight):
        # calling constructor of parent class
        Fighter.__init__(self, name=name, data_id=data_id, description=description, char=char, color=color, hp=hp,
                         speed=speed, sight_radius=sight_radius, damage=damage, categories=categories,
                         properties=properties, ai=None, weight=weight)
        # hit zones with percent to hit (monsters doesn't have them)
        self.hit_zones = [('HEAD', 10), ('BODY', 40), ('ARMS', 15), ('SHOULDERS', 15), ('LEGS', 15), ('FEET', 5)]

    def get_protection(self, dmg_type):
        """ Overrides get_protection() of BattleEntity to add protection from equipment """
        basic_prot = BattleEntity.get_protection(self, dmg_type)  # obtain protection as every BE, if any
        prot = basic_prot[0]
        block = basic_prot[1]
        hit_zone = weighted_choice(self.hit_zones)
        armor = self.equipment[hit_zone]
        if armor:  # if there are armor on hit zone - add protection
            if 'armor_' + dmg_type in armor.properties.keys():
                prot += armor.properties['armor_' + dmg_type]  # add armor protection
        block += self.get_effect('BLOCK_' + dmg_type.upper())  # add damage block ammount
        return prot, block, hit_zone

    def death(self):
        """ Death method """
        Game.add_message('You died!', 'PLAYER', [255, 0, 0])
        Game.add_message(self.name + 'player died', 'DEBUG', [255, 255, 255])
        self.char = '%'
        self.color = [255, 0, 0]
        self.state = 'dead'


class Prop(BattleEntity, Abilities, Entity):
    """
        Mixed class of a prop (wall, window, pillar, etc), that has HP and can be destroyed, but lacks acting ability.
    """

    def __init__(self, name, data_id, char, hp, description='', color=None, blocks_los=True, weight=0, blocks_shots=1,
                 occupies_tile=True, pass_cost=1, armor=None, corpse='no corpse'):
        Entity.__init__(self, name=name, data_id=data_id, description=description, char=char, color=color,
                        occupies_tile=occupies_tile, blocks_los=blocks_los, blocks_shots=blocks_shots,
                        weight=weight, pass_cost=pass_cost)
        BattleEntity.__init__(self, hp, armor=armor, corpse=corpse)
        Abilities.__init__(self)

    def death(self):
        """ Death method """
        events.Event(self.location, {'type': 'entity_died', 'entity': self})  # fire an event
        corpse = self.get_corpse()  # get corpse entity
        if corpse:
            self.location.place_entity(corpse, self.position[0], self.position[1])
        self.location.remove_entity(self)


class Door(BattleEntity, Entity):
    """
        Mixed class of a door, that has HP and can be destroyed, has open/closed state, blocks los when closed.
    """

    def __init__(self, name, data_id, description, char_closed, char_open, color, hp, weight=0, armor=None, pass_cost=1,
                 is_closed=True, corpse='no corpse'):
        self.char_closed = char_closed  # char representing closed door
        self.char_open = char_open  # char representing open door
        self.is_closed = is_closed  # is door closed or open
        if is_closed:
            blocks_los = True
            blocks_shots = 1
        else:
            blocks_los = False
            blocks_shots = 0
        self.__set_char()  # set current char for drawing purposes
        Entity.__init__(self, name=name, data_id=data_id, description=description, char=self.char, color=color,
                        occupies_tile=self.is_closed, blocks_los=blocks_los, blocks_shots=blocks_shots,
                        weight=weight, pass_cost=pass_cost)
        BattleEntity.__init__(self, hp, armor=armor, corpse=corpse)

    def __set_char(self):
        """ Method sets current character to display according to open/closed state """
        if self.is_closed:
            self.char = self.char_closed
        else:
            self.char = self.char_open

    def open(self):
        """ Method that opens the door """
        if self.is_closed:
            self.is_closed = False
            self.occupies_tile = False
            self.__set_char()
            self.blocks_los = False
            self.blocks_shots = 0
            self.location.path_map_update(self.position[0], self.position[1])  # update path map
            return True  # if action successful
        return False  # if it's not

    def close(self):
        """ Method that closes the door """
        if not self.is_closed:
            self.is_closed = True
            self.occupies_tile = True
            self.__set_char()
            self.blocks_los = True
            self.blocks_shots = 1
            self.location.path_map_update(self.position[0], self.position[1])  # update path map
            return True  # if action successful
        return False  # if it's not

    def death(self):
        """ Death method """
        events.Event(self.location, {'type': 'entity_died', 'entity': self})  # fire an event
        corpse = self.get_corpse()  # get corpse entity
        if corpse:
            self.location.place_entity(corpse, self.position[0], self.position[1])
        self.location.remove_entity(self)


class Location:
    """
        Represents a location, has a grid (nested list) of Cells
    """

    def __init__(self, height, width):
        self.height = height  # height of location in tiles
        self.width = width  # width of location in tiles
        self.cells = []  # list of Cell objects
        self.action_mgr = actions.ActionMgr()  # action manager for this location
        self.entities = set()  # a set of Entities
        self.seers = []  # a list of Seer objects, to recompute their FOV if map changes
        self.actors = []  # a list of Actor objects
        self.dead = []  # list of dead BattleEntities to be removed
        # WARNING! it's a hack, graphic-related info stored in loc, to save/load it with the loc
        self.out_of_sight_map = {}  # dict for storing explored, but invisible tiles
        self.path_map = [[1 for i in range(width)] for j in range(height)]  # a list of path cost numbers

    def is_in_boundaries(self, x, y):
        """ Method validating coordinates, to avoid out of range errors  """
        if (x >= 0) and (y >= 0) and (x < self.width) and (y < self.height):
            return True
        return False

    def entities_reobserve(self):
        """ Register all entities observers - i.e. when game loads """
        for ent in self.entities:
            self.reobserve_entity(ent)

    def reobserve_entity(self, entity):
        """ Register entity's observers if needed """
        if entity in self.entities:
            try:  # if entity has AI component - register event observer
                ai = entity.ai
                ai.reobserve()
            except AttributeError:
                pass
            if isinstance(entity, Abilities):  # if entity has abilities - register them as event observers
                for ability in entity.abilities:
                    ability.reobserve()
        else:
            raise Exception('Tried to reobserve entity not from this loc.')

    def reg_entity(self, entity):
        """ Method that registers entity to location (and loads a new one from data, if needed) """
        if entity not in self.entities:
            if isinstance(entity, str):  # if entity is not an Entity object, but a string - load from data
                entity = dataset.get_entity(entity)
                entity.location = self  # update entity location
                self.entities.add(entity)
                self.reobserve_entity(entity)
            else:
                entity.location = self  # update entity location
                self.entities.add(entity)
                self.reobserve_entity(entity)
            if isinstance(entity, Actor):  # check if entity is an Actor
                self.actors.append(entity)  # add it to Actors list
            if isinstance(entity, Inventory):  # check if entity has inventory
                for item in entity.inventory:  # register every item
                    self.reg_entity(item)
            events.Event(self, {'type': 'entity_registered', 'entity': entity})  # fire an event
        return entity

    def place_entity(self, entity, x, y):
        """ Method that places given entity on the location (and loads a new one from data, if needed) """
        if self.is_in_boundaries(x, y):  # validate coordinates
            entity = self.reg_entity(entity)  # register entity before placing
            self.cells[x][y].entities.append(entity)  # add entity to Cell list
            entity.position = (x, y)  # update entity position
            if isinstance(entity, Seer):  # check if entity is a Seer
                entity.compute_fov()  # recompute it's FOV
                self.seers.append(entity)  # add it to Seers list
            if entity.blocks_los:  # if placed entity blocks los, recompute fov for adjacent Seers
                for seer in self.seers:
                    if hypot(entity.position[0] - seer.position[0],
                             entity.position[1] - seer.position[1]) <= seer.sight_radius:
                        seer.compute_fov()
            if entity.occupies_tile or entity.pass_cost != 1:  # if entity blocks or impairs movement
                self.path_map_update(x, y)  # update path map
            events.Event(self, {'type': 'entity_placed', 'entity': entity})  # fire an event
            return entity
        else:
            raise Exception('Attempted to place entity outside of location.', entity.name)

    def remove_entity(self, entity):
        """ Method that removes entity from location """
        events.Event(self, {'type': 'entity_removed', 'entity': entity})  # fire an event
        # remove entity from cell
        if entity.position:
            entity.location.cells[entity.position[0]][entity.position[1]].entities.remove(entity)
        if isinstance(entity, Seer):  # check if entity is a Seer
            self.seers.remove(entity)  # remove from seers list
        if isinstance(entity, Actor):  # check if entity is an Actor
            for action in entity.actions:  # remove actions from ActMgr
                self.action_mgr.remove_action(action)
            self.actors.remove(entity)  # remove from actors list
        if isinstance(entity, Abilities):  # check if entity has abilities
            for abil in entity.abilities:  # remove them from observers
                abil.close()
        try:  # if entity has AI component - remove it from observers
            ai = entity.ai
            ai.close()
        except AttributeError:
            pass
        if entity.blocks_los:  # if removed entity blocked los, recompute fov for adjacent Seers
            for seer in self.seers:
                if hypot(entity.position[0] - seer.position[0],
                         entity.position[1] - seer.position[1]) <= seer.sight_radius:
                    seer.compute_fov()
        if entity.occupies_tile or entity.pass_cost != 1:  # if entity blocks or impairs movement
            self.path_map_update(entity.position[0], entity.position[1])  # update path map
        entity.position = None
        entity.location = None
        if entity in self.entities:
            self.entities.remove(entity)  # remove from entities set
        del entity

    def reap(self):
        """ Method that removes all dead entities at the end of tick """
        for victim in self.dead[:]:
            try:
                victim.death()
            except AttributeError:  # if no death method specified - just remove from location
                self.remove_entity(victim)
            self.dead.remove(victim)

    def cell_blocks_sight(self, x, y):
        """ Method that determines, is cell at x, y is blocking sight """
        if self.is_in_boundaries(x, y):  # check if cell coords are in boundaries
            return not self.cells[x][y].is_transparent()  # return if cell is transparent
        return False  # if out of bounds, edge of the map certainly block los ;)

    def get_move_cost(self, start, end):
        """ Method that returns movement cost (for A*) """
        dest_x, dest_y = end
        if self.cells[dest_x][dest_y].is_there_a(Player):  # if there a player - mark it as passable
            return self.cells[dest_x][dest_y].get_move_cost()
        actor = self.cells[dest_x][dest_y].is_there_a(Actor)
        if actor:  # if there is an actor - add 'not moved' turns count to prevent monster jams in narrow places
            if actor.not_moved > 100:
                print('not moved = ' + str(actor.not_moved))
            return self.cells[dest_x][dest_y].get_move_cost() + actor.not_moved * actor.speed
        else:
            return self.path_map[dest_x][dest_y]

    def path_map_recompute(self):
        """ Method that recomputes path map """
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].is_movement_allowed():
                    self.path_map[x][y] = self.cells[x][y].get_move_cost()
                else:
                    self.path_map[x][y] = self.width * self.height  # set cost too high

    def path_map_update(self, x, y):
        """ Method that updates single cell of path map """
        if self.cells[x][y].is_movement_allowed():
            self.path_map[x][y] = self.cells[x][y].get_move_cost()
        else:
            self.path_map[x][y] = self.width * self.height  # set cost too high

    def find_place(self, settings):
        """ Method that finds a place for something, specified in settings """
        if settings['shape'] == 'rect':  # rectangular shape
            size_x = settings['size_x']
            size_y = settings['size_y']
            if settings['place'] == 'random':
                for i in range(settings['tries']):
                    match = True  # place matches conditions or not
                    x = random.randrange(self.width - size_x)
                    y = random.randrange(self.height - size_y)
                    # make a set of cells in shape
                    shape_cells = set()
                    for xs in range(x, x + size_x):
                        for ys in range(y, y + size_y):
                            shape_cells.add(self.cells[xs][ys])
                    # check cells for conditions, specified in settings
                    for cell in shape_cells:
                        if 'placing' in settings:
                            if 'passable' in settings['placing'] and cell.blocks_move:
                                match = False
                                break
                    if match:
                        return x, y
        return None  # TODO: throw some exception


class Game:
    """
        Representation of whole game model, list of locations, game state, some between-locations info in the future.
    """
    log = []  # a list of game messages (like damage, usage of items, etc) each message has level:

    # DEBUG - debug messages
    # PLAYER - messages visible to player by default
    # it is static, because passing a Game object instance to each method that needs write lo log is not right

    def __init__(self, game_type='new'):
        self.current_loc = None  # current location
        self.player = None  # player object
        self.state = ''  # game state, like 'playing', 'looking', 'menu'
        self.is_waiting_input = True  # is game paused and waiting for player input
        self.loop_is_running = False  # this flag must be true when main_loop is running
        self.locations = []  # list of locations
        self.time_system = actions.TimeSystem()  # time system object
        self.show_debug_log = False  # show debug log to player

        if game_type == 'new':  # constructor option for new game start
            self.new_game()

    def start_update_thread(self):
        """ This method starts game update thread (containing main loop) """
        # threading is used to make UI responsible to input while game logic updates.
        # Also, removed situations, when long keypresses result in multiple moves at once instead of one-by-one
        if self.loop_is_running:
            return  # if loop is already running - don't run another one
        # t = ProfiledThread(target=self._main_loop)
        t = threading.Thread(target=self._main_loop)
        t.start()

    def _main_loop(self):
        """ Main game loop function (time advancement, performing actions etc) """
        if self.loop_is_running:
            raise(Warning('Multiple main_loops running at the same time!'))
        self.loop_is_running = True
        while not self.player.state == 'ready':
            if self.state == 'playing':  # check if state is 'playing'
                if self.is_waiting_input:  # check if game is waiting for player input
                    if not self.player.state == 'ready':  # if after command execution player is performing an action
                        self.is_waiting_input = False  # set waiting for input flag to False
                else:  # if not waiting for input
                    self.time_system.pass_time()  # pass game time, fire events
                    self.current_loc.reap()  # if there are dead after tick - call their death() methods
                    if self.player.state == 'dead':  # check if player is dead
                        self.state = 'dead'  # set game state to dead
                        self.is_waiting_input = True  # set waiting for input flag True
                        break
                    for actor in self.current_loc.actors:  # iterate through actors
                        if actor.state == 'ready' and actor.ai:  # pick those who have ai and ready to act
                            actor.ai.act()  # make them act
        self.is_waiting_input = True  # set waiting for input flag True
        self.loop_is_running = False

    def new_game(self):
        """ Method that starts a new game. Mostly a placeholder now. """
        self.current_loc = generation.generate_loc('ruins', None, 200, 200)
        self.add_location(self.current_loc)
        self.player = Player(name='Player', data_id='player', description='A player character.', char='@',
                             color=[255, 255, 255], hp=20, speed=100, sight_radius=23, damage=1,
                             categories={'living'}, properties={'money': 0, 'max_carry_weight': 30}, weight=70)
        start_x, start_y = 0, 0
        for i in range(100):  # look for acceptable random position
            x = random.randrange(self.current_loc.width // 4, self.current_loc.width // 4 * 3)
            y = random.randrange(self.current_loc.height // 4, self.current_loc.height // 4 * 3)
            if self.current_loc.cells[x][y].is_movement_allowed:
                enemies_near = False
                for point in circle_points(r=20, include_center=False):  # check for an enemy near player
                    p_x = point[0] + x
                    p_y = point[1] + y
                    if self.current_loc.cells[p_x][p_y].is_there_a(Fighter):
                        enemies_near = True
                        break
                if not enemies_near:
                    start_x, start_y = x, y
                    break
        self.current_loc.place_entity(self.player, start_x, start_y)
        # self.player.add_item(self.current_loc.place_entity('item_wall_smasher', 10, 10))
        # self.current_loc.place_entity('mob_frost_wisp', 20, 20)
        self.current_loc.actors.remove(self.player)  # A hack, to make player act first if acting in one tick
        self.current_loc.actors.insert(0, self.player)
        self.is_waiting_input = True
        self.state = 'playing'

    def enter_camp(self):
        """ Method that must be called when player enters camp """
        self.state = 'camp'

    def leave_camp(self):
        """ Method that must be called when player leaves camp """
        if self.current_loc:
            self.state = 'playing'
        else:
            raise RuntimeError('Left camp to None location.')

    def add_location(self, location):
        """ Method that adds a location to the game """
        self.time_system.register_act_mgr(location.action_mgr)  # register act manager to time system
        self.locations.append(location)

    def remove_location(self, location):
        """ Method that removes location from the game """
        self.time_system.unregister_act_mgr(location.action_mgr)  # unregister act manager to time system
        self.locations.remove(location)
        del location

    def locations_reobserve(self):
        """ Method to register observer for all locations """
        for loc in self.locations:
            loc.entities_reobserve()

    @staticmethod
    def add_message(message, level, color):
        """ Method that adds a message to log """
        Game.log.append((message, level, color))

    @staticmethod
    def clear_log():
        """ Method that clears mesage log """
        Game.log.clear()


# ======================================= UTILITY FUNCTIONS ============================================
def weighted_choice(choices):
    """ Weighted choice function """
    total = sum(w for c, w in choices)
    random.seed()
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"


def determine_number(dmg):
    """ Function that determines number if it's a (min, max) tuple """
    try:  # if damage is (min, max) tuple
        random.seed()
        min_dmg = dmg[0]
        max_dmg = dmg[1]
        dmg = random.randint(min_dmg, max_dmg)
    except TypeError:  # if not a tuple - must be int
        pass
    return dmg


def ranged_hit_probability(weapon_acc, weapon_maxrange, range_to_target, mods=None):
    """ Function that determines if shot hits the target """
    # TODO: implement accuracy modifications
    # goal - to make 70% at range/2, almost 95% one tile away, and very low probability at max range
    # some math ahead (magic numbers included)
    hit_prob = 1 - random.betavariate(2, 3)  # probability to hit, Expected value 0.70
    weapon_halfrange = weapon_maxrange / 2
    if range_to_target >= weapon_halfrange:  # if target is farther than half range of the weapon
        range_coef = 0.01 + weapon_halfrange / range_to_target  # calculate (0.01, 1.01) range coefficient
    else:  # if target is near
        range_coef = 1 + (1 - (range_to_target / weapon_halfrange))  # calculate (1, 2) range coefficient
    hit_value = hit_prob * range_coef * weapon_acc
    if hit_value >= 0.5:  # translate probability to boolean hit-or-not
        return True
    else:
        return False


def circle_points(r, include_center):
    """ Function that returns points within the circle at (0, 0). r - radius """
    points = set()
    for x in range(int(r) + 1):
        for y in range(int(r) + 1):
            if x ** 2 + y ** 2 <= r ** 2:  # if point within the circle
                if not (x == 0 and y == 0):
                    points.add((x, y))  # add 4 points, because of symmetry
                    points.add((-x, -y))
                    points.add((-x, y))
                    points.add((x, -y))
    if include_center:
        points.add((0, 0))
    return points

"""
    This file contains game logic objects.
"""
import actions
import fov_los
import effects
import events

import random
from math import hypot


class Cell:
    """
        Class represents a single cell in location grid
    """

    def __init__(self, tile_type, blocks_move=False, blocks_los=False, explored=False):
        self.explored = explored  # is tile explored?
        self.tile = tile_type  # tile type for drawing purposes (i.e. 'WALL', 'FLOOR')
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

    def __init__(self, name='', description='', char=' ', color=None, location=None, position=None, occupies_tile=False,
                 blocks_los=False):
        self.name = name  # entity name
        self.description = description  # entity's description
        self.location = location  # Location object, where entity is placed
        self.position = position  # (x, y) tuple, represents position in the location
        self.occupies_tile = occupies_tile  # entity occupy tile? (no other occupying entity can be placed there)
        self.blocks_los = blocks_los  # is it blocking line of sight? walls do, monsters (usually) don't
        self.char = char  # char that represents entity in graphics ('@')
        self.color = color  # entity char color
        self.effects = []  # entity effects

    def __str__(self):
        """ Method returns string representation of an entity - it's name """
        return self.name


class BattleEntity(Entity):
    """
        Mixin class, adds combat related functionality to the Entity.
        Hp, taking/inflicting damage, that kind of stuff.
    """

    def __init__(self, hp):
        self.hp = hp  # current hitpoints
        self.maxhp = hp  # maximum hitpoints

    def take_damage(self, damage):
        """ This method should be called if entity is damaged """
        self.hp -= damage
        if self.hp <= 0:
            self.death()

    def deal_damage(self, target, damage):
        """ Method for dealing damage """
        if isinstance(target, BattleEntity):
            target.take_damage(damage)  # inflict that damage to target
            events.Event('location', {'type': 'entity_damaged', 'attacker': self,
                                      'target': target, 'damage': damage})  # fire an event
        else:
            raise Exception('Attempted to damage non-BattleEntity entity. ', self.name)

    def death(self):
        """ Abstract method that is called when BattleEntity dies """
        raise NotImplementedError


class Seer(Entity):
    """
        Mixin class, adds visibility (FOV & LOS) functionality to Entity.
    """

    def __init__(self, sight_radius):
        self.sight_radius = sight_radius  # sight radius in tiles
        self.fov_set = ()  # field of view - set of (x, y) points

    def compute_fov(self):
        """ Method that calculates FOV """
        self.fov_set = fov_los.get_fov(self.position[0], self.position[1], self.location, self.sight_radius)
        if isinstance(self, Player):
            for point in self.fov_set:
                if self.location.is_in_boundaries(point[0], point[1]):
                    self.location.cells[point[0]][point[1]].explored = True

    def is_in_fov(self, x, y):
        """ Method that determines is a cell in Seer's FOV """
        return (x, y) in self.fov_set


class Actor(Entity):
    """
        Mixin class, adds acting functionality to the Entity.
        Time-system related stuff.
    """

    def __init__(self, speed, state='ready', ai=None):
        self.speed = speed  # overall speed factor of actions
        self.state = state  # actor state - ready, acting or withdrawal (for now)
        self.actions = []  # list of actions
        self.ai = ai  # ai component

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
                    self.location.cells[self.position[0]][self.position[1]].entities.remove(self)
                    self.location.cells[new_x][new_y].entities.append(self)  # add to new cell
                    self.position = (new_x, new_y)  # update entity position
                    events.Event('location', {'type': 'entity_moved', 'entity': self})  # fire an event
                    msg = self.name + 'moved to ' + str(new_x) + ':' + str(new_y)
                    Game.add_message(msg, 'DEBUG', [255, 255, 255])
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


class Inventory(Entity):
    """
        Mixin class, adds inventory to Entity.
    """

    def __init__(self):
        self.inventory = []  # a list of Item objects

    def add_item(self, item):
        """ Item adding method """
        self.inventory.append(item)  # add item to inventory
        item.owner = self  # set item's owner
        if item.location:  # if it's placed somewhere in location
            item.location.remove_entity(item)

    def drop_item(self, item):
        """ Item dropping method (in a location) """
        item.owner = None
        self.location.place_entity(item, self.position[0], self.position[1])  # place it on the map
        self.inventory.remove(item)

    def discard_item(self, item):
        """ Method that removes item from inventory, without placing it anywhere """
        item.owner = None
        self.inventory.remove(item)

    def use_item(self, item):
        """ Item use on self method """
        item.use(self)


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

    def equip_item(self, item, slot):
        """ Method for equipping items """
        if self.equipment[slot]:
            self.add_item(self.equipment[slot])  # add old item to inventory
        if item in self.inventory:  # if item is in inventory - remove it
            self.discard_item(item)
        item.owner = self  # set item owner
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


class AI(events.Observer):
    """ Base class that represents monster AI """

    def __init__(self, state):
        self.state = state  # state of AI, i.e. 'sleeping', 'wandering', 'chasing'
        self.owner = None  # owner Entity of ai object. TODO: hack - owner set externally
        events.Observer.__init__(self)  # register self as observer

    def act(self):
        """ Abstract method of AI class that is called when AI should decide what to do """
        raise NotImplementedError


class SimpleMeleeChaserAI(AI):
    """ A simple melee chaser monster AI """

    def __init__(self, state='idle'):
        AI.__init__(self, state)
        self.observe('location', self.on_event_location)

    def on_event_location(self, data):
        """ Method handling location-related events """
        if data['type'] == 'entity_moved':
            if isinstance(data['entity'], Player):
                pl_x = data['entity'].position[0]
                pl_y = data['entity'].position[1]
                if hypot(pl_x - self.owner.position[0], pl_y - self.owner.position[1]) <= self.owner.sight_radius:
                    self.state = 'alert'
                else:
                    self.state = 'idle'

    def act(self):
        """ Method called when monster is ready to act """
        if self.state == 'alert':
            x = self.owner.position[0]
            y = self.owner.position[1]
            for point in self.owner.fov_set:
                player = self.owner.location.cells[point[0]][point[1]].is_there_a(Player)
                if player:
                    if hypot(point[0] - self.owner.position[0], point[1] - self.owner.position[1]) <= 1.42:
                        self.owner.perform(actions.act_attack_melee, self.owner, player)
                    else:
                        los = fov_los.get_los(x, y, point[0], point[1])
                        step_cell = los[1]
                        self.owner.perform(actions.act_move, self.owner, step_cell[0] - x, step_cell[1] - y)
            if self.owner.state == 'ready':
                self.owner.perform(actions.act_wait, self.owner, self.owner.speed)


class Item(Entity):
    """
        Mixed class, simple Item.
    """

    def __init__(self, name, description, char, color, equip_slots=None, categories=None):
        # calling constructors
        Entity.__init__(self, name=name, description=description, char=char, color=color, occupies_tile=False)
        self.owner = None  # owner of item - entity with inventory
        self.categories = categories  # item categories - a potion, a sword, etc
        if equip_slots:  # equipment slots, in which item can be placed
            self.equip_slots = equip_slots
        else:  # by default - can be taken to hands
            self.equip_slots = dict.fromkeys(['RIGHT_HAND', 'LEFT_HAND'])

    def use(self, target):
        """ Item using method """
        for effect in self.effects:
            if effect.eff == 'HEAL':  # if item has HEAL effect - heal the user
                result_hp = target.hp + effect.magnitude
                if result_hp > target.maxhp:
                    target.hp = target.maxhp
                else:
                    target.hp = result_hp
                msg = self.name + ' heals ' + target.name + ' for ' + str(effect.magnitude) + ' HP.'
                Game.add_message(msg, 'PLAYER', [255, 255, 255])


class ItemCharges(Item):
    """
        Child class of item that has charges
    """

    def __init__(self, name, description, char, color, charges,
                 categories=None, destroyed_after_use=True, equip_slots=None):
        super(ItemCharges, self).__init__(name=name, description=description, categories=categories,
                                          char=char, color=color, equip_slots=equip_slots)
        self.destroyed_after_use = destroyed_after_use  # if True, item is destroyed when charges are depleted
        self.charges = charges  # number of uses

    def use(self, target):
        """ Overrides the use() method, to manage charges and item destruction """
        if self.charges > 0:  # if there are remaining charges
            super(ItemCharges, self).use(target)  # call parent method
            self.charges -= 1  # use 1 charge
        else:
            msg = self.name + ' is depleted!'
            Game.add_message(msg, 'PLAYER', [255, 255, 255])
        if self.destroyed_after_use and self.charges == 0:
            self.owner.discard_item(self)  # if item is depleted and destroys when empty - remove it from inventory


class Fighter(BattleEntity, Equipment, Inventory, Actor, Seer, Entity):
    """
        Mixed class, basic monster, that can participate in combat and perform actions.
    """

    def __init__(self, name, description, char, color, hp, speed, sight_radius,
                 damage, equip_layout='humanoid', ai=None):
        # calling constructors of mixins
        Entity.__init__(self, name=name, description=description, char=char, color=color, occupies_tile=True)
        BattleEntity.__init__(self, hp=hp)
        if ai:  # set AI owner
            ai.owner = self
        Actor.__init__(self, speed=speed, ai=ai)
        Seer.__init__(self, sight_radius=sight_radius)
        Inventory.__init__(self)
        Equipment.__init__(self, layout=equip_layout)
        self.damage = damage  # damage from basic melee 'punch in da face' attack

    def attack_melee(self, target):
        """ Attack in melee method """
        # check if target is in melee range
        dist_to_target = hypot(target.position[0] - self.position[0], target.position[1] - self.position[1])
        if dist_to_target <= 1.42:
            dmg = 0
            for item in self.equipment.values():  # check if any weapons equipped
                if item:
                    if 'weapon' in item.categories:
                        for eff in item.effects:
                            if eff.eff == 'INCREASE_MELEE_DAMAGE':
                                dmg += eff.magnitude
                        if 'sword' in item.categories:
                            random.seed()
                            dmg = random.randrange(dmg - dmg // 3, dmg + dmg // 3)  # a sword damage dispersion
                        if 'dagger' in item.categories:
                            random.seed()
                            dmg = random.randrange(dmg - dmg // 2, dmg + dmg // 2)  # a dagger damage dispersion
                        if 'blunt' in item.categories:
                            random.seed()
                            dmg = random.randrange(dmg - dmg // 5, dmg + dmg // 5)  # a blunt weapon damage dispersion
            if dmg == 0:
                dmg = self.damage
            msg = self.name + ' attacks ' + target.name + ' and deals ' + str(dmg) + ' damage!'
            Game.add_message(msg, 'PLAYER', [255, 255, 255])
            msg = self.name + '/' + target.name + 'for' + str(dmg) + 'dmg@' + str(
                target.position[0]) + ':' + str(target.position[1])
            Game.add_message(msg, 'DEBUG', [255, 255, 255])
            self.deal_damage(target, dmg)  # deal damage
        else:
            msg = self.name + 'misses,dist=' + str(dist_to_target)
            Game.add_message(msg, 'DEBUG', [255, 255, 255])

    def death(self):
        """ Death method """
        Game.add_message(self.name + ' dies!', 'PLAYER', [255, 255, 255])
        Game.add_message(self.name + 'die', 'DEBUG', [255, 255, 255])
        events.Event('location', {'type': 'entity_died', 'entity': self})  # fire an event
        corpse = Item(name=self.name + "'s corpse.", description='A dead ' + self.name + '.', char='%',
                      color=self.color)
        self.location.place_entity(corpse, self.position[0], self.position[1])
        for item in self.equipment.values():  # drop all equipped items
            if item:
                self.drop_equipped_item(item)
        for item in self.inventory:  # drop all inventory items
            self.drop_item(item)
        self.location.remove_entity(self)
        self.ai.close()  # unregister Observer


class Player(Fighter):
    """
        Child class, adds player-specific functionality to Fighter.
    """

    def __init__(self, name, description, char, color, hp, speed, sight_radius, damage):
        # calling constructor of parent class
        Fighter.__init__(self, name=name, description=description, char=char, color=color, hp=hp, speed=speed,
                         sight_radius=sight_radius, damage=damage, ai=None)

    def death(self):
        """ Death method """
        Game.add_message('You died!', 'PLAYER', [255, 0, 0])
        Game.add_message(self.name + 'player died', 'DEBUG', [255, 255, 255])
        self.char = '%'
        self.color = [255, 0, 0]
        self.state = 'dead'


class Wall(BattleEntity, Entity):
    """
        Mixed class of a wall, that has HP and can be destroyed, but lacks acting ability.
    """

    def __init__(self, name, char, hp, description='', color=None, blocks_los=True):
        Entity.__init__(self, name=name, description=description, char=char, color=color,
                        occupies_tile=True, blocks_los=blocks_los)
        BattleEntity.__init__(self, hp)

    def death(self):
        """ Death method """
        events.Event('location', {'type': 'entity_died', 'entity': self})  # fire an event
        self.location.remove_entity(self)


class Door(BattleEntity, Entity):
    """
        Mixed class of a door, that has HP and can be destroyed, has open/closed state, blocks los when closed.
    """

    def __init__(self, name, description, char_closed, char_open, color, hp, is_closed=True):
        self.char_closed = char_closed  # char representing closed door
        self.char_open = char_open  # char representing open door
        self.is_closed = is_closed  # is door closed or open
        if is_closed:
            blocks_los = True
        else:
            blocks_los = False
        self.__set_char()  # set current char for drawing purposes
        Entity.__init__(self, name=name, description=description, char=self.char, color=color,
                        occupies_tile=self.is_closed, blocks_los=blocks_los)
        BattleEntity.__init__(self, hp)

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
            return True  # if action successful
        return False  # if it's not

    def close(self):
        """ Method that closes the door """
        if not self.is_closed:
            self.is_closed = True
            self.occupies_tile = True
            self.__set_char()
            self.blocks_los = True
            return True  # if action successful
        return False  # if it's not

    def death(self):
        """ Death method """
        events.Event('location', {'type': 'entity_died', 'entity': self})  # fire an event
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
        # self.entities = []  # a list of Entities
        self.seers = []  # a list of Seer objects, to recompute their FOV if map changes
        self.actors = []  # a list of Actor objects
        # WARNING! it's a hack, graphic-related info stored in loc, to save/load it with the loc
        self.out_of_sight_map = {}  # dict for storing explored, but invisible tiles

    def is_in_boundaries(self, x, y):
        """ Method validating coordinates, to avoid out of range errors  """
        if (x >= 0) and (y >= 0) and (x < self.width) and (y < self.height):
            return True
        return False

    def generate(self, pattern):
        """ Mapgen method, mostly placeholder for now."""
        if pattern == 'clear':  # simply make a location full of sand tiles
            self.cells.clear()
            self.cells = [[Cell('SAND') for y in range(self.height)] for x in range(self.width)]
        if pattern == 'ruins':  # simply make a location of sand and few wall and door elements
            self.cells.clear()
            self.cells = [[Cell('SAND') for y in range(self.height)] for x in range(self.width)]
            random.seed()
            for i in range(0, random.randint(2, 40)):
                wall = Wall(name='Wall', description='A wall.', char='#', color=[255, 255, 255], hp=100)
                self.place_entity(wall, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(2, 20)):
                door = Door(name='Door', description='A door.', char_closed='+', char_open='.', color=[255, 255, 255],
                            hp=100, is_closed=True)
                self.place_entity(door, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(2, 20)):
                item = Item(name='boulder', description='A stone boulder.', categories={'rubbish'},
                            char='*', color=[200, 200, 200])
                self.place_entity(item, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(1, 5)):
                item = ItemCharges(name='healing potion', description='A potion that heals 5 HP.',
                                   categories={'consumable', 'potion'}, char='!', color=[255, 0, 0],
                                   charges=1, destroyed_after_use=True)
                item.effects.append(effects.Effect('HEAL', 5))
                self.place_entity(item, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(1, 2)):
                item = Item(name='sabre', description='A sharp sabre with pointy tip.',
                            categories={'weapon', 'sword', 'speed_normal'}, char='/', color=[200, 200, 255])
                item.effects.append(effects.Effect('INCREASE_MELEE_DAMAGE', 5))
                self.place_entity(item, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(1, 2)):
                item = Item(name='dagger', description='A simple dagger about 20cm long.',
                            categories={'weapon', 'dagger', 'speed_fast'}, char=',', color=[200, 200, 255])
                item.effects.append(effects.Effect('INCREASE_MELEE_DAMAGE', 3))
                self.place_entity(item, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(1, 2)):
                item = Item(name='bronze maul', description='Huge bronze sphere attached on top of a wooden pole.',
                            categories={'weapon', 'blunt', 'speed_slow'}, char='/', color=[80, 50, 20])
                item.effects.append(effects.Effect('INCREASE_MELEE_DAMAGE', 10))
                self.place_entity(item, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(3, 10)):
                enemy = Fighter(name='Mindless body', description='No description, normal debug monster.', char='b',
                                color=[109, 49, 9], hp=5, speed=100, sight_radius=14.5, damage=1,
                                ai=SimpleMeleeChaserAI())
                self.place_entity(enemy, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(0, random.randint(1, 3)):
                enemy = Fighter(name='Sand golem', description='No description, slow debug monster.', char='G',
                                color=[255, 255, 0], hp=20, speed=200, sight_radius=9.5, damage=4,
                                ai=SimpleMeleeChaserAI())
                self.place_entity(enemy, random.randint(0, self.width - 1), random.randint(0, self.height - 1))

    def place_entity(self, entity, x, y):
        """ Method that places given entity on the location """
        if self.is_in_boundaries(x, y):  # validate coordinates
            self.cells[x][y].entities.append(entity)  # add entity to Cell list
            entity.position = (x, y)  # update entity position
            entity.location = self  # update entity location
            if isinstance(entity, Seer):  # check if entity is a Seer
                entity.compute_fov()  # recompute it's FOV
                self.seers.append(entity)  # add it to Seers list
            if isinstance(entity, Actor):  # check if entity is an Actor
                self.actors.append(entity)  # add it to Actors list
            if entity.blocks_los:  # if placed entity blocks los, recompute fov for adjacent Seers
                for seer in self.seers:
                    if hypot(entity.position[0] - seer.position[0],
                             entity.position[1] - seer.position[1]) <= seer.sight_radius:
                        seer.compute_fov()
            events.Event('location', {'type': 'entity_placed', 'entity': entity})  # fire an event
        else:
            raise Exception('Attempted to place entity outside of location.', entity.name)

    def remove_entity(self, entity):
        """ Method that removes entity from location """
        events.Event('location', {'type': 'entity_removed', 'entity': entity})  # fire an event
        # remove entity from cell
        entity.location.cells[entity.position[0]][entity.position[1]].entities.remove(entity)
        entity.position = None
        entity.location = None
        if isinstance(entity, Seer):  # check if entity is a Seer
            self.seers.remove(entity)  # remove from seers list
        if isinstance(entity, Actor):  # check if entity is an Actor
            for action in entity.actions:  # remove actions from ActMgr
                self.action_mgr.remove_action(action)
            self.actors.remove(entity)  # remove from actors list
        if entity.blocks_los:  # if removed entity blocked los, recompute fov for adjacent Seers
            for seer in self.seers:
                if hypot(entity.position[0] - seer.position[0],
                         entity.position[1] - seer.position[1]) <= seer.sight_radius:
                    seer.compute_fov()
        del entity

    def is_cell_transparent(self, x, y):
        """ Method that determines, is cell at x, y is transparent """
        if self.is_in_boundaries(x, y):  # check if cell coords are in boundaries
            return self.cells[x][y].is_transparent()  # return if cell is transparent
        return False  # if out of bounds, edge of the map certainly block los ;)


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
        self.locations = []  # list of locations
        self.time_system = actions.TimeSystem()  # time system object
        self.show_debug_log = False  # show debug log to player

        if game_type == 'new':  # constructor option for new game start
            self.new_game()

    def new_game(self):
        """ Method that starts a new game. Mostly a placeholder now. """
        self.current_loc = Location(100, 100)
        self.add_location(self.current_loc)
        self.current_loc.generate('ruins')
        self.player = Player(name='Player', description='A player character.', char='@', color=[255, 255, 255],
                             hp=10, speed=100, sight_radius=23.5, damage=2)
        self.current_loc.place_entity(self.player, 10, 10)
        self.current_loc.actors.remove(self.player)  # A hack, to make player act first if acting in one tick
        self.current_loc.actors.insert(0, self.player)
        self.is_waiting_input = True
        self.state = 'playing'

    def add_location(self, location):
        """ Method that adds a location to the game """
        self.time_system.register_act_mgr(location.action_mgr)  # register act manager to time system
        self.locations.append(location)

    @staticmethod
    def add_message(message, level, color):
        """ Method that adds a message to log """
        Game.log.append((message, level, color))

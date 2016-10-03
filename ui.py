"""
    This file contains user interface. For now uses tdl (maybe need to move all render work to render?)
"""
import tdl
import textwrap
import math

import game_logic
import actions
import player_input
import dataset


class Element:
    """ Base class for UI element """

    def __init__(self, owner, x=0, y=0, width=0, height=0, visible=True):
        self.owner = owner  # owner (other element or window)
        self.x = x  # position in window
        self.y = y
        self.width = width  # element width
        self.height = height  # element height
        self.elements = []  # child elements
        self.visible = visible  # is element visible

    def draw(self):
        """ Abstract method, must return element appearance, ready to draw (tdl.Console for now) """
        raise NotImplementedError

    def add_element(self, element):
        """ Method for adding child elements """
        element.owner = self
        self.elements.append(element)


class ElementTextLine(Element):
    """ Simple UI element - line of text """

    def __init__(self, owner, x=0, y=0, line='', color=None, bgcolor=None, visible=True):
        super(ElementTextLine, self).__init__(owner=owner, x=x, y=y, width=len(line), height=1, visible=visible)
        self._line = line  # line of text
        if color:  # check if color specified
            self.color = color
        else:  # if not - white
            self.color = [255, 255, 255]
        if bgcolor:  # check if background color specified
            self.bgcolor = bgcolor
        else:  # if not - black
            self.bgcolor = [0, 0, 0]

    def set_line(self, line):
        """ Method used to change line """
        self._line = line  # set the line of text
        self.width = len(line)  # calculate element width accordingly

    def draw(self):
        """ Method returns tdl.Console with single line of text """
        console = tdl.Console(self.width, 1)
        console.draw_str(0, 0, self._line, self.color, self.bgcolor)  # draw a line on console
        return console


class ElementTextRect(Element):
    """ Simple UI element - rectangle with text (wrapped) """

    def __init__(self, owner, x, y, width, height, text='', color=None, bgcolor=None, visible=True):
        super(ElementTextRect, self).__init__(owner=owner, x=x, y=y, width=width, height=height, visible=visible)
        self.text = text  # text to be displayed
        if color:  # check if color specified
            self.color = color
        else:  # if not - white
            self.color = [255, 255, 255]
        if bgcolor:  # check if background color specified
            self.bgcolor = bgcolor
        else:  # if not - black
            self.bgcolor = [0, 0, 0]

    def draw(self):
        """ Method returns tdl.Console with single line of text """
        console = tdl.Console(self.width, self.height)
        console.set_mode('scroll')
        console.move(0, 0)
        console.set_colors(self.color, self.bgcolor)
        console.print_str(self.text)  # draw text on console
        return console


class ElementMainPanel(Element):
    """ Main panel with player stats, etc """

    def __init__(self, owner, player, x=0, y=0, width=0, height=0, visible=True):
        super(ElementMainPanel, self).__init__(owner=owner, x=x, y=y, width=width, height=height, visible=visible)
        self.player = player  # Player object, to obtain player-related info
        self.add_element(ElementTextLine(self, 0, 0, player.name))  # player name on top of panel
        self.player_hp = ElementTextLine(self, 0, 1, str(player.hp) + '/' + str(player.maxhp) + ' HP')  # player hp bar
        self.add_element(self.player_hp)
        # player position (for debug)
        self.player_pos = ElementTextLine(self, 0, 2, 'X:' + str(player.position[0]) + ' Y:' + str(player.position[1]))
        self.add_element(self.player_pos)
        # player equipment in hands
        self.player_hands = ElementTextLine(self, 0, 3,
                                            (', '.join([str(player.equipment['RIGHT_HAND']),
                                                        str(player.equipment['LEFT_HAND'])])))
        self.add_element(self.player_hands)

    def draw(self):
        """ Drawing method """
        # update player stats in lines
        self.player_hp.set_line(str(self.player.hp) + '/' + str(self.player.maxhp) + ' HP')
        self.player_pos.set_line('X:' + str(self.player.position[0]) + ' Y:' + str(self.player.position[1]))
        right = self.player.equipment['RIGHT_HAND']
        left = self.player.equipment['LEFT_HAND']
        if isinstance(right, game_logic.ItemRangedWeapon):  # display ammo loaded to ranged weapon
            right = str(right) + '[' + str(len(right.ammo)) + ']'
        else:
            right = str(right)
        if isinstance(left, game_logic.ItemRangedWeapon):
            left = str(left) + '[' + str(len(left.ammo)) + ']'
        else:
            left = str(left)
        self.player_hands.set_line(', '.join([right, left]))
        console = tdl.Console(self.width, self.height)
        for element in self.elements:  # blit every element to console
            console.blit(element.draw(), element.x, element.y)
        return console


class ElementItemInfo(Element):
    """ Item info for inventory """

    def __init__(self, owner, item=None, x=0, y=0, width=0, height=0, visible=True):
        super(ElementItemInfo, self).__init__(owner=owner, x=x, y=y, width=width, height=height, visible=visible)
        self._item = item  # Item object, to obtain player-related info
        self.item_name = ElementTextLine(self, 0, 0, ' ')
        self.add_element(self.item_name)  # item name on top of panel
        self.item_desc = ElementTextRect(self, 0, 1, width, height - 1)  # description of item
        self.add_element(self.item_desc)
        self.item = item

    @property
    def item(self):
        return self.item

    @item.setter
    def item(self, item: game_logic.Item):
        self._item = item
        text = ''  # clear item info
        self.item_name.set_line(' ')
        if item:  # if item is not None
            self.item_name.set_line(item.name)
            text += item.description + '\n'
            text += 'Weight: ' + str(item.weight) + ' kg.\n'
            if item.properties:
                if 'bashing' in item.properties:
                    text += 'Deals '+str(item.properties['bashing'][0])+'-'+str(item.properties['bashing'][1])+' bashing damage.\n'
                if 'slashing' in item.properties:
                    text += 'Deals '+str(item.properties['slashing'][0])+'-'+str(item.properties['slashing'][1])+' slashing damage.\n'
                if 'piercing' in item.properties:
                    text += 'Deals '+str(item.properties['piercing'][0])+'-'+str(item.properties['piercing'][1])+' piercing damage.\n'
            if len(item.effects) > 0:
                text += 'Effects: '
                for effect in item.effects:
                    text += effect.description + '\n'
            if len(item.abilities) > 0:
                text += 'Abilities: '
                for ability in item.abilities:
                    text += ability.name + '\n'
        self.item_desc.text = text  # set element text to generated text

    def draw(self):
        """ Drawing method """
        console = tdl.Console(self.width, self.height)
        for element in self.elements:  # blit every element to console
            if element.visible:
                console.blit(element.draw(), element.x, element.y)
        return console


class ElementMap(Element):
    """ Location map element  """

    def __init__(self, owner, loc, player, x=0, y=0, width=0, height=0, visible=True):
        super(ElementMap, self).__init__(owner=owner, x=x, y=y, width=width, height=height, visible=visible)
        self.loc = loc  # Location object, to obtain location-related info
        self.player = player  # Player object, to obtain player-related info
        self.cam_offset = (0, 0)  # camera offset (if at (0, 0) - centered on player)

    def move_camera(self, dx, dy):
        """ Method for moving camera by dx, dy """
        if self.owner.game.state == 'targeting':
            if math.sqrt((self.cam_offset[0] + dx) ** 2 + (self.cam_offset[1] + dy) ** 2) > self.owner.targeting_range:
                return
        self.cam_offset = (self.cam_offset[0] + dx, self.cam_offset[1] + dy)

    @staticmethod
    def cell_graphics(x, y, cell, loc, visible):
        """ Method that returns graphic representation of tile. """
        char = ' '
        color = [255, 255, 255]
        bgcolor = [0, 0, 0]
        if visible:  # check if cell is visible
            tile = dataset.get_tile(cell.tile)
            char = tile[0]
            color = tile[1]
            bgcolor = tile[2]
            brk = False
            for ent in cell.entities:  # iterate through list of entities,if there are any, display them instead of tile
                char = ent.char
                color = ent.color
                if not color:
                    color = [255, 255, 255]
                if ent.occupies_tile:  # check if there is entity, occupying tile - display it on top
                    color = ent.color
                    brk = True
                if len(cell.entities) > 1:  # if there are multiple items, replace bgcolor
                    bgcolor = cell.entities[0].color
                    if color == bgcolor:
                        bgcolor = [c - 50 for c in bgcolor]
                        i = 0
                        for c in bgcolor:
                            if c < 0:
                                bgcolor[i] = 0
                            i += 1
                if brk:
                    break
            # update visited cells map (for displaying grey out of vision explored tiles)
            loc.out_of_sight_map[(x, y)] = [char, color, bgcolor]
            return [char, color, bgcolor]
        elif cell.explored:  # check if it was previously explored
            prev_seen_cg = loc.out_of_sight_map[(x, y)]  # take cell graphic from out_of_sight map of Location
            prev_seen_cg[1] = [100, 100, 100]  # make it greyish
            prev_seen_cg[2] = [50, 50, 50]
            return prev_seen_cg
        return [char, color, bgcolor]

    def draw(self):
        """ Method that returns console with map drawn """
        console = tdl.Console(self.width, self.height)
        # player on-map coords
        player_x = self.player.position[0]
        player_y = self.player.position[1]
        # player on-screen coords
        player_scr_x = self.width // 2 - self.cam_offset[0]
        player_scr_y = self.height // 2 - self.cam_offset[1]
        for x in range(0, self.width):  # iterate through every x, y in map_console
            for y in range(0, self.height):
                rel_x = x - player_scr_x + player_x  # game location coordinates in accordance to screen coordinates
                rel_y = y - player_scr_y + player_y
                # checks if location coordinates are valid (in boundaries)
                if self.loc.is_in_boundaries(rel_x, rel_y):
                    # obtain cell graphics
                    cg = self.cell_graphics(rel_x, rel_y, self.loc.cells[rel_x][rel_y], self.loc,
                                            self.player.is_in_fov(rel_x, rel_y))
                    console.draw_char(x, y, cg[0], cg[1], cg[2])  # draw it on map_console
                else:
                    console.draw_char(x, y, ' ')  # if out of bounds then draw blank space
                if not self.cam_offset == (0, 0):
                    # if camera is not centered on player - draw there a red 'X'
                    console.draw_char(self.width // 2, self.height // 2, 'X', [255, 0, 0])
        return console


class ElementLog(Element):
    """ Game log element """

    def __init__(self, owner, game, x=0, y=0, width=0, height=0, visible=True):
        super(ElementLog, self).__init__(owner=owner, x=x, y=y, height=height, width=width, visible=visible)
        self.game = game  # game object to obtain log level

    def draw(self):
        """ Drawing method """
        console = tdl.Console(self.width, self.height)
        # get log messages, intended to be shown to player
        if self.game.show_debug_log:
            msgs = [m for m in game_logic.Game.log if m[1] == 'DEBUG']
        else:
            msgs = [m for m in game_logic.Game.log if m[1] == 'PLAYER']
        msgs = msgs[-self.height:]  # make a slice for last ones log_height ammount
        log_lines = []
        for msg in msgs:  # iterate through messages
            for line in textwrap.wrap(msg[0], self.width):  # wrap them in lines of log_width
                log_lines.append((line, msg[2]))  # store them in list
        log_lines = log_lines[-(self.height - 1):]  # slice list to log_height elements
        y = 0
        for line in log_lines:
            y += 1
            console.draw_str(0, y, line[0], line[1])  # draw each line
        return console  # a tdl.Console that contains log messages


class ElementCellInfo(Element):
    """ Selected cell info element """

    def __init__(self, owner, game, x=0, y=0, width=0, height=0, visible=False):  # not visible by default
        super(ElementCellInfo, self).__init__(owner=owner, x=x, y=y, height=height, width=width, visible=visible)
        self.game = game  # game object to obtain info

    def draw(self):
        """ Drawing method """
        console = tdl.Console(self.width, self.height)
        console.clear()
        self.elements.clear()
        entities = self.game.current_loc.cells[self.game.player.position[0] + self.owner.map.cam_offset[0]][
            self.game.player.position[1] + self.owner.map.cam_offset[1]].entities  # get entities @ selected cell
        creatures = [ent for ent in entities if ent.occupies_tile]
        items = [ent for ent in entities if isinstance(ent, game_logic.Item)]
        other = [ent for ent in entities if (not isinstance(ent, game_logic.Item)) and (not ent.occupies_tile)]
        cur_y = 0  # a 'cursor' y position
        for creature in creatures:  # show creature info if any
            self.add_element(ElementTextLine(self, 0, cur_y, creature.name + ' is here.', creature.color))
            cur_y += 1
            for ln in textwrap.wrap(creature.description, self.width):
                self.add_element(ElementTextLine(self, 0, cur_y, ln))
                cur_y += 1
        self.add_element(ElementTextLine(self, 0, cur_y, 'Items:'))
        cur_y += 1
        for item in items:  # show items if any
            self.add_element(ElementTextLine(self, 0, cur_y, item.name, item.color))
            cur_y += 1
        self.add_element(ElementTextLine(self, 0, cur_y, 'Other:'))
        cur_y += 1
        for other in other:  # show other objects
            self.add_element(ElementTextLine(self, 0, cur_y, other.name + ' is here.', other.color))
            cur_y += 1
        for element in self.elements:  # blit every element to console
            if element.visible:
                console.blit(element.draw(), element.x, element.y)
        return console


class Window:
    """ Base class for UI window """

    def __init__(self, x=0, y=0, width=0, height=0, z=0, visible=True, prev_window=None):
        self.elements = []  # UI elements, tdl consoles
        self.x = x  # position on screen
        self.y = y
        self.width = width  # element width
        self.height = height  # element height
        self.z = z  # windows are displayed by render in z-order, from lower to higher
        self.visible = visible  # is window supposed to be shown
        self.win_mgr = None  # window manager that contains window
        self.prev_window = prev_window  # previous opened window - to return after window close

    def draw(self):
        """ Abstract method, must return window appearance, ready to draw (tdl.Console for now) """
        raise NotImplementedError

    def handle_input(self):
        """ Abstract method, window must handle input """
        raise NotImplementedError

    def add_element(self, element):
        """ Method for adding child elements """
        element.owner = self
        self.elements.append(element)


class WindowMain(Window):
    """ Class for main game window """

    def __init__(self, game, x, y, width, height, z, map_width, map_height):
        super(WindowMain, self).__init__(x, y, width, height, z, True, None)  # call parent constructor
        self.game = game  # a Game object
        # elements
        self.map = ElementMap(self, game.current_loc, game.player, 0, 0, map_width, map_height)  # a map element
        self.add_element(self.map)
        self.panel = ElementMainPanel(self, game.player, map_width, 0, width - map_width, height // 2)  # panel element
        self.add_element(self.panel)
        self.log = ElementLog(self, game, map_width, height // 2, width - map_width, height // 2 - 1)  # log element
        self.add_element(self.log)
        # cell info element
        self.cell_info = ElementCellInfo(self, game, map_width, height // 2, width - map_width, height // 2 - 1)
        self.add_element(self.cell_info)
        self.cam_offset = (0, 0)  # camera offset (for looking, shooting, etc)
        self.console = tdl.Console(width, height)  # offscreen console of window
        self.targeting_range = 0  # range in 'targeting' state
        self.targeting_thing = None  # determines what player is targeting - specific scroll, weapon, ability etc
        self.targeting_command = None  # determines what command execute after targeting complete
        self.targeting_args = None  # targeting command arguments
        self.targeting_kwargs = None  # targeting command keyword arguments

    def draw(self):
        """ Window drawing method """
        self.console.clear()
        for element in self.elements:  # blit every element to console
            if element.visible:
                self.console.blit(element.draw(), element.x, element.y)
        return self.console

    # ========================== COMMAND METHODS (special cases, to prevent code duplication) ====================
    @staticmethod
    def command_default_direction(player, loc, dx, dy):
        """ Command method for player pressed direction key - move/open/attack/use default action for each type
            of object in desired cell
        """
        player_x = player.position[0]
        player_y = player.position[1]
        new_x = player_x + dx
        new_y = player_y + dy
        if loc.is_in_boundaries(new_x, new_y):  # check if new position is in the location boundaries
            if loc.cells[new_x][new_y].is_movement_allowed():  # check if movement is allowed
                player.perform(actions.act_move, player, dx, dy)  # perform move action
            door = loc.cells[new_x][new_y].is_there_a(game_logic.Door)
            if door:  # check if there is a door
                if door.is_closed:  # check if it is closed
                    player.perform(actions.act_open_door, player, door)  # open door
            # TODO: here must be more complicated check - if target is hostile, etc
            enemy = loc.cells[new_x][new_y].is_there_a(game_logic.Fighter)
            if enemy:  # check if there an enemy
                if player.equipment['LEFT_HAND'] or player.equipment['RIGHT_HAND']:
                    player.perform(actions.act_attack_melee_weapons, player, enemy)  # attack it in melee with weapon
                else:
                    player.perform(actions.act_attack_melee_basic, player, enemy)  # attack it in melee with hands

    @staticmethod
    def command_close_direction(player, loc, dx, dy):
        """ Command method for player wants to close door in some direction  """
        door_x = player.position[0] + dx
        door_y = player.position[1] + dy
        if loc.is_in_boundaries(door_x, door_y):  # check if position of selected cell is in boundaries
            door = loc.cells[door_x][door_y].is_there_a(game_logic.Door)
            if door:  # check if there is a door
                if not door.is_closed:  # check if it is closed
                    player.perform(actions.act_close_door, player, door)  # close door
                    return True
            return False

    @staticmethod
    def command_smash_direction(player, loc, dx, dy):
        """ Command method for player wants to close door in some direction  """
        be_x = player.position[0] + dx  # battle entity estimated position
        be_y = player.position[1] + dy
        if loc.is_in_boundaries(be_x, be_y):  # check if position of selected cell is in boundaries
            be = loc.cells[be_x][be_y].is_there_a(game_logic.BattleEntity)
            if be:  # check if there is a BattleEntity
                if player.equipment['LEFT_HAND'] or player.equipment['RIGHT_HAND']:
                    player.perform(actions.act_attack_melee_weapons, player, be)  # attack it in melee with weapon
                else:
                    player.perform(actions.act_attack_melee_basic, player, be)  # attack it in melee with hands
                return True
            return False

    def command_pick_up(self, player, loc, dx, dy):
        """ Command method for player wants to pick up some items  """
        x = player.position[0] + dx
        y = player.position[1] + dy
        if loc.is_in_boundaries(x, y):  # check if position of selected cell is in boundaries
            items = [i for i in loc.cells[x][y].entities if isinstance(i, game_logic.Item)]  # select items in cell
            if items:  # check if there is an item
                if len(items) == 1:
                    player.perform(actions.act_pick_up_item, player, items[0])
                else:
                    item = show_menu_inventory(self.win_mgr, items, 'Pick up item:', 0, 0, 1, self)
                    if item:
                        player.perform(actions.act_pick_up_item, player, item[0])
            return False

    def command_use_item(self, player, item):
        """ Command method to use item - chooses usage behavior based on item properties """
        if 'usable' in item.properties:
            # TODO: make items usable on self or on target
            if item.properties['usable'] == 'self':  # if item usable on self
                player.perform(actions.act_use_item, player, item, player)
            elif item.properties['usable'] == 'point':  # if item usable on point
                self.command_target_choose(item.properties['range'], item, self.command_use_item_on_point, player, item)
            elif item.properties['usable'] == 'battle_entity':  # if item usable on battle entity
                self.command_target_choose(item.properties['range'], item, self.command_use_item_on_entity,
                                           player, item, game_logic.BattleEntity)
            elif item.properties['usable'] == 'battle_entity_or_point':  # if item usable on battle entity or point
                self.command_target_choose(item.properties['range'], item, self.command_use_item_on_entity_or_point,
                                           player, item, game_logic.BattleEntity)

    def command_use_item_on_point(self, target, player, item):
        """ Command method to use item on targeted point """
        player.perform(actions.act_use_item, player, item, target)  # use item on target point

    def command_use_item_on_entity(self, target, player, item, ent_type):
        """ Command method to use item on targeted entity """
        x, y = target
        entity = player.location.cells[x][y].is_there_a(ent_type)
        if entity:
            player.perform(actions.act_use_item, player, item, entity)  # use item on target entity

    def command_use_item_on_entity_or_point(self, target, player, item, ent_type):
        """ Command method to use item on targeted entity """
        x, y = target
        entity = player.location.cells[x][y].is_there_a(ent_type)
        if entity:
            player.perform(actions.act_use_item, player, item, entity)  # use item on target entity
        else:
            player.perform(actions.act_use_item, player, item, target)  # use item on target point

    def command_inventory(self, player):
        """ Command method to show inventory menu """
        # show inventory menu
        item = show_menu_inventory(self.win_mgr, player.inventory, 'Inventory:', 0, 0, 1, self)
        if item:
            add_options = []
            item = item[0]
            if isinstance(item, game_logic.ItemRangedWeapon):
                if len(item.ammo) < item.ammo_max:
                    add_options.append('Load')
                if len(item.ammo) > 0:
                    add_options.append('Unload')
            action = show_menu_list(self.win_mgr, ['Use', 'Equip', 'Drop']+add_options,
                                    'What to do with ' + item.name + '?', 0, 0, 1, self)
            if action:
                if action[0] == 'Use':
                    self.command_use_item(player, item)
                elif action[0] == 'Equip':
                    if item:
                        if len(item.equip_slots) > 1:
                            slot = show_menu_list(self.win_mgr, list(item.equip_slots),
                                                  'Select a slot:', 0, 0, True, self)
                            if slot:
                                slot = slot[0]
                        elif len(item.equip_slots) == 1:
                            slot = list(item.equip_slots)[0]
                        else:
                            slot = False
                        if slot:  # if selected - equip item
                            player.perform(actions.act_equip_item, player, item, slot)
                elif action[0] == 'Drop':
                    player.perform(actions.act_drop_item, player, item)
                elif action[0] == 'Load':
                    ammos = [a for a in player.inventory if item.ammo_type in a.categories]
                    if ammos:
                        if len(ammos) == 1:
                            player.perform(actions.act_reload, player, item, ammos[0])
                        else:
                            ammo = show_menu_inventory(self.win_mgr, ammos, 'Select ammunition:', 0, 0, 1, self)
                            if ammo:
                                player.perform(actions.act_reload, player, item, ammo[0])
                    else:
                        game_logic.Game.add_message('No ' + item.ammo_type + ' type ammunition.', 'PLAYER',
                                                    [255, 255, 255])
                elif action[0] == 'Unload':
                    player.perform(actions.act_unload, player, item)

    def command_reload(self, player):
        """ Command method for player wants to reload ranged weapon (in hands)  """
        for item in player.equipment.values():  # iterate through player equipment
            if isinstance(item, game_logic.ItemRangedWeapon):  # check if there is ranged weapon
                if len(item.ammo) < item.ammo_max:  # check if it is loaded
                    # select appropriate ammo items
                    ammos = [a for a in player.inventory if item.ammo_type in a.categories]
                    if ammos:
                        if len(ammos) == 1:
                            player.perform(actions.act_reload, player, item, ammos[0])
                        else:
                            ammo = show_menu_inventory(self.win_mgr, ammos, 'Select ammunition:', 0, 0, 1, self)
                            if ammo:
                                player.perform(actions.act_reload, player, item, ammo[0])
                    else:
                        game_logic.Game.add_message('No ' + item.ammo_type + ' type ammunition.', 'PLAYER',
                                                    [255, 255, 255])
                else:
                    game_logic.Game.add_message(item.name + ' is fully loaded.', 'PLAYER', [255, 255, 255])

    def command_fire_choose(self, player):
        """ Command method for player wants to fire ranged weapon - choose target """
        ranged_weapons = [w for w in list(player.equipment.values()) if
                          isinstance(w, game_logic.ItemRangedWeapon)]  # pick ranged weapons in equipment
        if ranged_weapons:  # check if there are any
            if len(ranged_weapons) == 1:  # if one
                if len(ranged_weapons[0].ammo) > 0:  # if it has ammo loaded
                    self.command_target_choose(ranged_weapons[0].range, ranged_weapons[0],
                                               self.command_fire, player, ranged_weapons[0])
                else:
                    game_logic.Game.add_message(ranged_weapons[0].name + " isn't loaded!",
                                                'PLAYER', [255, 255, 255])
            else:  # if multiple ranged equipped
                weapon = show_menu_list(self.win_mgr, ranged_weapons,
                                        'Fire weapon:', 0, 0, True, self)  # select one
                if weapon:
                    if len(weapon[0].ammo) > 0:  # check if loaded
                        self.command_target_choose(weapon[0].range, weapon[0],
                                                   self.command_fire, player, weapon[0])
                    else:
                        game_logic.Game.add_message(weapon[0].name + " isn't loaded!",
                                                    'PLAYER', [255, 255, 255])
        else:
            game_logic.Game.add_message('Equip ranged weapon to fire.', 'PLAYER', [255, 255, 255])

    def command_fire(self, target, player, weapon):
        """ Command method for player wants to fire ranged weapon - target confirmed, fire """
        tx, ty = target  # target cell coordinates
        target = player.location.cells[tx][ty].is_there_a(game_logic.Fighter)  # TODO: if more monster types - add here
        if target:
            player.perform(actions.act_fire_ranged, player, weapon, target)  # if there are a monster - target him
        else:
            player.perform(actions.act_fire_ranged, player, weapon, (tx, ty))  # if not - target cell

    def command_target_choose(self, range, thing, command_function, *args, **kwargs):
        """ Command method for player wants to select target for some command """
        self.targeting_range = range
        self.targeting_thing = thing
        self.targeting_command = command_function
        self.targeting_args = args
        self.targeting_kwargs = kwargs
        self.game.state = 'targeting'
        self.log.visible = False
        self.cell_info.visible = True

    def command_target_confirmed(self, player):
        """ Command method when target is chosen - execute command """
        tx = player.position[0] + self.map.cam_offset[0]  # target cell coordinates
        ty = player.position[1] + self.map.cam_offset[1]
        self.targeting_command((tx, ty), *self.targeting_args, **self.targeting_kwargs)
    # ===========================================================================================================

    def clear_targeting(self):
        """ Method that clears targeting info and returns window to playing state """
        self.map.cam_offset = (0, 0)  # set camera offset to normal
        self.targeting_range = 0
        self.targeting_command = None
        self.targeting_args = None
        self.targeting_kwargs = None
        self.targeting_thing = None
        self.log.visible = True
        self.cell_info.visible = False
        self.game.state = 'playing'

    def handle_input(self):
        """ Method that translates player input commands to game logic actions and runs them """
        # block for easier naming inside method
        game = self.game
        player = game.player
        loc = game.current_loc
        commands = player_input.get_input(game)  # get list of player commands
        if len(commands) > 0:
            for command in commands:
                if game.state == 'playing':
                    # game exit command
                    if command == 'exit':
                        game.state = 'exit'
                    # moving commands
                    elif command == 'move_n':
                        self.command_default_direction(player, loc, 0, -1)
                    elif command == 'move_s':
                        self.command_default_direction(player, loc, 0, 1)
                    elif command == 'move_w':
                        self.command_default_direction(player, loc, -1, 0)
                    elif command == 'move_e':
                        self.command_default_direction(player, loc, 1, 0)
                    elif command == 'move_nw':
                        self.command_default_direction(player, loc, -1, -1)
                    elif command == 'move_ne':
                        self.command_default_direction(player, loc, 1, -1)
                    elif command == 'move_sw':
                        self.command_default_direction(player, loc, -1, 1)
                    elif command == 'move_se':
                        self.command_default_direction(player, loc, 1, 1)
                    elif command == 'wait1step':  # wait for 1 step
                        player.perform(actions.act_wait, game.player, game.player.speed)
                    # closing door commands
                    elif command == 'close_n':
                        self.command_close_direction(player, loc, 0, -1)
                    elif command == 'close_s':
                        self.command_close_direction(player, loc, 0, 1)
                    elif command == 'close_w':
                        self.command_close_direction(player, loc, -1, 0)
                    elif command == 'close_e':
                        self.command_close_direction(player, loc, 1, 0)
                    elif command == 'close_nw':
                        self.command_close_direction(player, loc, -1, -1)
                    elif command == 'close_ne':
                        self.command_close_direction(player, loc, 1, -1)
                    elif command == 'close_sw':
                        self.command_close_direction(player, loc, -1, 1)
                    elif command == 'close_se':
                        self.command_close_direction(player, loc, 1, 1)
                    # smashin' things commands
                    elif command == 'smash_n':
                        self.command_smash_direction(player, loc, 0, -1)
                    elif command == 'smash_s':
                        self.command_smash_direction(player, loc, 0, 1)
                    elif command == 'smash_w':
                        self.command_smash_direction(player, loc, -1, 0)
                    elif command == 'smash_e':
                        self.command_smash_direction(player, loc, 1, 0)
                    elif command == 'smash_nw':
                        self.command_smash_direction(player, loc, -1, -1)
                    elif command == 'smash_ne':
                        self.command_smash_direction(player, loc, 1, -1)
                    elif command == 'smash_sw':
                        self.command_smash_direction(player, loc, -1, 1)
                    elif command == 'smash_se':
                        self.command_smash_direction(player, loc, 1, 1)
                    # 'look' command
                    elif command == 'look':
                        game.state = 'looking'
                        self.log.visible = False
                        self.cell_info.visible = True
                    # show/hide debug log command
                    elif command == 'debug_log':
                        if game.show_debug_log:
                            game.show_debug_log = False
                        else:
                            game.show_debug_log = True
                    # inventory command
                    elif command == 'inventory':
                        # show inventory menu
                        self.command_inventory(player)
                    # wield (equip) command
                    elif command == 'wield_item':
                        # show list menu with items
                        item = show_menu_list(self.win_mgr, player.inventory, 'Equip item:', 0, 0, True, self)
                        if item:
                            if len(item[0].equip_slots) > 1:
                                slot = show_menu_list(self.win_mgr, list(item[0].equip_slots),
                                                      'Select a slot:', 0, 0, True, self)
                                if slot:
                                    slot = slot[0]
                            elif len(item[0].equip_slots) == 1:
                                slot = list(item[0].equip_slots)[0]
                            else:
                                slot = False
                            if slot:  # if selected - equip item
                                player.perform(actions.act_equip_item, player, item[0], slot)
                    # use command
                    elif command == 'use_item':
                        # show list menu with items
                        item = show_menu_list(self.win_mgr, player.inventory, 'Use item:', 0, 0, True, self)
                        if item:
                            self.command_use_item(player, item[0])
                    # take off item command
                    elif command == 'take_off_item':
                        # show list menu with equipped items
                        item = show_menu_list(self.win_mgr, [sl for sl in list(player.equipment.values()) if sl],
                                              'Take off item:', 0, 0, True, self)
                        if item:  # if selected - take off
                            player.perform(actions.act_unequip_item, player, item[0])
                    # drop item command
                    elif command == 'drop':
                        # show inventory menu
                        item = show_menu_inventory(self.win_mgr, player.inventory, 'Drop item:', 0, 0, 1, self)
                        if item:
                            player.perform(actions.act_drop_item, player, item[0])
                    # pick up from ground command
                    elif command == 'ground':
                        self.command_pick_up(player, loc, 0, 0)
                    # reload ranged weapon (in hands) command
                    elif command == 'reload':
                        self.command_reload(player)
                    # unload ranged weapon (in hands) command
                    elif command == 'unload':
                        for item in player.equipment.values():  # unload every equipped item
                            if isinstance(item, game_logic.ItemRangedWeapon):
                                player.perform(actions.act_unload, player, item)
                    # fire ranged weapon (in hands) command
                    elif command == 'fire':
                        self.command_fire_choose(player)
                elif game.state == 'looking':  # if the game is in 'looking' mode
                    # exit looking mode
                    if command == 'exit':
                        self.map.cam_offset = (0, 0)  # set camera offset to normal
                        self.cell_info.visible = False
                        self.log.visible = True
                        game.state = 'playing'  # resume normal game flow
                    # moving camera commands
                    elif command == 'move_n':
                        self.map.move_camera(0, -1)
                    elif command == 'move_s':
                        self.map.move_camera(0, 1)
                    elif command == 'move_w':
                        self.map.move_camera(-1, 0)
                    elif command == 'move_e':
                        self.map.move_camera(1, 0)
                    elif command == 'move_nw':
                        self.map.move_camera(-1, -1)
                    elif command == 'move_ne':
                        self.map.move_camera(1, -1)
                    elif command == 'move_sw':
                        self.map.move_camera(-1, 1)
                    elif command == 'move_se':
                        self.map.move_camera(1, 1)
                elif game.state == 'targeting':  # if the game is in 'targeting' mode
                    # exit targeting mode
                    if command == 'exit':
                        self.clear_targeting()
                    if command == 'confirm':
                        self.command_target_confirmed(player)
                        self.clear_targeting()
                    # moving camera commands
                    elif command == 'move_n':
                        self.map.move_camera(0, -1)
                    elif command == 'move_s':
                        self.map.move_camera(0, 1)
                    elif command == 'move_w':
                        self.map.move_camera(-1, 0)
                    elif command == 'move_e':
                        self.map.move_camera(1, 0)
                    elif command == 'move_nw':
                        self.map.move_camera(-1, -1)
                    elif command == 'move_ne':
                        self.map.move_camera(1, -1)
                    elif command == 'move_sw':
                        self.map.move_camera(-1, 1)
                    elif command == 'move_se':
                        self.map.move_camera(1, 1)
                elif game.state == 'dead':  # if game is in dead state
                    # game exit command
                    if command == 'exit':
                        game.state = 'exit'
                return True  # if any commands
            else:
                return False  # if not


# TODO: refactor ListMenu and InventoryMenu, to minimize code duplication (make one inherit another)
class WindowInventoryMenu(Window):
    """ Class for simple inventory menu (list of selectable items, on selection performs player_function with item) """

    def __init__(self, options, caption, x=0, y=0, z=0, visible=True, prev_window=None):
        self.options = options  # a list of menu items
        self.x = x
        self.y = y
        width = 0  # width is calculated accordingly to options length
        y = 0
        letter_index = ord('a')  # start menu item indexing from 'a'
        elems = []
        for option in options:
            y += 1
            # add menu items as text line objects
            text_line = str(option)
            if isinstance(option, game_logic.ItemCharges):
                text_line += '[' + str(option.charges) + ']'
            elems.append(ElementTextLine(self, 0, y, chr(letter_index) + ') ' + text_line))
            letter_index += 1
            if len(text_line) > width:
                width = len(text_line)
        width += 3
        if width < len(str(caption)):
            width = len(str(caption))
        self.caption = ElementTextLine(self, 0, 0, caption)
        elems.append(self.caption)  # add menu caption as text line
        width += 1
        self.item_info = ElementItemInfo(owner=self, x=width, y=0, width=20, height=30)  # add item info panel
        elems.append(self.item_info)
        # call parent constructor
        height = len(options) + 1
        if height < self.item_info.height:
            height = self.item_info.height
        super(WindowInventoryMenu, self).__init__(self.x, self.y, width + self.item_info.width, height, z, visible)
        for elem in elems:
            self.add_element(elem)
        self.selected = None  # if no options - selected remains None
        self.selected_index = 0
        if len(self.options) > 0:
            self.selected = self.options[0]  # set selection to first option
            self.selected_index = 0
            self.item_info.item = self.selected
        self.state = 'working'  # set menu state to working
        self.prev_window = prev_window  # previous window
        self.console = tdl.Console(self.width, self.height)

    def draw(self):
        """ Drawing method """
        i = 0
        for element in self.elements:  # blit every element to console
            if isinstance(element, ElementTextLine):
                if i == self.selected_index and self.selected:  # highlight selected element
                    element.bgcolor = [0, 100, 0]
                else:  # if not highligted - set background color to color of menu caption
                    element.bgcolor = self.caption.bgcolor
            self.console.blit(element.draw(), element.x, element.y)
            i += 1
        return self.console

    def handle_input(self):
        """ Input handling method """
        events = player_input.get_raw_input()  # get a raw input from player
        if events:
            for event in events:
                if event.type == 'KEYDOWN':
                    if event.key == 'ESCAPE':
                        self.state = 'cancelled'
                        self.win_mgr.close_window(self)
                    if event.key == 'ENTER':  # if player hits Enter
                        if self.selected:
                            self.state = 'finished'
                            self.win_mgr.close_window(self)
                        else:  # if no options - cancel selection
                            self.state = 'cancelled'
                            self.win_mgr.close_window(self)
                    elif event.key == 'UP' or event.key == 'KP8':  # selection movement
                        if self.selected_index > 0:  # if up - select previous option
                            self.selected_index -= 1
                            self.selected = self.options[self.selected_index]
                            self.item_info.item = self.selected
                        else:  # if attempted to scroll up at top - jump to bottom
                            self.selected_index = len(self.options) - 1
                    elif event.key == 'DOWN' or event.key == 'KP2':
                        if self.selected_index < len(self.options) - 1:  # if down - select next option
                            self.selected_index += 1
                            self.selected = self.options[self.selected_index]
                            self.item_info.item = self.selected
                        else:  # if attempted to scroll down at bottom - jump to top
                            self.selected_index = 0
                    elif event.key == 'CHAR':
                        # convert the ASCII code to an index; if it corresponds to an option, return it
                        index = ord(event.keychar) - ord('a')
                        if 0 <= index < len(self.options):
                            self.selected = self.options[index]
                            self.selected_index = index
                            self.state = 'finished'
                            self.win_mgr.close_window(self)
            return True
        else:
            return False


class WindowListMenu(Window):
    """ Class for simple list menu (list of selectable options) """

    def __init__(self, options, caption, x=0, y=0, z=0, visible=True, prev_window=None):
        self.options = options  # a list of menu options
        self.x = x
        self.y = y
        width = 0  # width is calculated accordingly to options length
        y = 0
        letter_index = ord('a')  # start menu item indexing from 'a'
        elems = []
        for option in options:
            y += 1
            # add menu options as text line objects
            text_line = str(option)
            elems.append(ElementTextLine(self, 0, y, chr(letter_index) + ') ' + text_line))
            letter_index += 1
            if len(text_line) > width:
                width = len(text_line)
        width += 3
        if width < len(str(caption)):
            width = len(str(caption))
        elems.append(ElementTextLine(self, 0, 0, caption))  # add menu caption as text line
        # call parent constructor
        super(WindowListMenu, self).__init__(self.x, self.y, width, len(options) + 1, z, visible)
        for elem in elems:
            self.add_element(elem)
        self.selected = None  # if no options - selected remains None
        self.selected_index = 0
        if len(self.options) > 0:
            self.selected = self.options[0]  # set selection to first option
            self.selected_index = 0
        self.state = 'working'  # set menu state to working
        self.prev_window = prev_window  # previous window
        self.console = tdl.Console(self.width, self.height)

    def draw(self):
        """ Drawing method """
        i = 0
        for element in self.elements:  # blit every element to console
            if i == self.selected_index and self.selected:  # highlight selected element
                element.bgcolor = [0, 100, 0]
            else:  # if not highligted - set background color to color of menu caption
                element.bgcolor = self.elements[-1].bgcolor
            self.console.blit(element.draw(), element.x, element.y)
            i += 1
        return self.console

    def handle_input(self):
        """ Input handling method """
        events = player_input.get_raw_input()  # get a raw input from player
        if events:
            for event in events:
                if event.type == 'KEYDOWN':
                    if event.key == 'ESCAPE':
                        self.state = 'cancelled'
                        self.win_mgr.close_window(self)
                    if event.key == 'ENTER':  # if player hits Enter
                        if self.selected:
                            self.state = 'finished'
                            self.win_mgr.close_window(self)
                        else:  # if no options - cancel selection
                            self.state = 'cancelled'
                            self.win_mgr.close_window(self)
                    elif event.key == 'UP' or event.key == 'KP8':  # selection movement
                        if self.selected_index > 0:  # if up - select previous option
                            self.selected_index -= 1
                            self.selected = self.options[self.selected_index]
                        else:  # if attempted to scroll up at top - jump to bottom
                            self.selected_index = len(self.options) - 1
                    elif event.key == 'DOWN' or event.key == 'KP2':
                        if self.selected_index < len(self.options) - 1:  # if down - select next option
                            self.selected_index += 1
                            self.selected = self.options[self.selected_index]
                        else:  # if attempted to scroll down at bottom - jump to top
                            self.selected_index = 0
                    elif event.key == 'CHAR':
                        # convert the ASCII code to an index; if it corresponds to an option, return it
                        index = ord(event.keychar) - ord('a')
                        if 0 <= index < len(self.options):
                            self.selected = self.options[index]
                            self.selected_index = index
                            self.state = 'finished'
                            self.win_mgr.close_window(self)
            return True
        else:
            return False


class WindowManager:
    """ Class that manages windows """

    def __init__(self, graphics):
        self.windows = []  # windows list
        self.active_window = None  # current active window
        self.graphics = graphics  # a graphics object

    def add_window(self, window):
        """ Window adding method """
        window.win_mgr = self
        self.windows.append(window)

    def close_window(self, window):
        """ Window closing method """
        if window.prev_window and self.active_window == window:
            self.active_window = window.prev_window
            self.windows.remove(window)
        else:
            self.windows.remove(window)  # if no previous - just remove window

    def handle_input(self, commands):
        """ Pass handling input to active window """
        self.active_window.handle_input(commands)


def show_menu_list(win_mgr, options, caption, x_offset=0, y_offset=0, z=1, prev_window=None):
    """ A function to show a list menu, and return result """
    menu = WindowListMenu(options, caption, x_offset, y_offset, z, True, prev_window)  # create a list menu
    menu.x = win_mgr.graphics.screen_width // 2 - menu.width // 2 + x_offset  # place it at center of screen
    menu.y = win_mgr.graphics.screen_height // 2 - menu.height // 2 + y_offset
    win_mgr.add_window(menu)  # add menu to window manager
    win_mgr.active_window = menu
    while menu.state == 'working':  # a loop until menu does it job (or cancelled)
        menu.handle_input()
        win_mgr.graphics.render_all()
    if menu.state == 'cancelled':  # if menu cancelled return false
        return False
    if menu.state == 'finished':  # if option selected - return it
        return menu.selected, menu.selected_index


def show_menu_inventory(win_mgr, options, caption, x_offset=0, y_offset=0, z=1, prev_window=None):
    """ A function to show an inventory menu, and return result """
    menu = WindowInventoryMenu(options, caption, x_offset, y_offset, z, True, prev_window)  # create a list menu
    menu.x = win_mgr.graphics.screen_width // 2 - menu.width // 2 + x_offset  # place it at center of screen
    menu.y = win_mgr.graphics.screen_height // 2 - menu.height // 2 + y_offset
    win_mgr.add_window(menu)  # add menu to window manager
    win_mgr.active_window = menu
    while menu.state == 'working':  # a loop until menu does it job (or cancelled)
        menu.handle_input()
        win_mgr.graphics.render_all()
    if menu.state == 'cancelled':  # if menu cancelled return false
        return False
    if menu.state == 'finished':  # if option selected - return it
        return menu.selected, menu.selected_index

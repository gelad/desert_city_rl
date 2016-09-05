"""
    This file contains user interface. For now uses tdl (maybe need to move all render work to render?)
"""
import tdl
import textwrap

import game_logic
import actions
import player_input


class Element:
    """ Base class for UI element """

    def __init__(self, owner, x=0, y=0, width=0, height=0):
        self.owner = owner  # owner (other element or window)
        self.x = x  # position in window
        self.y = y
        self.width = width  # element width
        self.height = height  # element height
        self.elements = []  # child elements

    def draw(self):
        """ Abstract method, must return element appearance, ready to draw (tdl.Console for now) """
        raise NotImplementedError

    def add_element(self, element):
        """ Method for adding child elements """
        element.owner = self
        self.elements.append(element)


class ElementTextLine(Element):
    """ Simple UI element - line of text """

    def __init__(self, owner, x=0, y=0, line='', color=None, bgcolor=None):
        super(ElementTextLine, self).__init__(owner=owner, x=x, y=y, width=len(line), height=1)
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


class ElementMainPanel(Element):
    """ Main panel with player stats, etc """

    def __init__(self, owner, player, x=0, y=0, width=0, height=0):
        super(ElementMainPanel, self).__init__(owner=owner, x=x, y=y, width=width, height=height)
        self.player = player  # Player object, to obtain player-related info
        self.add_element(ElementTextLine(self, 0, 0, player.name))  # player name on top of panel
        self.player_hp = ElementTextLine(self, 0, 1, str(player.hp) + '/' + str(player.maxhp) + ' HP')  # player hp bar
        self.add_element(self.player_hp)
        # player position (for debug)
        self.player_pos = ElementTextLine(self, 0, 2, 'X:' + str(player.position[0]) + ' Y:' + str(player.position[1]))
        self.add_element(self.player_pos)

    def draw(self):
        """ Drawing method """
        # update player stats in lines
        self.player_hp.set_line(str(self.player.hp) + '/' + str(self.player.maxhp) + ' HP')
        self.player_pos.set_line('X:' + str(self.player.position[0]) + ' Y:' + str(self.player.position[1]))
        console = tdl.Console(self.width, self.height)
        for element in self.elements:  # blit every element to console
            console.blit(element.draw(), element.x, element.y)
        return console


class ElementMap(Element):
    """ Location map element  """

    def __init__(self, owner, loc, player, x=0, y=0, width=0, height=0):
        super(ElementMap, self).__init__(owner=owner, x=x, y=y, width=width, height=height)
        self.loc = loc  # Location object, to obtain location-related info
        self.player = player  # Player object, to obtain player-related info
        self.cam_offset = (0, 0)  # camera offset (if at (0, 0) - centered on player)

    def move_camera(self, dx, dy):
        """ Method for moving camera by dx, dy """
        self.cam_offset = (self.cam_offset[0] + dx, self.cam_offset[1] + dy)

    @staticmethod
    def cell_graphics(x, y, cell, loc, visible):
        """ Method that returns graphic representation of tile. Must be reworked when tileset comes in """
        char = ' '
        color = [255, 255, 255]
        bgcolor = [0, 0, 0]
        if visible:  # check if cell is visible
            if cell.tile == 'SAND':  # sand tile type
                char = '.'
                color = [200, 200, 0]
                bgcolor = [100, 100, 0]
            for ent in cell.entities:  # iterate through list of entities,if there are any, display them instead of tile
                char = ent.char
                color = [255, 255, 255]
                if ent.occupies_tile:  # check if there is entity, occupying tile - display it on top
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

    def __init__(self, owner, game, x=0, y=0, width=0, height=0):
        super(ElementLog, self).__init__(owner=owner, x=x, y=y, height=height, width=width)
        self.game = game  # game object to obtain log level

    def draw(self):
        """ Drawing method """
        console = tdl.Console(self.height, self.width)
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
        self.cam_offset = (0, 0)  # camera offset (for looking, shooting, etc)
        self.console = tdl.Console(width, height)  # offscreen console of window

    def draw(self):
        """ Window drawing method """
        self.console.clear()
        for element in self.elements:  # blit every element to console
            self.console.blit(element.draw(), element.x, element.y)
        return self.console

    # ========================== COMMAND METHODS (special cases, to prevent code duplication) ====================
    def command_default_direction(self, player, loc, dx, dy):
        """ Command method for player pressed direction key - move/open/attack/use default action for each type
            of object in desired cell
        """
        player_x = player.position[0]
        player_y = player.position[1]
        new_x = player_x + dx
        new_y = player_y + dy
        if loc.is_in_boundaries(new_x, new_y):  # check if new position is in the location boundaries
            if loc.cells[new_x][new_y].is_movement_allowed():  # check if movement is allowed
                player.perform(actions.act_move, self.game.player, dx, dy)  # perform move action
            door = loc.cells[new_x][new_y].is_there_a(game_logic.Door)
            if door:  # check if there is a door
                if door.is_closed:  # check if it is closed
                    player.perform(actions.act_open_door, self.game.player, door)  # open door
            # TODO: here must be more complicated check - if target is hostile, etc
            enemy = loc.cells[new_x][new_y].is_there_a(game_logic.Fighter)
            if enemy:  # check if there an enemy
                player.perform(actions.act_attack_melee, self.game.player, enemy)  # attack it in melee

    def command_close_direction(self, player, loc, dx, dy):
        """ Command method for player wants to close door in some direction  """
        door_x = player.position[0] + dx
        door_y = player.position[1] + dy
        if loc.is_in_boundaries(door_x, door_y):  # check if position of selected cell is in boundaries
            door = loc.cells[door_x][door_y].is_there_a(game_logic.Door)
            if door:  # check if there is a door
                if not door.is_closed:  # check if it is closed
                    player.perform(actions.act_close_door, self.game.player, door)  # close door
                    return True
            return False

    # ===========================================================================================================

    def handle_input(self):
        """ Method that translates player input commands to game logic actions and runs them """
        # block for easier naming inside method
        game = self.game
        player = game.player
        loc = game.current_loc
        commands = player_input.get_input(game)  # get list of player commands
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
                # 'look' command
                elif command == 'look':
                    game.state = 'looking'
                # show/hide debug log command
                elif command == 'debug_log':
                    if game.show_debug_log:
                        game.show_debug_log = False
                    else:
                        game.show_debug_log = True
                # inventory command
                elif command == 'inventory':
                    # show inventory menu and make it active
                    inv_menu = WindowInventoryMenu(['one', 'two', 'three'], 'Inventory:', 0, 0, 1, True, self)
                    inv_menu.x = self.width // 2 - inv_menu.width // 2  # place it at center of screen
                    inv_menu.y = self.height // 2 - inv_menu.height // 2
                    self.win_mgr.add_window(inv_menu)
                    self.win_mgr.active_window = inv_menu
            elif game.state == 'looking':  # if the game is in 'looking' mode
                # exit looking mode
                if command == 'exit':
                    self.map.cam_offset = (0, 0)  # set camera offset to normal
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


class WindowInventoryMenu(Window):
    """ Class for simple menu (list of selectable items) """

    # TODO: rework menus
    def __init__(self, options, caption, x=0, y=0, z=0, visible=True, prev_window=None):
        self.options = options  # a list of menu items
        width = 0
        y = 0
        letter_index = ord('a')  # start menu item indexing from 'a'
        elems = []
        for option in options:
            y += 1
            # add menu items as text line objects
            elems.append(ElementTextLine(self, 0, y, chr(letter_index) + ') ' + str(option)))
            letter_index += 1
            if len(str(option)) > width:
                width = len(option)
        width += 3
        if width < len(caption):
            width = len(caption)
        elems.append(ElementTextLine(self, 0, 0, caption))  # add menu caption as text line
        super(WindowInventoryMenu, self).__init__(x, y, width, len(options) + 1, z, visible)  # call parent constructor
        for elem in elems:
            self.add_element(elem)
        self.selected = self.options[0]  # set selection to first item
        self.state = 'working'  # set menu state to working
        self.prev_window = prev_window  # previous window
        self.console = tdl.Console(self.width, self.height)

    def draw(self):
        """ Drawing method """
        for element in self.elements:  # blit every element to console
            self.console.blit(element.draw(), element.x, element.y)
        return self.console

    def handle_input(self):
        """ Input handling method """
        events = player_input.get_raw_input()  # get a raw input from player
        for event in events:
            if event.type == 'KEYDOWN':
                if event.key == 'ESCAPE':
                    self.state = 'cancelled'
                    self.win_mgr.close_window(self)
                elif event.key == 'CHAR':
                    # convert the ASCII code to an index; if it corresponds to an option, return it
                    index = ord(event.keychar) - ord('a')
                    if 0 <= index < len(self.options):
                        self.selected = self.options[index]
                        # Here must be an action with an item
                        print(self.selected)
                        self.win_mgr.close_window(self)


class WindowManager:
    """ Class that manages windows """

    def __init__(self):
        self.windows = []  # windows list
        self.active_window = None  # current active window

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
            raise Exception(
                "Attempted to close active window with no previous. Change active window first.",
                str(type(self.active_window)))

    def handle_input(self, commands):
        """ Pass handling input to active window """
        self.active_window.handle_input(commands)

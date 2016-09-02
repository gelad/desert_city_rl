import tdl
import fov_los
import game_logic

import textwrap


class Graphics:
    """
        Class that performs all graphic-related work.
    """

    def __init__(self, renderer='TDL', screen_width=110, screen_height=50, map_width=80, map_height=50, fps_limit=60):
        if renderer == 'TDL':
            self.renderer = renderer  # renderer type
            self.screen_width = screen_width  # screen width in tiles
            self.screen_height = screen_height  # screen height in tiles
            self.map_width = map_width  # map width in tiles
            self.map_height = map_height  # map height in tiles
            self.panel_width = self.screen_width - self.map_width  # panel width in tiles
            self.panel_height = self.screen_height  # panel height in tiles
            self.log_width = self.panel_width  # message log width
            self.log_height = self.panel_height // 2 - 1  # message log height
            self.fps_limit = fps_limit  # FPS limit
            self.cam_offset = (0, 0)  # camera offset (for looking, shooting, etc)
            # TDL initialization block
            tdl.set_font('consolas_unicode_16x16.png', greyscale=True)
            self.console = tdl.init(screen_width, screen_height, title="Desert City")  # main console, displayed
            self.map_console = tdl.Console(map_width, map_height)  # offscreen map console
            self.panel = tdl.Console(self.panel_width, self.panel_height)  # offscreen panel console
            self.log = tdl.Console(self.log_width, self.log_height)  # offscreen message log console
            tdl.set_fps(fps_limit)  # set fps limit

    def move_camera(self, dx, dy):
        """ Method for moving camera by dx, dy """
        self.cam_offset = (self.cam_offset[0] + dx, self.cam_offset[1] + dy)

    def set_camera_offset(self, x, y):
        """ Method for setting camera offset """
        self.cam_offset = (x, y)

    # TODO: make some data structure storing tileset (simply a TYPE - CHAR - COLOR for start)
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

    def render_all(self, loc, player, game):
        """ Method that displays all to screen """
        if self.renderer == 'TDL':
            # map rendering
            player_x = player.position[0]
            player_y = player.position[1]
            # player on-screen coords
            player_scr_x = self.map_width // 2 - self.cam_offset[0]
            player_scr_y = self.map_height // 2 - self.cam_offset[1]
            for x in range(0, self.map_width):  # iterate through every x, y in map_console
                for y in range(0, self.map_height):
                    rel_x = x - player_scr_x + player_x  # game location coordinates in accordance to screen coordinates
                    rel_y = y - player_scr_y + player_y
                    # checks if location coordinates are valid (in boundaries)
                    if loc.is_in_boundaries(rel_x, rel_y):
                        # obtain cell graphics
                        cg = self.cell_graphics(rel_x, rel_y, loc.cells[rel_x][rel_y], loc,
                                                player.is_in_fov(rel_x, rel_y))
                        self.map_console.draw_char(x, y, cg[0], cg[1], cg[2])  # draw it on map_console
                    else:
                        self.map_console.draw_char(x, y, ' ')  # if out of bounds then draw blank space
                    if not self.cam_offset == (0, 0):
                        # if camera is not centered on player - draw there a red 'X'
                        self.map_console.draw_char(self.map_width // 2, self.map_height // 2, 'X', [255, 0, 0])
            self.console.blit(self.map_console)  # blit map_console on main console
            # TODO: move rendering each element to separate function.
            # right panel rendering
            self.panel.clear()
            self.panel.draw_str(0, 0, game.player.name)
            self.panel.draw_str(0, 1, str(game.player.hp)+'/'+str(game.player.maxhp)+' HP')
            self.panel.draw_str(0, 2, game.state)
            self.panel.draw_str(0, 3, 'X:'+str(player_x)+' Y:'+str(player_y))
            self.panel.draw_str(0, 4, 'Current time: '+str(game.time_system.current_time()))
            self.console.blit(self.panel, self.map_width, 0)
            # message log rendering
            self.log.clear()  # clear log window
            # get log messages, intended to be shown to player
            msgs = [m for m in game_logic.Game.log if m[1] == 'PLAYER']
            msgs = msgs[-self.log_height:]  # make a slice for last ones log_height ammount
            log_lines = []
            for msg in msgs:  # iterate through messages
                for line in textwrap.wrap(msg[0], self.log_width):  # wrap them in lines of log_width
                    log_lines.append((line, msg[2]))  # store them in list
            log_lines = log_lines[-(self.log_height-1):]  # slice list to log_height elements
            y = 0
            for line in log_lines:
                y += 1
                self.log.draw_str(0, y, line[0], line[1])  # draw each line
            self.console.blit(self.log, self.map_width, self.panel_height / 2)
            tdl.flush()  # draw main console

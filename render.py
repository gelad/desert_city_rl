import tdl

import fov_los
import game_logic
import ui

import textwrap


class Graphics:
    """
        Class that performs all graphic-related work.
    """

    def __init__(self, game, renderer='TDL', screen_width=110, screen_height=50, map_width=80, map_height=50,
                 fps_limit=60):
        if renderer == 'TDL':
            self.renderer = renderer  # renderer type
            self.fps_limit = fps_limit  # FPS limit
            self.screen_width = screen_width  # screen width in tiles
            self.screen_height = screen_height  # screen height in tiles
            # window stuff
            self.win_mgr = ui.WindowManager()  # windows manager
            main_window = ui.WindowMain(game, 0, 0, screen_width, screen_height, 0, map_width, map_height)
            self.win_mgr.windows.append(main_window)  # add main window to WinMgr
            self.win_mgr.active_window = main_window  # make it active
            # TDL initialization block
            tdl.set_font('consolas_unicode_16x16.png', greyscale=True)
            self.console = tdl.Console(screen_width, screen_height)  # console on which windows blit
            tdl.set_fps(fps_limit)  # set fps limit

    def render_all(self, loc, player, game):
        """ Method that displays all to screen """
        if self.renderer == 'TDL':
            # window rendering
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
            if game.show_debug_log:
                msgs = [m for m in game_logic.Game.log if m[1] == 'DEBUG']
            else:
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

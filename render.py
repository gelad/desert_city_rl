import tdl
import fov_los


class Graphics:
    """
        Class that performs all graphic-related work.
    """

    def __init__(self, renderer='TDL', screen_width=80, screen_height=65, map_width=80, map_height=50, fps_limit=60):
        if renderer == 'TDL':
            self.renderer = renderer
            self.screen_width = screen_width  # screen width in tiles
            self.screen_height = screen_height  # screen height in tiles
            self.map_width = map_width  # map width in tiles
            self.map_height = map_height  # map height in tiles
            self.panel_width = self.screen_width  # panel width in tiles
            self.panel_height = self.screen_height - self.map_height  # panel height in tiles
            self.fps_limit = fps_limit  # FPS limit
            # TDL initialization block
            tdl.set_font('consolas_unicode_16x16.png', greyscale=True)
            self.console = tdl.init(screen_width, screen_height, title="Desert City")  # main console, displayed
            self.map_console = tdl.Console(map_width, map_height)  # offscreen map console
            self.panel = tdl.Console(map_width, map_height)
            tdl.set_fps(fps_limit)

    # TODO: make some data structure storing tileset (simply a TYPE - CHAR - COLOR for start)
    @staticmethod
    def cell_graphics(x, y, cell, loc, visible):
        """ Method that returns graphic representation of tile. Must be reworked when tileset comes in """
        char = ' '
        color = [255, 255, 255]
        bgcolor = [0, 0, 0]
        if visible:
            if cell.tile == 'SAND':  # sand tile type
                char = '.'
                color = [150, 150, 0]
                bgcolor = [60, 60, 20]
            for ent in cell.entities:  # iterate through list of entities,if there are any, display them instead of tile
                char = ent.char
                color = [255, 255, 255]
                if ent.occupies_tile:
                    break
            loc.out_of_sight_map[(x, y)] = [char, color, bgcolor]
            return [char, color, bgcolor]
        elif cell.explored:
            prev_seen_cg = loc.out_of_sight_map[(x, y)]
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
            camera_x = self.map_width // 2  # camera (viewport) is centered by default at center of map part of window
            camera_y = self.map_height // 2  # there is player @ too
            for x in range(0, self.map_width):  # iterate through every x, y in map_console
                for y in range(0, self.map_height):
                    rel_x = x - camera_x + player_x  # game location coordinates in accordance to screen coordinates
                    rel_y = y - camera_y + player_y
                    # checks if location coordinates are valid (in boundaries)
                    if loc.is_in_boundaries(rel_x, rel_y):
                        # obtain cell graphics
                        cg = self.cell_graphics(rel_x, rel_y, loc.cells[rel_x][rel_y], loc,
                                                player.is_in_fov(rel_x, rel_y))
                        self.map_console.draw_char(x, y, cg[0], cg[1], cg[2])  # draw it on map_console
                    else:
                        self.map_console.draw_char(x, y, ' ')  # if out of bounds then draw blank space
            self.console.blit(self.map_console)  # blit map_console on main console
            # bottom panel rendering
            self.panel.clear()
            self.panel.draw_str(0, 0, game.state)
            self.panel.draw_str(0, 1, str(player_x) + ':' + str(player_y))
            self.panel.draw_str(0, 2, 'Current time: ' + str(game.time_system.current_time()))
            self.console.blit(self.panel, 0, self.map_height)
            tdl.flush()  # draw main console

import tdl


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
            self.fps_limit = fps_limit  # FPS limit
            # TDL initialization block
            tdl.set_font('consolas_unicode_16x16.png', greyscale=True)
            self.console = tdl.init(screen_width, screen_height, title="Desert City")  # main console, displayed
            self.map_console = tdl.Console(map_width, map_height)  # offscreen map console
            tdl.set_fps(fps_limit)

    # TODO: make some data structure storing tileset (simply a TYPE - CHAR - COLOR for start)
    @staticmethod
    def cell_graphics(cell):
        """ Method that returns graphic representation of tile. Must be reworked when tileset comes in """
        char = ' '
        color = [255, 255, 255]
        bgcolor = [0, 0, 0]
        if cell.type == 'SAND':  # sand tile type
            char = '.'
            color = [150, 150, 0]
            bgcolor = [60, 60, 20]
        for ent in cell.entities:  # iterate through list of entities, if there are any, display them instead of tile
            if ent.occupies_tile:
                return ent.char, [255, 255, 255], bgcolor  # TODO: Need to implement non-blocking entities visibility
        return char, color, bgcolor

    def render_all(self, loc, player):
        """ Method that displays all to screen """
        if self.renderer == 'TDL':
            player_x = player.position[0]
            player_y = player.position[1]
            camera_x = self.map_width // 2  # camera (viewport) is centered by default at center of map part of window
            camera_y = self.map_height // 2  # there is player @ too
            for x in range(0, self.map_width):  # iterate through every x, y in map_console
                for y in range(0, self.map_height):
                    rel_x = x - camera_x + player_x  # game location coordinates in accordance to screen coordinates
                    rel_y = y - camera_y + player_y
                    # checks if location coordinates are valid (in boundaries)
                    if (rel_x >= 0) and (rel_y >= 0) and (rel_x < loc.width) and (rel_y < loc.height):
                        cg = self.cell_graphics(loc.cells[rel_x][rel_y])  # obtain cell graphics
                        self.map_console.draw_char(x, y, cg[0], cg[1], cg[2])  # draw it on map_console
                    else:
                        self.map_console.draw_char(x, y, ' ')  # if out of bounds then draw blank space
            self.console.blit(self.map_console)  # blit map_console on main console
            tdl.flush()  # draw main console

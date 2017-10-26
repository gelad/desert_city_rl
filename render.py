import clubsandwich

import ui


class Graphics:
    """
        Class that performs all graphic-related work.
    """

    def __init__(self, renderer='TDL', screen_width=110, screen_height=50, fps_limit=60):
        if renderer == 'TDL':
            self.renderer = renderer  # renderer type
            self.fps_limit = fps_limit  # FPS limit
            self.screen_width = screen_width  # screen width in tiles
            self.screen_height = screen_height  # screen height in tiles
            # TDL initialization block
            tdl.set_font('data/fonts/consolasb_full_unicode_16x16.png', greyscale=True)
            self.console = tdl.init(screen_width, screen_height, title="Desert City")  # main console, displayed
            tdl.set_fps(fps_limit)  # set fps limit
            # window stuff
            self.win_mgr = ui.WindowManager(self)  # windows manager

    def render_all(self):
        """ Method that displays all to screen """
        if self.renderer == 'TDL':
            self.win_mgr.windows.sort(key=lambda win: win.z)  # sort in z order
            for window in self.win_mgr.windows:
                if window.visible:
                    self.console.blit(window.draw(), window.x, window.y)
            tdl.flush()  # draw main console

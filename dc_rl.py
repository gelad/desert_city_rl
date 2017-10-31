import game_view
import dataset

import jsonpickle


def player_death():
    """ Function that is called if player is dead """
    # show window with death recap, that returns to main menu
    chosen = ui.show_menu_text_above(win_mgr=game_view.win_mgr, caption='You died!',
                                     options=['Return to main menu', 'Exit'], keys=None,
                                     texts='Horrors of the Desert City got you.',
                                     prev_window=game_view.win_mgr.active_window,
                                     width=40,
                                     text_height=2)
    if chosen[0] == 'Return to main menu':
        to_menu = True
    else:
        to_menu = False
    return to_menu

# HERE PROGRAM RUN STARTS
dataset.initialize()
settings_file = open('data/settings.json')  # open settings file
settings = jsonpickle.loads(settings_file.read())  # load settings
settings_file.close()
loop = game_view.GameLoop()
loop.run()


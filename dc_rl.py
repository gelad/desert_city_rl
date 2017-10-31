import game_view
import dataset

import os

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

back_to_menu = False
current_game = None
while back_to_menu:
    game_view.win_mgr.active_window = None  # TODO: maybe make a method for clearing graphics?
    game_view.win_mgr.windows.clear()
    game_view.console.clear()
    if current_game:
        del current_game
    current_game = main_menu()
    back_to_menu = main_loop()
    if current_game.player.state == 'dead':
        try:
            os.remove('savegame')
        except FileNotFoundError:
            pass
    else:
        save_game(current_game)



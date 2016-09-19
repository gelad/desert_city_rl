import render
import game_logic
import events
import dataset

import pickle
import os


# =========================== global functions, save/load, loop, etc =================================
def save_game(game):
    """ Game saving function """
    # save game object instance, and observers
    pickle.dump((game, events.Observer._observers), open('savegame', 'wb'))


def load_game():
    """ Game loading function """
    try:
        # load game object instance, and observers
        loaded_game, events.Observer._observers = pickle.load(open('savegame', 'rb'))
        if loaded_game.state == 'exit':
            print('Saved game state was exit, changed to playing')  # debug output
            loaded_game.state = 'playing'
        return loaded_game, events.Observer._observers
    except FileNotFoundError:
        return False


def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        draw_screen = False
        if game.state == 'playing':  # check if state is 'playing'
            if game.is_waiting_input:  # check if game is waiting for player input
                graphics.win_mgr.active_window.handle_input()  # let active window handle them
                draw_screen = True  # set flag to draw screen
                if not game.player.state == 'ready':  # if after command execution player is performing an action
                    game.is_waiting_input = False  # set waiting for input flag to False
            else:  # if not waiting for input
                game.time_system.pass_time()  # pass game time, fire events
                game.current_loc.reap()  # if there are dead after tick - call their death() methods
                if game.player.state == 'dead':  # check if player is dead
                    game.state = 'dead'  # set game state to dead
                    game.is_waiting_input = True  # set waiting for input flag True
                for actor in game.current_loc.actors:  # iterate through actors
                    if actor.state == 'ready' and actor.ai:  # pick those who have ai and ready to act
                        actor.ai.act()  # make them act
                if game.player.state == 'ready':  # check if player is 'ready'
                    game.is_waiting_input = True  # set waiting for input flag True
        elif game.state == 'looking' or game.state == 'targeting':  # check if state is 'looking' or 'targeting'
            if game.is_waiting_input:
                graphics.win_mgr.active_window.handle_input()  # let active window handle them
                draw_screen = True  # set flag to draw scree4n
            else:
                pass
        elif game.state == 'dead':
            if game.is_waiting_input:
                graphics.win_mgr.active_window.handle_input()  # let active window handle them
                draw_screen = True  # set flag to draw screen
            else:
                pass
        if draw_screen:
            graphics.render_all()  # call a screen rendering function


dataset.initialize()
loaded = load_game()
if not loaded:
    game = game_logic.Game()
else:
    game = loaded[0]
    events.Observer._observers = loaded[1]
graphics = render.Graphics(game)
main_loop()
if game.player.state == 'dead':
    try:
        os.remove('savegame')
    except FileNotFoundError:
        pass
else:
    save_game(game)


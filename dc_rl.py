import player_input
import render
import game_logic

import pickle


# =========================== global functions, save/load, loop, etc =================================
def save_game(game):
    """ Game saving function """
    pickle.dump(game, open('savegame', 'wb'))


def load_game():
    """ Game loading function """
    try:
        loaded_game = pickle.load(open('savegame', 'rb'))
        if loaded_game.state == 'exit':
            print('Saved game state was exit, changed to playing')  # debug output
            loaded_game.state = 'playing'
        return loaded_game
    except FileNotFoundError:
        return False


def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        draw_screen = False
        if game.state == 'playing':  # check if state is 'playing'
            if game.is_waiting_input:  # check if game is waiting for player input
                commands = player_input.get_input(game)  # get list of player commands
                if commands:  # if there are commands
                    graphics.win_mgr.active_window.handle_input(commands)  # let active window handle them
                draw_screen = True  # set flag to draw screen
                if not game.player.state == 'ready':  # if after command execution player is performing an action
                    game.is_waiting_input = False  # set waiting for input flag to False
            else:  # if not waiting for input
                game.time_system.pass_time()  # pass game time, fire events
                if game.player.state == 'dead':  # check if player is dead
                    game.state = 'dead'  # set game state to 'dead' # PLACEHOLDER FOR NOW!
                    draw_screen = True
                for actor in game.current_loc.actors:  # iterate through actors
                    if actor.state == 'ready' and actor.ai:  # pick those who have ai and ready to act
                        actor.ai.act()  # make them act
                if game.player.state == 'ready':  # check if player is 'ready'
                    game.is_waiting_input = True  # set waiting for input flag True
        elif game.state == 'looking':  # check if state is 'looking'
            if game.is_waiting_input:
                commands = player_input.get_input(game)  # get list of player commands
                if commands:  # if there are commands
                    graphics.win_mgr.active_window.handle_input(commands)  # let active window handle them
                draw_screen = True  # set flag to draw screen
            else:
                pass
        if draw_screen:
            graphics.render_all()  # call a screen rendering function


game = load_game()
if not game:
    game = game_logic.Game()
graphics = render.Graphics(game)
main_loop()
if not game.player.state == 'dead':
    save_game(game)

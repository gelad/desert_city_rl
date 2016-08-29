import player_input
import render
import actions
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
            loaded_game.state = 'playing'
        return loaded_game
    except FileNotFoundError:
        return False


def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        # TODO: TEST how time works!
        commands = player_input.handle_input(game)  # get list of player commands
        if game.state == 'playing':
            game.time_system.pass_time()
        if game.player.state == 'ready':
            game.state = 'waiting_input'
        for command in commands:
            if command == 'exit':
                save_game(game)  # save game before exit
                return
            elif command == 'move_n':
                game.player.perform(actions.act_move, game.player, game.current_loc, 0, -1)
            elif command == 'move_s':
                game.player.perform(actions.act_move, game.player, game.current_loc, 0, 1)
            elif command == 'move_w':
                game.player.perform(actions.act_move, game.player, game.current_loc, -1, 0)
            elif command == 'move_e':
                game.player.perform(actions.act_move, game.player, game.current_loc, 1, 0)
            elif command == 'move_nw':
                game.player.perform(actions.act_move, game.player, game.current_loc, -1, -1)
            elif command == 'move_ne':
                game.player.perform(actions.act_move, game.player, game.current_loc, 1, -1)
            elif command == 'move_sw':
                game.player.perform(actions.act_move, game.player, game.current_loc, -1, 1)
            elif command == 'move_se':
                game.player.perform(actions.act_move, game.player, game.current_loc, 1, 1)
            elif command == 'close_n':
                game.player.close(0, -1)
            elif command == 'close_s':
                game.player.close(0, 1)
            elif command == 'close_w':
                game.player.close(-1, 0)
            elif command == 'close_e':
                game.player.close(1, 0)
            elif command == 'close_nw':
                game.player.close(-1, -1)
            elif command == 'close_ne':
                game.player.close(1, -1)
            elif command == 'close_sw':
                game.player.close(-1, 1)
            elif command == 'close_se':
                game.player.close(1, 1)
            game.state = 'playing'
        if not game.state == 'playing':
            graphics.render_all(game.current_loc, game.player, game)  # call a screen rendering function

graphics = render.Graphics()
game = load_game()
if not game:
    game = game_logic.Game()
main_loop()

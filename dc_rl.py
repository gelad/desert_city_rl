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


def execute_player_commands(game, commands):
    """ Function that translates player input commands to game logic actions and runs them """
    # block for easier naming inside function
    player = game.player
    if player.position:
        player_x = game.player.position[0]
        player_y = game.player.position[1]
    loc = game.current_loc
    for command in commands:
        if command == 'exit':
            save_game(game)  # save game before exit
            game.state = 'exit'
        elif command == 'move_n':
            command_default_direction(player, loc, 0, -1)
        elif command == 'move_s':
            command_default_direction(player, loc, 0, 1)
        elif command == 'move_w':
            command_default_direction(player, loc, -1, 0)
        elif command == 'move_e':
            command_default_direction(player, loc, 1, 0)
        elif command == 'move_nw':
            command_default_direction(player, loc, -1, -1)
        elif command == 'move_ne':
            command_default_direction(player, loc, 1, -1)
        elif command == 'move_sw':
            command_default_direction(player, loc, -1, 1)
        elif command == 'move_se':
            command_default_direction(player, loc, 1, 1)
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


# ========================== COMMAND FUNCTIONS (special cases, to prevent code duplication) ====================
def command_default_direction(player, loc, dx, dy):
    """ Command function for player pressed direction key - move/open/attack/use default action for each type
        of object in desired cell
    """
    player_x = player.position[0]
    player_y = player.position[1]
    new_x = player_x + dx
    new_y = player_y + dy
    if loc.is_in_boundaries(new_x, new_y):  # check if new position is in the location boundaries
        if loc.cells[new_x][new_y].is_movement_allowed():  # if movement is allowed - perform move action
            player.perform(actions.act_move, game.player, game.current_loc, dx, dy)
            return True
        door = loc.cells[new_x][new_y].is_there_a(game_logic.Door)
        if door:  # check if there is a door
            if door.is_closed:  # check if it is closed
                player.perform(actions.act_open_door, game.player, door)  # open door
                return True
        return False


# ==============================================================================================================
def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        # TODO: TEST how time works!
        game.state = 'playing'
        if game.player.state == 'ready':  # TODO: menu implementation will need rework on game state handling
            game.state = 'waiting_input'  # if player is ready to act, stop time and wait for input
            commands = player_input.handle_input(game)  # get list of player commands
            execute_player_commands(game, commands)
        if game.state == 'playing':  # pass time
            game.time_system.pass_time()
        if not game.state == 'playing':
            graphics.render_all(game.current_loc, game.player, game)  # call a screen rendering function

graphics = render.Graphics()
game = load_game()
if not game:
    game = game_logic.Game()
main_loop()

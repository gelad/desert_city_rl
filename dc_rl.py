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
        if game.state == 'waiting_input':
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
                command_close_direction(player, loc, 0, -1)
            elif command == 'close_s':
                command_close_direction(player, loc, 0, 1)
            elif command == 'close_w':
                command_close_direction(player, loc, -1, 0)
            elif command == 'close_e':
                command_close_direction(player, loc, 1, 0)
            elif command == 'close_nw':
                command_close_direction(player, loc, -1, -1)
            elif command == 'close_ne':
                command_close_direction(player, loc, 1, -1)
            elif command == 'close_sw':
                command_close_direction(player, loc, -1, 1)
            elif command == 'close_se':
                command_close_direction(player, loc, 1, 1)
            elif command == 'look':  # 'look' command
                game.state = 'looking'
        elif game.state == 'looking':
            if command == 'exit':
                game.state = 'playing'


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
        if loc.cells[new_x][new_y].is_movement_allowed():  # check if movement is allowed
            player.perform(actions.act_move, game.player, dx, dy)  # perform move action
            return True
        door = loc.cells[new_x][new_y].is_there_a(game_logic.Door)
        if door:  # check if there is a door
            if door.is_closed:  # check if it is closed
                player.perform(actions.act_open_door, game.player, door)  # open door
                return True
        return False


def command_close_direction(player, loc, dx, dy):
    """ Command function for player wants to close door in some direction  """
    door_x = player.position[0] + dx
    door_y = player.position[1] + dy
    if loc.is_in_boundaries(door_x, door_y):  # check if position of selected cell is in boundaries
        door = loc.cells[door_x][door_y].is_there_a(game_logic.Door)
        if door:  # check if there is a door
            if not door.is_closed:  # check if it is closed
                player.perform(actions.act_close_door, game.player, door)  # close door
                return True
        return False


# ==============================================================================================================
def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        if game.state == 'looking':
            commands = player_input.handle_input(game)  # get list of player commands
            execute_player_commands(game, commands)
        game.state = 'playing'
        if game.player.state == 'ready' and game.state == 'playing':
            # TODO: menu implementation will need rework on game state handling
            # Make wait for input a sort of a flag, it occures in different states
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

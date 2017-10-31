""" This module contains "commands" - functions that make "game-logic" actions in accord with player input """
import actions
import game_logic


def command_default_direction(game, dx, dy):
    """ Command for player pressed direction key - move/open/attack/use default action for each type
        of object in desired cell
    """
    game.is_waiting_input = False
    player = game.player
    loc = game.current_loc
    player_x = player.position[0]
    player_y = player.position[1]
    new_x = player_x + dx
    new_y = player_y + dy
    if loc.is_in_boundaries(new_x, new_y):  # check if new position is in the location boundaries
        if loc.cells[new_x][new_y].is_movement_allowed():  # check if movement is allowed
            player.perform(actions.act_move, player, dx, dy)  # perform move action
        door = loc.cells[new_x][new_y].is_there_a(game_logic.Door)
        if door:  # check if there is a door
            if door.is_closed:  # check if it is closed
                player.perform(actions.act_open_door, player, door)  # open door
        # TODO: here must be more complicated check - if target is hostile, etc
        enemy = loc.cells[new_x][new_y].is_there_a(game_logic.Fighter)
        if enemy:  # check if there an enemy
            if player.equipment['LEFT_HAND'] or player.equipment['RIGHT_HAND']:
                player.perform(actions.act_attack_melee_weapons, player, enemy)  # attack it in melee with weapon
            else:
                player.perform(actions.act_attack_melee_basic, player, enemy)  # attack it in melee with hands
    else:  # TODO: PLACEHOLDER - moving to another level
        pass
        # if not leave:
        #     return
        # if leave[1] == 1:  # if yes - leave location
        #     self.command_leave_loc()
    game_logic.main_loop(game)

""" This module contains "commands" - functions that make "game-logic" actions in accord with player input """
import actions
import game_logic
import game_view

from clubsandwich.ui import LayoutOptions


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


def command_pick_up(director, game, dx, dy):
    """ Command function for player wants to pick up some items  """
    player = game.player
    loc = game.current_loc
    x = player.position[0] + dx
    y = player.position[1] + dy
    if loc.is_in_boundaries(x, y):  # check if position of selected cell is in boundaries
        items = [i for i in loc.cells[x][y].entities if isinstance(i, game_logic.Item)]  # select items in cell
        if items:  # check if there is an item
            if len(items) == 1:
                player.perform(actions.act_pick_up_item, player, items[0])
            else:  # if there are multiple Items - ask which to pick up?
                director.push_scene(game_view.PickUpItemSelectionScene(items=items,
                                                                       game=game,
                                                                       caption='Pick up item:',
                                                                       layout_options=LayoutOptions(
                                                                            top=0.25, bottom=0.25,
                                                                            left=0.2, right=0.2)))


def command_use_item(game, item):
    """ Command method to use item - chooses usage behavior based on item properties """
    player = game.player
    if 'usable' in item.properties:
        # TODO: make items usable on self or on target
        if item.properties['usable'] == 'self':  # if item usable on self
            player.perform(actions.act_use_item, player, item, player)
        elif item.properties['usable'] == 'point':  # if item usable on point
            pass
            #self.command_target_choose(item.properties['range'], item, self.command_use_item_on_point, player, item)
        elif item.properties['usable'] == 'battle_entity':  # if item usable on battle entity
            pass
            #command_target_choose(item.properties['range'], item, self.command_use_item_on_entity,
            #                            player, item, game_logic.BattleEntity)
        elif item.properties['usable'] == 'battle_entity_or_point':  # if item usable on battle entity or point
            pass
            #self.command_target_choose(item.properties['range'], item, self.command_use_item_on_entity_or_point,
            #                            player, item, game_logic.BattleEntity)

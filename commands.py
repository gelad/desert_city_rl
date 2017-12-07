""" This module contains "commands" - functions that make "game-logic" actions in accord with player input """
import actions
import game_logic
import game_view
import generation
import save_load

from messages import _  # translation function

import random
import threading
import sys

from clubsandwich.ui import LayoutOptions
from bearlibterminal import terminal


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
        enemy = loc.cells[new_x][new_y].is_there_a(game_logic.Fighter)
        if enemy:  # check if there an enemy
            if player.equipment['LEFT_HAND'] or player.equipment['RIGHT_HAND']:
                player.perform(actions.act_attack_melee_weapons, player, enemy)  # attack it in melee with weapon
            else:
                player.perform(actions.act_attack_melee_basic, player, enemy)  # attack it in melee with hands
    else:  # if desired cell is out of bounds - ask player if he wants to leave this location
        command_ask_leave_loc(game)


def command_close_direction(player, dx, dy):
        """ Command function for player wants to close door in some direction  """
        loc = player.location
        door_x = player.position[0] + dx
        door_y = player.position[1] + dy
        if loc.is_in_boundaries(door_x, door_y):  # check if position of selected cell is in boundaries
            door = loc.cells[door_x][door_y].is_there_a(game_logic.Door)
            if door:  # check if there is a door
                if not door.is_closed:  # check if it is closed
                    player.perform(actions.act_close_door, player, door)  # close door


def command_smash_direction(player, dx, dy):
        """ Command function for player wants to smash something in some direction  """
        loc = player.location
        be_x = player.position[0] + dx  # battle entity estimated position
        be_y = player.position[1] + dy
        if loc.is_in_boundaries(be_x, be_y):  # check if position of selected cell is in boundaries
            be = loc.cells[be_x][be_y].is_there_a(game_logic.BattleEntity)
            if be:  # check if there is a BattleEntity
                if player.equipment['LEFT_HAND'] or player.equipment['RIGHT_HAND']:
                    player.perform(actions.act_attack_melee_weapons, player, be)  # attack it in melee with weapon
                else:
                    player.perform(actions.act_attack_melee_basic, player, be)  # attack it in melee with hands


def command_pick_up(game, dx, dy):
    """ Command function for player wants to pick up some items  """
    director = game_view.GameLoop.active_director
    player = game.player
    loc = game.current_loc
    x = player.position[0] + dx
    y = player.position[1] + dy
    if loc.is_in_boundaries(x, y):  # check if position of selected cell is in boundaries
        items = [i for i in loc.cells[x][y].entities if isinstance(i, game_logic.Item)]  # select items in cell
        if items:  # check if there is an item
            if len(items) == 1:
                if isinstance(items[0], game_logic.ItemCharges) and\
                        'stackable' in items[0].categories and items[0].charges > 1:
                    director.push_scene(game_view.NumberInputScene(
                        num_range=(1, items[0].charges),
                        num_start=items[0].charges,
                        title=str(items[0]),
                        callback=lambda text, item=items[0], game=game: _split_stack_and_pick(text, item, game)))
                else:
                    player.perform(actions.act_pick_up_item, player, items[0])
            else:  # if there are multiple Items - ask which to pick up?
                director.push_scene(game_view.PickUpItemSelectionScene(items=items,
                                                                       game=game,
                                                                       caption=_('Pick up item:'),
                                                                       layout_options=LayoutOptions(
                                                                            top=0.25, bottom=0.25,
                                                                            left=0.2, right=0.2)))


def _split_stack_and_pick(text, item, game):
    """
    Method to split items stack and pick up
    :param text: accepts string, because NumberInput returns string 
    :return: None
    """
    director = game_view.GameLoop.active_director
    try:  # check if text can be converted to int
        split_num = int(text)
    except ValueError:
        director.pop_scene()
        return
    split_item = item.split(split_num)
    game.player.perform(actions.act_pick_up_item, game.player, split_item)
    director.pop_scene()


def command_use_item(game, item, main_scene):
    """ Command function to use item - chooses usage behavior based on item properties """
    player = game.player
    if 'usable' in item.properties:
        if item.properties['usable'] == 'self':  # if item usable on self
            player.perform(actions.act_use_item, player, item, player)
            game.start_update_thread()
        elif item.properties['usable'] == 'point':  # if item usable on point
            main_scene.start_targeting(range=item.properties['range'],
                                       t_object=item,
                                       eligible_types=['point'],
                                       callback=command_use_item,
                                       player=player,
                                       item=item)
        elif item.properties['usable'] == 'battle_entity':  # if item usable on battle entity
            main_scene.start_targeting(range=item.properties['range'],
                                       t_object=item,
                                       eligible_types=[game_logic.BattleEntity],
                                       callback=command_use_item_on_target,
                                       player=player,
                                       item=item)
        elif item.properties['usable'] == 'battle_entity_or_point':  # if item usable on battle entity or point
            main_scene.start_targeting(range=item.properties['range'],
                                       t_object=item,
                                       eligible_types=[game_logic.BattleEntity, 'point'],
                                       callback=command_use_item_on_target,
                                       player=player,
                                       item=item)


def command_use_item_on_target(target, player, item):
    """ Command function to use item on targeted point or entity """
    player.perform(actions.act_use_item, player, item, target)


def command_throw_choose(game, main_scene):
        """ Command function for player wants to throw an item in hands - choose target """
        right = game.player.equipment['RIGHT_HAND']
        left = game.player.equipment['LEFT_HAND']
        items = [i for i in [right, left] if i is not None]  # pick equipment in hands
        if items:  # check if there are any
            if len(items) == 1:  # if one
                if game.player.get_throw_range(items[0]) > 0:
                    main_scene.start_targeting(range=game.player.get_throw_range(items[0]),
                                               t_object=items[0],
                                               eligible_types=(game_logic.BattleEntity, 'point'),
                                               callback=command_throw,
                                               player=game.player,
                                               item=items[0])
                else:
                    game_logic.Game.add_message(message=
                                                _('{item} is too heavy!'.format(item=str(items[0])).capitalize()),
                                                level='PLAYER', color=[255, 255, 255])
            else:  # if multiple items in hands
                main_scene.director.push_scene(game_view.ThrowItemSelectionScene(items=items,
                                                                                 game=game,
                                                                                 caption=_('Throw item:'),
                                                                                 layout_options=LayoutOptions(
                                                                                   top=0.30, bottom=0.30,
                                                                                   left=0.30, right=0.30)))
        else:
            game_logic.Game.add_message(message=_('Take something in hand to throw it.'),
                                        level='PLAYER', color=[255, 255, 255])


def command_throw(target, player, item):
    """ Command function for player wants to throw item """
    player.perform(actions.act_throw, player, item, target)


def command_reload_equipped(game):
    """ Command function for player wants to reload ranged weapon (in hands)  """
    for item in game.player.equipment.values():  # iterate through player equipment
        if isinstance(item, game_logic.ItemRangedWeapon):  # check if there is ranged weapon
            command_reload(game=game, item=item)


def command_reload(game, item):
    """ Command function for player wants to reload specific ranged weapon """
    director = game_view.GameLoop.active_director
    if isinstance(item, game_logic.ItemRangedWeapon):  # check if there is ranged weapon
        if len(item.ammo) < item.ammo_max:  # check if it is loaded
            # select appropriate ammo items
            ammos = [a for a in game.player.inventory if item.ammo_type in a.categories]
            if ammos:
                if len(ammos) == 1:
                    game.player.perform(actions.act_reload, game.player, item, ammos[0])
                    game.start_update_thread()
                else:
                    director.push_scene(game_view.AmmoItemSelectionScene(items=ammos,
                                                                         game=game,
                                                                         ranged_weapon=item,
                                                                         caption=_('Load ammo:'),
                                                                         layout_options=LayoutOptions(
                                                                             top=0.30, bottom=0.30,
                                                                             left=0.30,
                                                                             right=0.30)))
            else:
                game_logic.Game.add_message(message=
                    _('No {ammo_type} type ammunition.').format(ammo_type=_(item.ammo_type)).capitalize(),
                                            level='PLAYER',
                                            color=[255, 255, 255])
        else:
            game_logic.Game.add_message(message=
                _('{item} is fully loaded.').format(item=str(item)).capitalize(),
                                        level='PLAYER', color=[255, 255, 255])


def command_fire_choose(game):
    """ Command function for player wants to fire ranged weapon - choose target """
    director = game_view.GameLoop.active_director
    ranged_weapons = [w for w in list(game.player.equipment.values()) if
                      isinstance(w, game_logic.ItemRangedWeapon)]  # pick ranged weapons in equipment
    if ranged_weapons:  # check if there are any
        if len(ranged_weapons) == 1:  # if one
            if len(ranged_weapons[0].ammo) > 0:  # if it has ammo loaded
                director.main_game_scene.start_targeting(range=ranged_weapons[0].range,
                                                         t_object=ranged_weapons[0],
                                                         eligible_types=(game_logic.BattleEntity, 'point'),
                                                         callback=command_fire,
                                                         player=game.player,
                                                         weapon=ranged_weapons[0])
            else:
                game_logic.Game.add_message(message=
                                        _("{weapon} isn't loaded!").format(weapon=str(ranged_weapons[0]).capitalize()),
                                            level='PLAYER', color=[255, 255, 255])
        else:  # if multiple ranged equipped
            director.push_scene(game_view.FireItemSelectionScene(items=ranged_weapons,
                                                                 game=game,
                                                                 caption=_('Fire weapon:'),
                                                                 layout_options=LayoutOptions(
                                                                     top=0.30, bottom=0.30,
                                                                     left=0.30, right=0.30)))
    else:
        game_logic.Game.add_message(message=_('Equip ranged weapon to fire.'),
                                    level='PLAYER', color=[255, 255, 255])


def command_fire(target, player, weapon):
    """ Command function for player wants to fire fanged item """
    player.perform(actions.act_fire_ranged, player, weapon, target)


def command_player_dead(game):
    """ Command that is excutes if player dies """
    game_logic.Game.log.clear()
    director = game_view.GameLoop.active_director
    director.game = None
    del game
    director.push_scene(game_view.SingleButtonMessageScene(message=_('Horrors of the Desert City got you.'),
                                                           title=_('You are dead.'),
                                                           button_text=_('Return to main menu'),
                                                           callback=
                                                           lambda: command_return_to_main_menu(),
                                                           layout_options='intrinsic'))


def command_return_to_main_menu():
    """ Command that returns to main menu, closing all scenes
        Actually, runs game anew
    """
    director = game_view.GameLoop.active_director
    director.pop_to_first_scene()
    director.pop_scene(may_exit=False)
    terminal.clear()
    director.main_game_scene = None
    director.push_scene(game_view.MainMenuScene())


def command_execute_debug_line(line, game):
    """ Executes single debug command line """
    # unsafe, but will do for now
    director = game_view.GameLoop.active_director
    player = game.player
    loc = game.current_loc
    if game.player.position:
        x = game.player.position[0]
        y = game.player.position[1]
    try:
        exec(line, globals(), locals())
    except:
        game_logic.Game.add_message(message=_('Failed to execute line: {line}').format(line=line).capitalize(),
                                    level='DEBUG', color=[255, 0, 0])
        e = sys.exc_info()[0]
        print('WARNING! Failed to execute debug line: ' + line + '\n' + str(e))


def command_ask_leave_loc(game):
    """
    Function that prompts player before actually leaving location
    :param game: a Game object
    """
    director = game_view.GameLoop.active_director
    flee = False
    text = _('Do you really want to leave this location?')
    for point in game_logic.circle_points(r=25, include_center=False):  # check for an enemy near player
        x = point[0] + game.player.position[0]
        y = point[1] + game.player.position[1]
        if game.current_loc.is_in_boundaries(x, y):
            if game.current_loc.cells[x][y].is_there_a(game_logic.Fighter):
                flee = True  # if there are an enemy - set flee flag on
                text += _('\n[color=red]WARNING: There are enemies nearby! If you choose to leave now, you will be chased, and probably lose some items while fleeing.')
                break
    director.push_scene(game_view.MultiButtonMessageScene(buttons=[(_('Yes, head back to the camp.'), text,
                                                            lambda g=game, f=flee: command_leave_loc(game=g, flee=f)),
                                                                   (_('No, stay here.'), text, None)],
                                                          title=_('Leaving location'),
                                                          layout_options='intrinsic'))


def command_leave_loc(game, flee=False):
    """
    Function to execute when player wants to leave location
    :param game: a Game object
    :param flee: flee flag - if fleeing, some penalties take place
    """
    director = game_view.GameLoop.active_director
    old_loc = game.current_loc
    player = game.player
    raid_report_text = ''
    # fleeing report section
    if flee:  # check if player is fleeing from enemies
        lost_items = []
        for item in player.inventory:
            if game_logic.weighted_choice([(True, 50), (False, 50)]):  # lose some inventory items
                lost_items.append(item)
                player.discard_item(item=item)
        for item in [sl for sl in list(player.equipment.values()) if sl]:  # lose some equipped items
            if game_logic.weighted_choice([(True, 25), (False, 75)]):
                lost_items.append(item)
                player.unequip_item(item=item)
                player.discard_item(item=item)
        if len(lost_items) > 0:
            raid_report_text += _('You fled from the enemies, but lost some items in the process:\n')
            for item in lost_items:
                raid_report_text += _('{item}, ').format(item=str(item))
                del item
            raid_report_text = raid_report_text[:-2] + '.\n'  # a hack, replace last , with .\n
        else:
            raid_report_text += _('You fled from the enemies and kept all of your items. Lucky!\n')
    # treasures report section
    treasures = {}
    for item in player.inventory:
        if 'relic' in item.categories:  # if there'll be other types of treasure - add here
            if isinstance(item, game_logic.ItemCharges):
                count = item.charges
            else:
                count = 1
            if item.name in treasures:
                treasures[str(item)][0] += count
            else:
                treasures[str(item)] = [count, item.properties['value']]
    if len(treasures) > 0:
        raid_report_text += _('You obtained some treasures:\n\n')
        total = 0
        for tr in treasures.keys():
            raid_report_text += _('{tr_name} x{tr_count} * {tr_value} = {tr_total}\n').format(
                tr_name=tr,
                tr_count=str(treasures[tr][0]),
                tr_value=str(treasures[tr][1]),
                tr_total=str(treasures[tr][0] * treasures[tr][1]))
            total += treasures[tr][0] * treasures[tr][1]
        raid_report_text += _('\nTotal treasures value: {total} coins.\n ').format(total=str(total))
    else:
        raid_report_text += _('You escaped the City with nothing of value in your pockets. At least you managed to stay alive.\n')
    # actual leaving location section
    # TODO: location transition needs testing (eliminate leftovers, don't lose anything)
    player.location.remove_entity(player)
    player.effects.clear()  # simply clear list for now. Needs testing
    game.remove_location(old_loc)
    game.enter_camp()
    game.equipment_merchant.restock()
    director.pop_scene()
    director.push_scene(game_view.SingleButtonMessageScene(message=raid_report_text + '\n \n ',
                                                           title=_('Successful raid.'),
                                                           layout_options='intrinsic', close_on_esc=False,
                                                           callback=lambda: (director.pop_scene(),
                                                                             director.push_scene(game_view.CampMenuScene
                                                                                 (game=game)))))


def command_enter_loc(game, new_loc):
    """
    :param game: a Game object
    :param new_loc: Location object, to which transfer the player
    """
    game.current_loc = new_loc
    game.add_location(game.current_loc)
    game_logic.Game.clear_log()
    start_x, start_y = 0, 0
    for i in range(100):  # look for acceptable random position
        x = random.randrange(new_loc.width // 4, new_loc.width // 4 * 3)
        y = random.randrange(new_loc.height // 4, new_loc.height // 4 * 3)
        if new_loc.cells[x][y].is_movement_allowed:
            enemies_near = False
            for point in game_logic.circle_points(r=20, include_center=False):  # check for an enemy near player
                p_x = point[0] + x
                p_y = point[1] + y
                if game.current_loc.cells[p_x][p_y].is_there_a(game_logic.Fighter):
                    enemies_near = True
                    break
            if not enemies_near:
                start_x, start_y = x, y
                break
    game.current_loc.place_entity(game.player, start_x, start_y)
    game.current_loc.actors.remove(game.player)  # A hack, to make player act first if acting in one tick
    game.current_loc.actors.insert(0, game.player)



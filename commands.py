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
                                       eligible_types=('point'),
                                       callback=command_use_item,
                                       player=player,
                                       item=item)
        elif item.properties['usable'] == 'battle_entity':  # if item usable on battle entity
            main_scene.start_targeting(range=item.properties['range'],
                                       t_object=item,
                                       eligible_types=(game_logic.BattleEntity),
                                       callback=command_use_item_on_target,
                                       player=player,
                                       item=item)
        elif item.properties['usable'] == 'battle_entity_or_point':  # if item usable on battle entity or point
            main_scene.start_targeting(range=item.properties['range'],
                                       t_object=item,
                                       eligible_types=(game_logic.BattleEntity, 'point'),
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
                    game_logic.Game.add_message(items[0].name.capitalize() + ' is too heavy!',
                                                'PLAYER', [255, 255, 255])
            else:  # if multiple items in hands
                main_scene.director.push_scene(game_view.ThrowItemSelectionScene(items=items,
                                                                                 game=game,
                                                                                 caption='Throw item:',
                                                                                 layout_options=LayoutOptions(
                                                                                   top=0.30, bottom=0.30,
                                                                                   left=0.30, right=0.30)))
        else:
            game_logic.Game.add_message('Take something in hand to throw it.', 'PLAYER', [255, 255, 255])


def command_throw(target, player, item):
    """ Command function for player wants to throw item """
    player.perform(actions.act_throw, player, item, target)


def command_reload_equipped(director, game):
        """ Command function for player wants to reload ranged weapon (in hands)  """
        for item in game.player.equipment.values():  # iterate through player equipment
            if isinstance(item, game_logic.ItemRangedWeapon):  # check if there is ranged weapon
                command_reload(director=director, game=game, item=item)


def command_reload(director, game, item):
    """ Command function for player wants to reload specific ranged weapon """
    if isinstance(item, game_logic.ItemRangedWeapon):  # check if there is ranged weapon
        if len(item.ammo) < item.ammo_max:  # check if it is loaded
            # select appropriate ammo items
            ammos = [a for a in game.player.inventory if item.ammo_type in a.categories]
            if ammos:
                if len(ammos) == 1:
                    game.player.perform(actions.act_reload, game.player, item, ammos[0])
                else:
                    director.push_scene(game_view.AmmoItemSelectionScene(items=ammos,
                                                                         game=game,
                                                                         ranged_weapon=item,
                                                                         caption='Load ammo:',
                                                                         layout_options=LayoutOptions(
                                                                             top=0.30, bottom=0.30,
                                                                             left=0.30,
                                                                             right=0.30)))
            else:
                game_logic.Game.add_message('No ' + item.ammo_type + ' type ammunition.', 'PLAYER',
                                            [255, 255, 255])
        else:
            game_logic.Game.add_message(item.name + ' is fully loaded.', 'PLAYER', [255, 255, 255])


def command_fire_choose(director, game):
        """ Command function for player wants to fire ranged weapon - choose target """
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
                    game_logic.Game.add_message(ranged_weapons[0].name + " isn't loaded!",
                                                'PLAYER', [255, 255, 255])
            else:  # if multiple ranged equipped
                director.push_scene(game_view.FireItemSelectionScene(items=ranged_weapons,
                                                                     game=game,
                                                                     caption='Fire weapon:',
                                                                     layout_options=LayoutOptions(
                                                                        top=0.30, bottom=0.30,
                                                                        left=0.30, right=0.30)))
        else:
            game_logic.Game.add_message('Equip ranged weapon to fire.', 'PLAYER', [255, 255, 255])


def command_fire(target, player, weapon):
    """ Command function for player wants to fire fanged item """
    player.perform(actions.act_fire_ranged, player, weapon, target)


def command_execute_debug_line(line, game, director):
    """ Executes single debug command line """
    # unsafe, but will do for now
    player = game.player
    loc = game.current_loc
    x = game.player.position[0]
    y = game.player.position[1]
    try:
        eval(line, globals(), locals())
    except:
        game_logic.Game.add_message('Failed to execute line: ' + line, 'DEBUG', [255, 0, 0])
        print('WARNING! Failed to execute debug line: ' + line)


# def command_leave_loc(self):
#         """ PLACEHOLDER method for moving to another loc """
#
#         old_loc = self.game.current_loc
#         # show after level score - sold treasures for now
#         treasures = {}
#         for item in self.game.player.inventory:
#             if 'relic' in item.categories:  # if there'll be other types of treasure - add here
#                 if isinstance(item, game_logic.ItemCharges):
#                     count = item.charges
#                 else:
#                     count = 1
#                 if item.name in treasures:
#                     treasures[item.name][0] += count
#                 else:
#                     treasures[item.name] = [count, item.properties['value']]
#                 self.game.player.discard_item(item)
#                 del item
#         if len(treasures) > 0:
#             text = 'You escaped the City alive, and obtained some treasures:\n\n'
#             total = 0
#             for tr in treasures.keys():
#                 text += tr + ' x' + str(treasures[tr][0]) + ' * ' + str(treasures[tr][1]) + ' = ' \
#                         + str(treasures[tr][0] * treasures[tr][1]) + '\n'
#                 total += treasures[tr][0] * treasures[tr][1]
#             text += '\nTotal treasures value: ' + str(total) + ' coins.'
#             self.game.player.properties['money'] += total
#         else:
#             text = 'You escaped the City alive, but with nothing of value in your pockets.\n\n'
#         show_menu_text_above(win_mgr=self.win_mgr, caption='Successiful raid into ruins of Neth-Nikakh.',
#                              options=['Ok.'], keys=None, texts=text, prev_window=self, width=self.width // 3 * 2,
#                              text_height=25)
#         self.game.current_loc = generation.generate_loc('ruins', None, 200, 200)
#         self.game.add_location(self.game.current_loc)
#         self.game.player.location.remove_entity(self.game.player)
#         self.game.current_loc.place_entity(self.game.player, 0, 0)
#         self.game.current_loc.actors.remove(self.game.player)  # A hack, to make player act first if acting in one tick
#         self.game.current_loc.actors.insert(0, self.game.player)
#         self.game.remove_location(old_loc)


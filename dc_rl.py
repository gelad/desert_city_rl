import render
import ui
import game_logic
import events
import dataset

import pickle

import os
import time
import gc
import zlib

# TODO: load settings from file
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 50
MAP_HEIGHT = 50


# =========================== global functions, save/load, loop, etc =================================
def save_game(game):
    """ Game saving function """
    gc.collect()  # run garbage collect - remove weakref object without references and so on
    # save game object instance, and observers
    uncompressed = pickle.dumps(game)
    compressed = zlib.compress(uncompressed)
    open('savegame', 'wb').write(compressed)


def load_game():
    """ Game loading function """
    try:
        # load game object instance, and observers
        compressed = open('savegame', 'rb').read()
        uncompressed = zlib.decompress(compressed)
        loaded_game = pickle.loads(uncompressed)
        loaded_game.locations_reobserve()
        if loaded_game.state == 'exit':
            print('Saved game state was exit, changed to playing')  # debug output
            loaded_game.state = 'playing'
        return loaded_game
    except FileNotFoundError:
        return False


def main_loop():
    """ Main game loop function """
    draw_screen = True  # draw screen at first run
    last_frame_time = time.time()
    while not game.state == 'exit':
        if game.state == 'playing':  # check if state is 'playing'
            if game.is_waiting_input:  # check if game is waiting for player input
                if graphics.win_mgr.active_window.handle_input():  # let active window handle input
                    draw_screen = True  # if any input - set flag to draw screen
                if not game.player.state == 'ready':  # if after command execution player is performing an action
                    game.is_waiting_input = False  # set waiting for input flag to False
            else:  # if not waiting for input
                game.time_system.pass_time()  # pass game time, fire events
                game.current_loc.reap()  # if there are dead after tick - call their death() methods
                if game.player.state == 'dead':  # check if player is dead
                    game.state = 'dead'  # set game state to dead
                    game.is_waiting_input = True  # set waiting for input flag True
                    draw_screen = True  # set flag to draw screen
                for actor in game.current_loc.actors:  # iterate through actors
                    if actor.state == 'ready' and actor.ai:  # pick those who have ai and ready to act
                        actor.ai.act()  # make them act
                if game.player.state == 'ready':  # check if player is 'ready'
                    game.is_waiting_input = True  # set waiting for input flag True
                    draw_screen = True  # set flag to draw screen
        elif game.state == 'looking' or game.state == 'targeting':  # check if state is 'looking' or 'targeting'
            if game.is_waiting_input:
                if graphics.win_mgr.active_window.handle_input():  # let active window handle input
                    draw_screen = True  # if any input - set flag to draw screen
            else:
                pass
        elif game.state == 'dead':
            if game.is_waiting_input:
                if graphics.win_mgr.active_window.handle_input():  # let active window handle input
                    draw_screen = True  # if any input - set flag to draw screen
            else:
                pass
        if draw_screen:
            graphics.render_all()  # call a screen rendering function
        draw_screen = False
        # dealing with high CPU load
        current_time = time.time()
        # 1000 is a magic number, game runs smooth, but not eat 1 core of CPU completely
        sleep_time = 1. / 1000 - (current_time - last_frame_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        last_frame_time = current_time

# HERE PROGRAM RUN STARTS
dataset.initialize()
graphics = render.Graphics(screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT)
main_menu_options = []
loaded = load_game()  # try to load game
if loaded:
    main_menu_options.append('Continue')
main_menu_options.append('New Game')
main_menu_options.append('Exit')
main_menu_choice = ui.show_menu_list(win_mgr=graphics.win_mgr, caption='Welcome to ancient city of Neth-Nikakh!',
                                     options=main_menu_options)
if not main_menu_choice:
    exit()
if main_menu_choice[0] == 'Continue':
    game = loaded  # load saved game
elif main_menu_choice[0] == 'New Game':
    class_choice = ui.show_menu_text(win_mgr=graphics.win_mgr, caption='Choose your character background:',
                                     options=['Adventurer', 'Warrior', 'Gantra mercenary', 'Magic seeker'],
                                     keys='alphabet', text_width=40, text_height=30,
                                     texts=['Many adventurers are lured to the City - in search of treasures, power,' +
                                            ' glory or something else. You are among the others - jack of all trades,' +
                                            ' master of nothing.'
                                            ,
                                            'Mighty warriors visit Neth-Nikakh to prove their strength by fighting' +
                                            ' horrors, created by dark magic. Treasures are also nice bonus. You are ' +
                                            'such warrior, proficient in melee combat and wearing a set of armor.'
                                            ,
                                            'Mercenaries from distant Northern country called Gantra are well-known ' +
                                            'as trustworthy soldiers. One of them - with your sturdy crossbow' +
                                            ' and shooting skills - you headed south, to obtain treasures of mysterious'
                                            + ' City.'
                                            ,
                                            'A talent to use magic is rare among the people of Vaerthol. ' +
                                            'You lack one, but unlike others, you desperately crave ' +
                                            'for magic. One man told you a rumor, that in the sands lies a magic city' +
                                            ' of Neth-Nikakh, where among the other wonders, ordinary people can' +
                                            ' become powerful ' +
                                            'mages. So, you packed your spellbooks (useless for non-mage, of course)' +
                                            ', scrolls (not-so-useless), and headed South, to finally obtain desired' +
                                            ' magic gift.'])
    game = game_logic.Game()  # start a new game
    # TODO: need to make some templates for different starting classes (in dataset?)
    if not class_choice:  # if nothing selected (esc hit)
        quit()
    if class_choice[0] == 'Adventurer':
        game.player.add_item(game.current_loc.place_entity('item_short_bow', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_bronze_tipped_arrow', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_dagger', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_firebolt_scroll', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_antidote_potion', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_healing_potion', 10, 10))
    elif class_choice[0] == 'Warrior':
        game.player.add_item(game.current_loc.place_entity('item_sabre', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_mail_armor', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_misurka', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_antidote_potion', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_healing_potion', 10, 10))
    elif class_choice[0] == 'Gantra mercenary':
        game.player.add_item(game.current_loc.place_entity('item_hunting_crossbow', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_bronze_bolt', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_dagger', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_antidote_potion', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_healing_potion', 10, 10))
    elif class_choice[0] == 'Magic seeker':
        game.player.add_item(game.current_loc.place_entity('item_dagger', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_firebolt_scroll', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_frostbolt_scroll', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_antidote_potion', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_healing_potion', 10, 10))
        game.player.add_item(game.current_loc.place_entity('item_haste_potion', 10, 10))
elif main_menu_choice[0] == 'Exit':
    exit()
main_window = ui.WindowMain(game, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, MAP_WIDTH, MAP_HEIGHT)
graphics.win_mgr.add_window(main_window)  # add main window to WinMgr
graphics.win_mgr.active_window = main_window  # make it active
main_loop()
if game.player.state == 'dead':
    try:
        os.remove('savegame')
    except FileNotFoundError:
        pass
else:
    save_game(game)


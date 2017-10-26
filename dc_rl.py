import game_view
import game_logic
import dataset
import save_load

import pickle
import os
import time
import gc
import zlib

import jsonpickle


def main_menu():
    main_menu_options = []
    loaded = load_game()  # try to load game
    if loaded:
        main_menu_options.append('Continue')
    main_menu_options.append('New Game')
    main_menu_options.append('Exit')
    main_menu_choice = ui.show_menu_list(win_mgr=game_view.win_mgr, caption='Welcome to ancient city of Neth-Nikakh!',
                                         options=main_menu_options)
    if not main_menu_choice:
        exit()
    if main_menu_choice[0] == 'Continue':
        game = loaded  # load saved game
    elif main_menu_choice[0] == 'New Game':
        # TODO: move texts to files
        class_choice = ui.show_menu_text(win_mgr=game_view.win_mgr, caption='Choose your character background:',
                                         options=['Adventurer', 'Warrior', 'Gantra mercenary', 'Magic seeker'],
                                         keys='alphabet', text_width=40, text_height=30,
                                         texts=[
                                             'Many adventurers are lured to the City - in search of treasures, power,' +
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
        if not class_choice:  # if nothing selected (esc hit)
            quit()
        sg_file = open('data/starting_gear.json', 'r')  # load starting gear
        sg_dict = jsonpickle.loads(sg_file.read())
        for item_id in sg_dict[class_choice[0]]:
            game.player.add_item(item_id)
        sg_file.close()
    elif main_menu_choice[0] == 'Exit':
        exit()
    main_window = ui.WindowMain(game, 0, 0, settings['screen_width'], settings['screen_height'],
                                0, settings['map_width'], settings['map_height'])
    game_view.win_mgr.add_window(main_window)  # add main window to WinMgr
    game_view.win_mgr.active_window = main_window  # make it active
    return game


def player_death():
    """ Function that is called if player is dead """
    # show window with death recap, that returns to main menu
    chosen = ui.show_menu_text_above(win_mgr=game_view.win_mgr, caption='You died!',
                                     options=['Return to main menu', 'Exit'], keys=None,
                                     texts='Horrors of the Desert City got you.',
                                     prev_window=game_view.win_mgr.active_window,
                                     width=40,
                                     text_height=2)
    if chosen[0] == 'Return to main menu':
        to_menu = True
    else:
        to_menu = False
    return to_menu


def main_loop():
    """ Main game loop function """
    global current_game
    game = current_game
    to_menu = False  # 'return to main menu on game end' flag
    draw_screen = True  # draw screen at first run
    last_frame_time = time.time()
    while not game.state == 'exit':
        if game.state == 'playing':  # check if state is 'playing'
            if game.is_waiting_input:  # check if game is waiting for player input
                if game_view.win_mgr.active_window.handle_input():  # let active window handle input
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
                    to_menu = player_death()
                    break
                for actor in game.current_loc.actors:  # iterate through actors
                    if actor.state == 'ready' and actor.ai:  # pick those who have ai and ready to act
                        actor.ai.act()  # make them act
                if game.player.state == 'ready':  # check if player is 'ready'
                    game.is_waiting_input = True  # set waiting for input flag True
                    draw_screen = True  # set flag to draw screen
        elif game.state == 'looking' or game.state == 'targeting':  # check if state is 'looking' or 'targeting'
            if game.is_waiting_input:
                if game_view.win_mgr.active_window.handle_input():  # let active window handle input
                    draw_screen = True  # if any input - set flag to draw screen
            else:
                pass
        elif game.state == 'dead':
            if game.is_waiting_input:
                if game_view.win_mgr.active_window.handle_input():  # let active window handle input
                    draw_screen = True  # if any input - set flag to draw screen
            else:
                pass
        if draw_screen:
            game_view.render_all()  # call a screen rendering function
        draw_screen = False
        # dealing with high CPU load
        current_time = time.time()
        # 1000 is a magic number, game runs smooth, but not eat 1 core of CPU completely
        sleep_time = 1. / 1000 - (current_time - last_frame_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        last_frame_time = current_time
    return to_menu

# HERE PROGRAM RUN STARTS
dataset.initialize()
settings_file = open('data/settings.json')  # open settings file
settings = jsonpickle.loads(settings_file.read())  # load settings
settings_file.close()
loop = game_view.GameLoop()
loop.run()

back_to_menu = False
current_game = None
while back_to_menu:
    game_view.win_mgr.active_window = None  # TODO: maybe make a method for clearing graphics?
    game_view.win_mgr.windows.clear()
    game_view.console.clear()
    if current_game:
        del current_game
    current_game = main_menu()
    back_to_menu = main_loop()
    if current_game.player.state == 'dead':
        try:
            os.remove('savegame')
        except FileNotFoundError:
            pass
    else:
        save_game(current_game)



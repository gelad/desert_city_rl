"""
    Player input handling.
"""

import tdl


INPUT_ENGINE = 'TDL'


def get_input(game):
    """ Function returns list of player input (not keypresses, but desired actions) """
    if INPUT_ENGINE == 'TDL':
        user_input = tdl.event.get()  # get input from TDL
        player_input = []
        # translate TDL input to game logic player actions
        for event in user_input:
            if event.type == 'KEYDOWN':
                if event.key == 'ESCAPE':  # exiting the game
                    player_input.append('exit')
                if event.key == 'ENTER':  # confirm some action (targeting, etc)
                    player_input.append('confirm')
                elif event.key == 'UP' or event.key == 'KP8':  # movement
                    player_input.append('move_n')
                elif event.key == 'DOWN' or event.key == 'KP2':
                    player_input.append('move_s')
                elif event.key == 'LEFT' or event.key == 'KP4':
                    player_input.append('move_w')
                elif event.key == 'RIGHT' or event.key == 'KP6':
                    player_input.append('move_e')
                elif event.key == 'KP7':
                    player_input.append('move_nw')
                elif event.key == 'KP9':
                    player_input.append('move_ne')
                elif event.key == 'KP1':
                    player_input.append('move_sw')
                elif event.key == 'KP3':
                    player_input.append('move_se')
                elif event.key == 'KP5':  # waiting for 1 step
                    player_input.append('wait1step')
                elif event.key == 'CHAR':
                    if event.keychar == 'c':  # closing doors
                        key = tdl.event.keyWait()
                        if key.keychar == 'UP' or key.keychar == 'KP8':
                            player_input.append('close_n')
                        elif key.keychar == 'DOWN' or key.keychar == 'KP2':
                            player_input.append('close_s')
                        elif key.keychar == 'LEFT' or key.keychar == 'KP4':
                            player_input.append('close_w')
                        elif key.keychar == 'RIGHT' or key.keychar == 'KP6':
                            player_input.append('close_e')
                        elif key.keychar == 'KP7':
                            player_input.append('close_nw')
                        elif key.keychar == 'KP9':
                            player_input.append('close_ne')
                        elif key.keychar == 'KP1':
                            player_input.append('close_sw')
                        elif key.keychar == 'KP3':
                            player_input.append('close_se')
                    if event.keychar == 's':  # smashin' things
                        key = tdl.event.keyWait()
                        if key.keychar == 'UP' or key.keychar == 'KP8':
                            player_input.append('smash_n')
                        elif key.keychar == 'DOWN' or key.keychar == 'KP2':
                            player_input.append('smash_s')
                        elif key.keychar == 'LEFT' or key.keychar == 'KP4':
                            player_input.append('smash_w')
                        elif key.keychar == 'RIGHT' or key.keychar == 'KP6':
                            player_input.append('smash_e')
                        elif key.keychar == 'KP7':
                            player_input.append('smash_nw')
                        elif key.keychar == 'KP9':
                            player_input.append('smash_ne')
                        elif key.keychar == 'KP1':
                            player_input.append('smash_sw')
                        elif key.keychar == 'KP3':
                            player_input.append('smash_se')
                    if event.keychar == 'l':  # 'look' command
                        player_input.append('look')
                    if event.keychar == '`':  # show/hide debug log
                        player_input.append('debug_log')
                    if event.keychar == 'i':  # show inventory menu
                        player_input.append('inventory')
                    if event.keychar == 'w':  # wield (equip) item command
                        player_input.append('wield_item')
                    if event.keychar == 'o':  # take 'o'ff command
                        player_input.append('take_off_item')
                    if event.keychar == 'u':  # use command
                        player_input.append('use_item')
                    if event.keychar == 'g':  # pick up on same cell command
                        player_input.append('ground')
                    if event.keychar == 'd':  # drop item command
                        player_input.append('drop')
                    if event.keychar == 'r':  # reload ranged weapon command
                        player_input.append('reload')
                    if event.keychar == 'U':  # unload ranged weapon command
                        player_input.append('unload')
                    if event.keychar == 'f':  # fire ranged weapon command
                        player_input.append('fire')
                    if event.keychar == 't':  # throw item in hands command
                        player_input.append('throw_hands')
            elif event.type == "QUIT":
                player_input.append('exit')
        return player_input


def get_raw_input():
    """ Function returns list of player input (not keypresses, but desired actions) """
    if INPUT_ENGINE == 'TDL':
        return tdl.event.get()  # get input from TDL

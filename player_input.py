"""
    Player input handling.
"""

import tdl


INPUT_ENGINE = 'TDL'


# class Command
#
# class CommandMgr:
#     def __init__(self):
#         self.commands = []
#
#     def add_command(self, ):


def handle_input(game):
    """ Function returns list of player input (not keypresses, but desired actions) """
    if INPUT_ENGINE == 'TDL':
        user_input = tdl.event.get()  # get input from TDL
        player_input = []
        # translate TDL input to game logic player actions
        for event in user_input:
            if event.type == 'KEYDOWN':
                if event.key == 'ESCAPE':  # exiting the game
                    player_input.append('exit')
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
            elif event.type == "QUIT":
                player_input.append('exit')
        return player_input

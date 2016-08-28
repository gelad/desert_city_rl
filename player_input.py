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
                if event.key == 'ESCAPE':
                    player_input.append('exit')
                if event.key == 'UP':
                    player_input.append('move_up')
                elif event.key == 'DOWN':
                    player_input.append('move_down')
                elif event.key == 'LEFT':
                    player_input.append('move_left')
                elif event.key == 'RIGHT':
                    player_input.append('move_right')
                elif event.key == 'CHAR':
                    if event.keychar == 'c':
                        key = tdl.event.keyWait()
                        if key.keychar == 'UP':
                            player_input.append('close_up')
                        elif key.keychar == 'DOWN':
                            player_input.append('close_down')
                        elif key.keychar == 'LEFT':
                            player_input.append('close_left')
                        elif key.keychar == 'RIGHT':
                            player_input.append('close_right')
            elif event.type == "QUIT":
                player_input.append('exit')
        return player_input

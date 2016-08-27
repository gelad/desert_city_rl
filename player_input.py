import tdl


INPUT_ENGINE = 'TDL'


def handle_input():
    if INPUT_ENGINE == 'TDL':
        user_input = tdl.event.get()
        player_input = []
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
        return player_input

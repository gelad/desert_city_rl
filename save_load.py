"""
    This module contains game save and load functions
"""
import zlib
import pickle
from time import sleep

import gc


def save_game(game):
    """ Game saving function """
    while game.loop_is_running:  # if main game logic loop is in progress - wait until it finishes
        sleep(0.1)
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

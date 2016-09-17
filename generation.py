"""
    This file contains functions that generate locations (and other stuff that is generated - will be here)
"""

import game_logic

import random


def generate_loc(pattern, settings, width, height):
    """ Location generation function """
    loc = game_logic.Location(width, height)
    if pattern == 'clear':  # simply make a location full of sand tiles
        loc.cells.clear()
        loc.cells = [[game_logic.Cell('SAND') for y in range(loc.height)] for x in range(loc.width)]
    if pattern == 'ruins':  # simply make a location of sand and few wall and door elements
        loc.cells.clear()
        loc.cells = [[game_logic.Cell('SAND') for y in range(loc.height)] for x in range(loc.width)]
        random.seed()
        for i in range(0, random.randint(2, 40)):
            loc.place_entity('wall_sandstone', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(2, 20)):
            loc.place_entity('door_wooden', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(2, 20)):
            loc.place_entity('item_boulder', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 5)):
            loc.place_entity('item_healing_potion', random.randint(0, loc.width - 1),
                             random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 2)):
            loc.place_entity('item_sabre', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_barbed_loincloth', random.randint(0, loc.width - 1),
                             random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_misurka', random.randint(0, 10), random.randint(0, 10))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_mail_armor', random.randint(0, 10), random.randint(0, 10))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_iron_pauldrons', random.randint(0, 10), random.randint(0, 10))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_iron_boots', random.randint(0, 10), random.randint(0, 10))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_iron_armguards', random.randint(0, 10), random.randint(0, 10))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('item_mail_leggings', random.randint(0, 10), random.randint(0, 10))
        for i in range(0, random.randint(1, 2)):
            loc.place_entity('item_dagger', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 2)):
            loc.place_entity('item_bronze_maul', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 2)):
            loc.place_entity('item_hunting_crossbow', random.randint(0, loc.width - 1),
                             random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 5)):
            loc.place_entity('item_bronze_bolt', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(2, 5)):
            loc.place_entity('mob_mindless_body', random.randint(0, loc.width - 1),
                             random.randint(0, loc.height - 1))
        for i in range(0, random.randint(2, 5)):
            loc.place_entity('mob_scorpion', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('mob_rakshasa', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
        for i in range(0, random.randint(1, 3)):
            loc.place_entity('mob_sand_golem', random.randint(0, loc.width - 1), random.randint(0, loc.height - 1))
    return loc  # return generated location

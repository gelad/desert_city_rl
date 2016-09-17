"""
    This file contains functions that generate locations (and other stuff that is generated - will be here)
"""

import game_logic

import random
from collections import namedtuple


def generate_loc(loc_type, settings, width, height):
    """ Location generation function """
    loc = game_logic.Location(width, height)
    if loc_type == 'clear':  # simply make a location full of sand tiles
        loc.cells.clear()
        loc.cells = [[game_logic.Cell('SAND') for y in range(loc.height)] for x in range(loc.width)]
    if loc_type == 'ruins':  # simply make a location of sand and few wall and door elements
        loc.cells.clear()
        loc.cells = [[game_logic.Cell('SAND') for y in range(loc.height)] for x in range(loc.width)]
        random.seed()
        grid_size = 20  # divide location to plots 20x20 each, making a grid 20 times smaller than map
        plots = [[None for y in range(height // grid_size - 1)] for x in range(width // grid_size - 1)]
        # plot is a named tuple ([list of loc.cells in plot], building_x, building_y, building_width, building_height)
        Plot = namedtuple('Plot', ['cells', 'b_x', 'b_y', 'b_w', 'b_h', 'b_type'])
        for plot_x in range(width // grid_size - 1):
            for plot_y in range(height // grid_size - 1):
                build_type = game_logic.weighted_choice([('house', 50), ('none', 50)])  # choose a building type
                if build_type == 'house':  # generate a house
                    build_x = random.randrange(grid_size // 2)
                    build_y = random.randrange(grid_size // 2)
                    build_w = random.randrange(4, grid_size // 2)
                    build_h = random.randrange(4, grid_size // 2)
                    plots[plot_x][plot_y] = \
                        Plot(cells=[[loc.cells[x][y] for y in range(plot_y, plot_y + grid_size)] for x in
                             range(plot_x, plot_x + grid_size)],
                             b_x=build_x, b_y=build_y, b_w=build_w, b_h=build_h, b_type=build_type)
                    building = subgen_building('house', grid_size // 2, grid_size // 2)
                    for x in range(grid_size // 2):
                        for y in range(grid_size // 2):
                            loc_cell_x = x + build_x + plot_x * 20
                            loc_cell_y = y + build_y + plot_y * 20
                            loc.cells[loc_cell_x][loc_cell_y].tile = 'FLOOR_SANDSTONE'
                            if building[x][y] == 'wall':
                                loc.place_entity('wall_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'door':
                                loc.place_entity('door_wooden', loc_cell_x, loc_cell_y)
                elif build_type == 'none':  # generate no building
                    plots[plot_x][plot_y] = \
                        Plot(cells=[[loc.cells[x][y] for y in range(plot_y, plot_y + grid_size)] for x in
                                    range(plot_x, plot_x + grid_size)],
                             b_x=0, b_y=0, b_w=grid_size, b_h=grid_size, b_type=build_type)
                # TODO: add monster and loot generation in houses (and som e monsters outside)
                # TODO: add destructed buildings

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


def subgen_building(building, build_w, build_h, settings=None):
    """ Subgeneration function - generates a building """
    pattern = [['ground' for y in range(build_h)] for x in range(build_w)]  # fill cells with 'ground'
    if building == 'house':  # generate a simple house
        pattern = [['floor' for y in range(build_h)] for x in range(build_w)]  # fill cells with 'floor'
        for x in range(0, build_w):  # draw horizontal walls
            pattern[x][0] = 'wall'
            pattern[x][-1] = 'wall'
        for y in range(0, build_h):  # draw vertical walls
            pattern[0][y] = 'wall'
            pattern[-1][y] = 'wall'
        x = random.randrange(build_w)  # make a door
        y = random.randrange(build_h)
        direction = random.randrange(1, 4)
        if direction == 1: x = 0
        if direction == 2: x = -1
        if direction == 3: y = 0
        if direction == 4: y = -1
        pattern[x][y] = 'door'
    return pattern

"""
    This file contains functions that generate locations (and other stuff that is generated - will be here)
"""

import game_logic
import fov_los_pf

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
                build_type = game_logic.weighted_choice([('house', 70), ('none', 30)])  # choose a building type
                if build_type == 'house':  # generate a house
                    build_x = random.randrange(grid_size // 2)
                    build_y = random.randrange(grid_size // 2)
                    build_w = random.randrange(4, grid_size // 2)
                    build_h = random.randrange(4, grid_size // 2)
                    plots[plot_x][plot_y] = \
                        Plot(cells=[[loc.cells[x][y] for y in range(plot_y, plot_y + grid_size)] for x in
                             range(plot_x, plot_x + grid_size)],
                             b_x=build_x, b_y=build_y, b_w=build_w, b_h=build_h, b_type=build_type)
                    floor_cells = []  # empty floor cells for item gen
                    building = subgen_building('house', build_w, build_h,
                                               {'destruct': random.randint(1, 8)})
                    for x in range(build_w):
                        for y in range(build_h):
                            loc_cell_x = x + build_x + plot_x * 20
                            loc_cell_y = y + build_y + plot_y * 20
                            loc.cells[loc_cell_x][loc_cell_y].tile = 'FLOOR_SANDSTONE'
                            if building[x][y] == 'wall':
                                loc.place_entity('wall_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'door':
                                loc.place_entity('door_wooden', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'small_window':
                                loc.place_entity('window_small_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'large_window':
                                loc.place_entity('window_large_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'debris_stone':
                                loc.place_entity('debris_large_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'debris_wooden':
                                loc.place_entity('debris_large_wooden', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'sand':
                                loc.cells[loc_cell_x][loc_cell_y].tile = 'SAND'
                            # if cell is passable - add to floor list
                            if loc.cells[loc_cell_x][loc_cell_y].is_movement_allowed():
                                floor_cells.append((loc_cell_x, loc_cell_y))
                    item_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
                    for i in range(0, item_count):
                        item_id = game_logic.weighted_choice([(game_logic.weighted_choice([('item_healing_potion', 50),
                                                                                          ('item_haste_potion', 25),
                                                                                          ('item_antidote_potion', 25)]),
                                                               20),
                                                              (game_logic.weighted_choice([('item_sabre', 20),
                                                                                           ('item_dagger', 20),
                                                                                           ('item_longsword', 15),
                                                                                           ('item_bronze_maul', 15),
                                                                                           ('item_mace', 15),
                                                                                           ('item_assegai', 15)]),
                                                               30),
                                                              (game_logic.weighted_choice([('item_firebolt_scroll', 35),
                                                                                           ('item_frostbolt_scroll', 35),
                                                                                           ('item_lightning_scroll', 15),
                                                                                           ('item_ring_poison_res', 5),
                                                                                           ('item_ring_fire_res', 4),
                                                                                           ('item_ring_cold_res', 3),
                                                                                           ('item_ring_lightning_res', 3),]),
                                                               10),
                                                              ('item_misurka', 2), ('item_leather_cap', 3),
                                                              ('item_mail_armor', 2), ('item_leather_armor', 3),
                                                              ('item_iron_pauldrons', 2), ('item_leather_pauldrons', 3),
                                                              ('item_iron_boots', 2), ('item_leather_boots', 3),
                                                              ('item_iron_armguards', 2), ('item_leather_armguards', 3),
                                                              ('item_mail_leggings', 2), ('item_leather_leggings', 3),
                                                              (game_logic.weighted_choice([('item_hunting_crossbow', 50),
                                                                                          ('item_short_bow', 50)]),
                                                               5),
                                                              (game_logic.weighted_choice([('item_bronze_bolt', 50),
                                                                                          ('item_bronze_tipped_arrow', 30),
                                                                                          ('item_poisoned_arrow', 20)]),
                                                               10)])
                        item_coords = floor_cells[random.randrange(len(floor_cells))]
                        loc.place_entity(item_id, item_coords[0], item_coords[1])
                    mob_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
                    for m in range(0, mob_count):
                        mob_id = game_logic.weighted_choice([('mob_mindless_body', 55),
                                                            ('mob_scorpion', 20),
                                                            ('mob_rakshasa', 10 + item_count * 3),
                                                            ('mob_sand_golem', 7 + item_count * 3),
                                                            ('mob_lightning_wisp', 5 + item_count * 2),
                                                            ('mob_ifrit', 3 + item_count * 1)])
                        # more loot - dangerous mobs
                        mob_coords = floor_cells[random.randrange(len(floor_cells))]
                        loc.place_entity(mob_id, mob_coords[0], mob_coords[1])
                    trap_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
                    for m in range(0, trap_count):
                        trap_id = game_logic.weighted_choice([('trap_corrosive_moss', 100)])
                        trap_coords = floor_cells[random.randrange(len(floor_cells))]
                        loc.place_entity(trap_id, trap_coords[0], trap_coords[1])
                elif build_type == 'none':  # generate no building
                    plots[plot_x][plot_y] = \
                        Plot(cells=[[loc.cells[x][y] for y in range(plot_y, plot_y + grid_size)] for x in
                                    range(plot_x, plot_x + grid_size)],
                             b_x=0, b_y=0, b_w=grid_size, b_h=grid_size, b_type=build_type)
                    floor_cells = []
                    for x in range(grid_size // 2):
                        for y in range(grid_size // 2):
                            floor_cells.append((x + plot_x * 20, y + plot_y * 20))
                    # place some mobs even there are no building
                    mob_count = game_logic.weighted_choice([(0, 70), (1, 20), (2, 7), (3, 3)])
                    for m in range(0, mob_count):
                        mob_id = game_logic.weighted_choice([('mob_mindless_body', 50),
                                                             ('mob_scorpion', 40),
                                                             ('mob_rakshasa', 10)])
                        mob_coords = floor_cells[random.randrange(len(floor_cells))]
                        loc.place_entity(mob_id, mob_coords[0], mob_coords[1])
    loc.path_map_recompute()  # generate pathfinding map for location
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
        for n in range(1, 8): # make windows
            x = random.randrange(1, build_w - 1)
            y = random.randrange(1, build_h - 1)
            direction = random.randint(1, 4)
            if direction == 1: x = 0
            if direction == 2: x = -1
            if direction == 3: y = 0
            if direction == 4: y = -1
            pattern[x][y] = game_logic.weighted_choice([('small_window', 50), ('large_window', 50)])
        x = random.randrange(1, build_w - 1)  # make a door
        y = random.randrange(1, build_h - 1)
        direction = random.randint(1, 4)
        if direction == 1: x = 0
        if direction == 2: x = -1
        if direction == 3: y = 0
        if direction == 4: y = -1
        pattern[x][y] = 'door'
        # destruction algorithm
        if 'destruct' in settings:
            for i in range(settings['destruct']):  # run destruction as many times as desired
                dest_cells_num = int(build_w * build_h / 10)  # one iteration affects up to 10% of the building
                for j in range(dest_cells_num):  # destroy selected number of cells
                    x = random.randrange(build_w)
                    y = random.randrange(build_h)
                    if pattern[x][y] == 'wall' or pattern[x][y] == 'small_window' or pattern[x][y] == 'large_window':
                        pattern[x][y] = game_logic.weighted_choice([('debris_stone', 70), ('floor', 30)])
                    elif pattern[x][y] == 'door':
                        pattern[x][y] = game_logic.weighted_choice([('debris_wood', 70), ('floor', 30)])
                    elif pattern[x][y] == 'floor':
                        pattern[x][y] = game_logic.weighted_choice([('sand', 70), ('floor', 30)])
    return pattern

"""
    This file contains functions that generate locations (and other stuff that is generated - will be here)
"""

import game_logic
import fov_los_pf
import dataset
import xp_loader

import jsonpickle

import random
import gzip
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
                # choose a building type
                build_type = game_logic.weighted_choice([('house', 50), ('prefab_small_shop', 30), ('none', 20)])
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
                        item = dataset.get_item_from_loot_list('house_default')
                        item_coords = floor_cells[random.randrange(len(floor_cells))]
                        loc.place_entity(item, item_coords[0], item_coords[1])
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
                        mob = loc.place_entity(mob_id, mob_coords[0], mob_coords[1])
                        gen_mob_loot(mob)  # generate mob loot
                    trap_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
                    for m in range(0, trap_count):
                        trap_id = game_logic.weighted_choice([('trap_corrosive_moss', 100)])
                        trap_coords = floor_cells[random.randrange(len(floor_cells))]
                        mob = loc.place_entity(trap_id, trap_coords[0], trap_coords[1])
                        gen_mob_loot(mob)  # generate mob loot
                elif build_type[:7] == 'prefab_':
                    prefab_name = build_type[7:]
                    place_prefab(name=prefab_name, loc=loc, plot_size=grid_size, plot_x=plot_x * grid_size,
                                 plot_y=plot_y * grid_size, settings={'destruct': random.randint(1, 8),
                                                                      'rotate': random.randint(0, 3)})
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
                        mob = loc.place_entity(mob_id, mob_coords[0], mob_coords[1])
                        gen_mob_loot(mob)  # generate mob loot
    loc.path_map_recompute()  # generate pathfinding map for location
    return loc  # return generated location


def load_prefab(name):
    """ Load building from prefab, created in REXPaint
        Prefab layers for now:
        0 - tiles
        1 - props and such - walls, windows, doors
        2 - 'i'nner and 'o'uter cells - for separate mob and loot spawn
    """
    prefab_xp = xp_loader.load_xp_string(gzip.open('data/prefabs/' + name + '.xp').read())
    return prefab_xp


def place_prefab(name, loc, plot_size, plot_x, plot_y, settings=None):
    """ Places prefab on the map, generating items, mobs, destruction etc """
    if settings is None:  # if no settings - empty set
        settings = {}
    prefab = load_prefab(name)  # load prefab from .xp file
    build_w = prefab['width']  # building dimensions - from prefab
    build_h = prefab['height']
    build_x = random.randrange(plot_size - build_w)  # random building position within plot (according to its size)
    build_y = random.randrange(plot_size - build_h)
    if 'rotate' in settings:  # rotate prefab if needed
        i = 0
        while i < settings['rotate']:
            for l in range(len(prefab['layer_data'])):
                cells = prefab['layer_data'][l]['cells']
                prefab['layer_data'][l]['cells'] = list(zip(*cells[::-1]))
            i += 1
    if 'destruct' in settings:  # TODO: destruction part needs rework
        for i in range(settings['destruct']):  # run destruction as many times as desired
            dest_cells_num = int(build_w * build_h / 10)  # one iteration affects up to 10% of the building
            for j in range(dest_cells_num):  # destroy selected number of cells
                x = random.randrange(build_w)
                y = random.randrange(build_h)
                tile = prefab['layer_data'][0]['cells'][x][y]
                char_tile = chr(prefab['layer_data'][0]['cells'][x][y]['keycode'])
                if ord(char_tile) == 0:  # space has 0 and 32 code in REXPaint - problems if it's 0
                    char_tile = ' '
                if char_tile == ' ':
                    prefab['layer_data'][0]['cells'][x][y]['keycode'] = \
                        ord(game_logic.weighted_choice([('.', 70), (' ', 30)]))
                char = chr(prefab['layer_data'][1]['cells'][x][y]['keycode'])
                if char == '#' or char == '"' or char == '_':
                    prefab['layer_data'][1]['cells'][x][y]['keycode'] = \
                        ord(game_logic.weighted_choice([('&', 70), (' ', 30)]))
                elif char == '+':
                    prefab['layer_data'][1]['cells'][x][y]['keycode'] = \
                        ord(game_logic.weighted_choice([('&', 70), (' ', 30)]))
    # actual entities and tiles placing part
    inner_cells = []  # empty floor cells for item and mob generation
    for x in range(build_w):
        for y in range(build_h):
            loc_cell_x = x + build_x + plot_x  # location cell coords - for placement
            loc_cell_y = y + build_y + plot_y
            tile_cell = prefab['layer_data'][0]['cells'][x][y]  # get tile info from prefab
            char_tile = chr(tile_cell['keycode'])
            if ord(char_tile) == 0:  # space has 0 and 32 code in REXPaint - problems if it's 0
                char_tile = ' '
            char_tile_color = (tile_cell['fore_r'], tile_cell['fore_g'], tile_cell['fore_b'])
            char_tile_bgcolor = (tile_cell['back_r'], tile_cell['back_g'], tile_cell['back_b'])
            for tile in dataset.tile_set:  # search for matching tile in dataset
                if char_tile == dataset.tile_set[tile][0] and char_tile_color == tuple(dataset.tile_set[tile][1]) \
                        and char_tile_bgcolor == tuple(dataset.tile_set[tile][2]):
                    loc.cells[loc_cell_x][loc_cell_y].tile = tile
                    break
            entity_cell = prefab['layer_data'][1]['cells'][x][y]  # get entity info from prefab
            char_ent = chr(entity_cell['keycode'])
            char_ent_color = (entity_cell['fore_r'], entity_cell['fore_g'], entity_cell['fore_b'])
            for entity_ID in dataset.data_set:  # search for matching entity in dataset
                if dataset.data_set[entity_ID].char == char_ent and\
                                tuple(dataset.data_set[entity_ID].color) == char_ent_color:
                    loc.place_entity(entity_ID, loc_cell_x, loc_cell_y)
                    break
            # if cell is passable and marked as 'i'nner - add to inner list
            if loc.cells[loc_cell_x][loc_cell_y].is_movement_allowed() and prefab['layer_data'][2]['cells'][x][y][
                                                                                  'keycode'] == ord('i'):
                inner_cells.append((loc_cell_x, loc_cell_y))
            # TODO: add 'o'uter cells list - when prefab will have separate outer and inner tile items and mobs
    # ============= PLACEHOLDER CODE - NEED LOAD ITEM AND MOB GENERATION INFO FROM PREFAB =========================
    item_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
    for i in range(0, item_count):
        item = dataset.get_item_from_loot_list('house_default')
        item_coords = inner_cells[random.randrange(len(inner_cells))]
        loc.place_entity(item, item_coords[0], item_coords[1])
    mob_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
    for m in range(0, mob_count):
        mob_id = game_logic.weighted_choice([('mob_mindless_body', 55),
                                             ('mob_scorpion', 20),
                                             ('mob_rakshasa', 10 + item_count * 3),
                                             ('mob_sand_golem', 7 + item_count * 3),
                                             ('mob_lightning_wisp', 5 + item_count * 2),
                                             ('mob_ifrit', 3 + item_count * 1)])
        # more loot - dangerous mobs
        mob_coords = inner_cells[random.randrange(len(inner_cells))]
        mob = loc.place_entity(mob_id, mob_coords[0], mob_coords[1])
        gen_mob_loot(mob)  # generate mob loot
    trap_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
    for m in range(0, trap_count):
        trap_id = game_logic.weighted_choice([('trap_corrosive_moss', 100)])
        trap_coords = inner_cells[random.randrange(len(inner_cells))]
        mob = loc.place_entity(trap_id, trap_coords[0], trap_coords[1])
        gen_mob_loot(mob)  # generate mob loot
        # ============================================================================================================


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
        for i in range(random.randrange(10)):  # make some walls inside
            x = random.randrange(build_w)
            y = random.randrange(build_h)
            if pattern[x][y] == 'floor':
                pattern[x][y] = 'wall'
        for n in range(1, 8):  # make windows
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
        if settings:
            if 'destruct' in settings:
                for i in range(settings['destruct']):  # run destruction as many times as desired
                    dest_cells_num = int(build_w * build_h / 10)  # one iteration affects up to 10% of the building
                    for j in range(dest_cells_num):  # destroy selected number of cells
                        x = random.randrange(build_w)
                        y = random.randrange(build_h)
                        if pattern[x][y] == 'wall' or pattern[x][y] == 'small_window' or pattern[x][
                            y] == 'large_window':
                            pattern[x][y] = game_logic.weighted_choice([('debris_stone', 70), ('floor', 30)])
                        elif pattern[x][y] == 'door':
                            pattern[x][y] = game_logic.weighted_choice([('debris_wood', 70), ('floor', 30)])
                        elif pattern[x][y] == 'floor':
                            pattern[x][y] = game_logic.weighted_choice([('sand', 70), ('floor', 30)])
    return pattern


def gen_mob_loot(mob):
    """ Function that generates mob loot and places it in inventory - mostly a placeholder now """
    try:
        if 'loot_list' in mob.properties:
            items = []
            if isinstance(mob.properties['loot_list'], str):
                items.append(dataset.get_item_from_loot_list(mob.properties['loot_list']))
            else:
                for lst in mob.properties['loot_list']:  # multiple lists allowed
                    items.append(dataset.get_item_from_loot_list(lst))
            for item in items:
                if item:
                    mob.add_item(item)
    except AttributeError:  # if no properties attribute - no loot
        pass

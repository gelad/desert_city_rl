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
                build_type = game_logic.weighted_choice([('house', 50), ('prefab_small_shop', 20),
                                                         ('prefab_small_market', 10), ('none', 20)])
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
                        item = dataset.get_item_from_loot_list('ruins_default_items')
                        item_coords = floor_cells[random.randrange(len(floor_cells))]
                        loc.place_entity(item, item_coords[0], item_coords[1])
                    mob_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
                    for m in range(0, mob_count):
                        mobs = dataset.get_entity_from_spawn_list('ruins_default_mobs')
                        if mobs:
                            if isinstance(mobs, list):  # if multiple mobs
                                for mob in mobs:
                                    mob_coords = floor_cells[random.randrange(len(floor_cells))]
                                    loc.place_entity(mob, mob_coords[0], mob_coords[1])
                                    gen_entity_loot(mob)  # generate mob loot
                            elif isinstance(mobs, game_logic.Entity):
                                mob_coords = floor_cells[random.randrange(len(floor_cells))]
                                loc.place_entity(mobs, mob_coords[0], mob_coords[1])
                                gen_entity_loot(mobs)  # generate mob loot
                    trap_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
                    for m in range(0, trap_count):
                        trap_id = game_logic.weighted_choice([('trap_corrosive_moss', 100)])
                        trap_coords = floor_cells[random.randrange(len(floor_cells))]
                        mob = loc.place_entity(trap_id, trap_coords[0], trap_coords[1])
                        gen_entity_loot(mob)  # generate mob loot
                elif build_type[:7] == 'prefab_':
                    prefab_name = build_type[7:]
                    place_prefab(name=prefab_name, loc=loc, plot_size=grid_size, plot_x=plot_x * grid_size,
                                 plot_y=plot_y * grid_size, settings={'loc_type': loc_type,
                                                                      'destruct': random.randint(1, 8),
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
                        gen_entity_loot(mob)  # generate mob loot
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


def load_prefab_info(name, settings):
    """
        Load prefab information: legend, mob/loot lists from JSON
    """
    try:  # try load prefab info
        fl = open('data/prefabs/' + name + '.json')
        prefab_info = jsonpickle.loads(fl.read())
        fl.close()
        if 'variant' in settings:  # if specific variant in settings
            prefab_variant = prefab_info['variants'][settings['variant']]
        else:  # if not specified - based on prefab info chances
            variants = []
            for v in prefab_info['variants']:  # make a list with chances - to use weighted_choice
                variants.append((v, prefab_info['variants'][v]['chance']))
            prefab_variant = prefab_info['variants'][game_logic.weighted_choice(variants)]  # choose one
        if 'loc_type' in settings:
            try:  # try load location info if exists
                fl = open('data/prefabs/' + settings['loc_type'] + '.json')
                loc_info = jsonpickle.loads(fl.read())
                fl.close()
                for v in prefab_variant:
                    if isinstance(prefab_variant[v], str):
                        if prefab_variant[v][:4] == 'LOC_':
                            try:
                                prefab_variant[v] = loc_info['variants'][prefab_variant[v][4:]][v]
                            except KeyError:
                                raise Exception('No location default for :' + v)
            except FileNotFoundError:
                print('Warning! No default prefab_info for location: ' + settings['loc_type'])
    except FileNotFoundError:
        raise Exception('No prefab info file for prefab"' + name + '"! Need one to generate loot and mobs.')
    return prefab_info, prefab_variant


def fill_prefab(loc, prefab, prefab_info, prefab_variant, build_x, build_y, build_w, build_h, settings=None):
    """ Function, that fills prefab with tiles and pre-defined Entites (such as walls, windows, doors) """
    cell_groups = {}  # empty floor cells for item and mob generation
    for x in range(build_w):
        for y in range(build_h):
            loc_cell_x = x + build_x  # location cell coords - for placement
            loc_cell_y = y + build_y
            tile_cell = prefab['layer_data'][0]['cells'][x][y]  # get tile info from prefab
            char_tile = chr(tile_cell['keycode'])
            if ord(char_tile) == 0:  # space has 0 and 32 code in REXPaint - problems if it's 0
                char_tile = ' '
            char_tile_color = (tile_cell['fore_r'], tile_cell['fore_g'], tile_cell['fore_b'])
            char_tile_bgcolor = (tile_cell['back_r'], tile_cell['back_g'], tile_cell['back_b'])
            found_tile = False  # tile found flag
            if char_tile == ' ' and char_tile_color == (0, 0, 0) and char_tile_bgcolor == (0, 0, 0):
                found_tile = True  # if empty tile - not look for it
            if 'legend' in prefab_info and not found_tile:  # first look in prefab legend - faster
                if 'tiles' in prefab_info['legend']:
                    for tile in prefab_info['legend']['tiles']:
                        if char_tile == tile['char'] and char_tile_color == tile['color'] and \
                                        char_tile_bgcolor == tile['bgcolor']:
                            loc.cells[loc_cell_x][loc_cell_y].tile = tile['name']
                            found_tile = True
                            break
            if not found_tile:  # if not found in legend - search for matching tile in dataset
                for tile in dataset.tile_set:
                    if char_tile == dataset.tile_set[tile][0] and char_tile_color == tuple(dataset.tile_set[tile][1]) \
                            and char_tile_bgcolor == tuple(dataset.tile_set[tile][2]):
                        loc.cells[loc_cell_x][loc_cell_y].tile = tile
                        found_tile = True
                        break
            if not found_tile:
                pass  # TODO: uncomment when destruction is reworked
                # print('Warning! Tile ' + char_tile + ' not found in prefab info and dataset, skipped.')
            entity_cell = prefab['layer_data'][1]['cells'][x][y]  # get entity info from prefab
            char_ent = chr(entity_cell['keycode'])
            char_ent_color = (entity_cell['fore_r'], entity_cell['fore_g'], entity_cell['fore_b'])
            found_ent = False  # entity found flag
            if char_ent == ' ' and char_ent_color == (0, 0, 0):
                found_ent = True  # if empty entity glyph of black color - not look for it
            if 'legend' in prefab_info and not found_ent:  # first look in prefab legend - faster
                if 'entities' in prefab_info['legend']:
                    for entity in prefab_info['legend']['entities']:
                        if char_ent == entity['char'] and char_ent_color == entity['color']:
                            if entity['name'][:7] == 'PREFAB_':
                                pr_str = entity['name'][7:]
                                pr_set = dict(settings)  # make settings copy
                                if pr_str.find('MV'):  # if 'match variant' keyword
                                    pr_set['variant'] = prefab_variant['name']
                                if pr_str.find('RR'):  # if 'random rotation' keyword
                                    pr_set['rotate'] = random.randint(0, 3)
                                pr_name = pr_str[pr_str.find('NAME:') + 5:]
                                place_prefab(name=pr_name, loc=loc, plot_x=loc_cell_x, plot_y=loc_cell_y,
                                             settings=pr_set)
                            else:
                                loc.place_entity(entity['name'], loc_cell_x, loc_cell_y)
                            found_ent = True
                            break
            if not found_ent:  # if not found in legend - search for matching entity in dataset
                for entity in dataset.data_set:
                    if char_ent == dataset.data_set[entity].char and \
                                    char_ent_color == tuple(dataset.data_set[entity].color):
                        loc.place_entity(entity, loc_cell_x, loc_cell_y)
                        found_ent = True
                        break
            if not found_ent:
                pass  # TODO: uncomment when destruction is reworked
                # print('Warning! Entity ' + char_ent + ' not found in prefab info and dataset, skipped.')
            # make cell groups, according to prefab # TODO: Move cell groups creation to separate function
            cell_group_char = chr(prefab['layer_data'][2]['cells'][x][y]['keycode'])
            if loc.cells[loc_cell_x][loc_cell_y].is_movement_allowed():
                if cell_group_char in cell_groups:  # if such cells are already in cell_groups
                    cell_groups[cell_group_char].add((loc_cell_x, loc_cell_y))  # add cell to group
                else:  # if not - create new group with 1 cell
                    cell_groups.update({cell_group_char: {(loc_cell_x, loc_cell_y)}})
    return cell_groups


def populate_prefab(ent_type, prefab_variant, cell_groups, loc, exclude_affected_cells=False):
    """
        This function places mob, loot, trap entities in the prefab
        if exclude_affected_cells is True - removes cells, where something is placed from cell_groups
        (useful to not generating mobs one into another)
    """
    for c_group in cell_groups:  # iterate through cell groups
        try:
            list_name = prefab_variant[ent_type + '_' + c_group]
        except KeyError:  # if there are no spawn list for group - skip it
            break
        if ent_type + '_' + c_group + '_num_chances' in prefab_variant:
            entity_count = game_logic.weighted_choice(prefab_variant[ent_type + '_' + c_group + '_num_chances'])
        else:
            print('Warning! No entity number chances for prefab! Using defaults.')
            entity_count = game_logic.weighted_choice([(0, 50), (1, 25), (2, 15), (3, 10)])
        for i in range(0, entity_count):
            if ent_type == 'items':  # if any categories of Entities need special get functions - place here
                entities = dataset.get_item_from_loot_list(list_name)
            else:
                entities = dataset.get_entity_from_spawn_list(list_name)
            if entities:
                if isinstance(entities, list):  # if multiple entities
                    for entity in entities:
                        if len(cell_groups[c_group]) > 0:
                            entity_coords = random.choice(tuple(cell_groups[c_group]))
                            if exclude_affected_cells:  # if exclude affected flag is set - remove coords from group
                                cell_groups[c_group].remove(entity_coords)
                            loc.place_entity(entity, entity_coords[0], entity_coords[1])
                            gen_entity_loot(entity)  # generate entity loot
                elif isinstance(entities, game_logic.Entity):
                    if len(cell_groups[c_group]) > 0:
                        entity_coords = random.choice(tuple(cell_groups[c_group]))
                        if exclude_affected_cells:  # if exclude affected flag is set - remove coords from group
                            cell_groups[c_group].remove(entity_coords)
                        loc.place_entity(entities, entity_coords[0], entity_coords[1])
                        gen_entity_loot(entities)  # generate entity loot


def place_prefab(name, loc, plot_x, plot_y, plot_size=0, settings=None):
    """
        This function should be called to place prefab during generation.
        Places prefab on the map, generating items, mobs, destruction etc.
    """
    # TODO: ?? make prefab recursion - allow one contain another
    if settings is None:  # if no settings - empty set
        settings = {}
    prefab = load_prefab(name)  # load prefab from .xp file
    prefab_info, prefab_variant = load_prefab_info(name=name, settings=settings)  # load prefab info
    build_w = prefab['width']  # building dimensions - from prefab
    build_h = prefab['height']
    if build_w != build_h:
        raise Exception('Not square prefab - currently not allowed.')
    if plot_size == 0:  # if plot size not specified - make it match prefab width
        plot_size = build_w
    if plot_size > build_w:
        # random building position within plot (according to size)
        build_x = random.randrange(plot_size - build_w) + plot_x
        build_y = random.randrange(plot_size - build_h) + plot_y
    elif plot_size == build_w:
        build_x = plot_x  # building takes whole plot
        build_y = plot_y
    else:
        raise Exception('Building larger than plot!')
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
    # actual pre-defined entities and tiles placing
    cell_groups = fill_prefab(loc=loc, prefab=prefab, prefab_info=prefab_info, prefab_variant=prefab_variant,
                              build_x=build_x, build_y=build_y, build_w=build_w, build_h=build_h, settings=settings)
    if len(cell_groups) == 0:
        print('Warning! Empty cell groups in prefab.')
        return
    populate_prefab(ent_type='items', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc)  # add items
    populate_prefab(ent_type='mobs', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc,
                    exclude_affected_cells=True)  # add mobs
    populate_prefab(ent_type='traps', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc,
                    exclude_affected_cells=True)  # add traps


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


def gen_entity_loot(entity):
    """ Function that generates entity loot and places it in inventory - mostly a placeholder now """
    try:
        if 'loot_list' in entity.properties:
            items = []
            if isinstance(entity.properties['loot_list'], str):
                items.append(dataset.get_item_from_loot_list(entity.properties['loot_list']))
            else:
                for lst in entity.properties['loot_list']:  # multiple lists allowed
                    items.append(dataset.get_item_from_loot_list(lst))
            for item in items:
                if item:
                    entity.add_item(item)
    except AttributeError:  # if no properties attribute - no loot
        pass

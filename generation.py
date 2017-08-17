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

from functools import lru_cache


def generate_loc(loc_type, settings, width, height):
    """ Location generation function """
    loc = game_logic.Location(width, height)
    # load loc prefab info
    loc_prefab_info = get_prefab_info(name=loc_type)
    loc_default_variant = get_random_prefab_variant(prefab_info=loc_prefab_info, settings={'variant': 'default'})
    if loc_type == 'clear':  # simply make a location full of sand tiles
        loc.cells.clear()
        loc.cells = [[game_logic.Cell('SAND') for y in range(loc.height)] for x in range(loc.width)]
    if loc_type == 'ruins':  # simply make a location of sand and few wall and door elements
        loc.cells.clear()
        loc.cells = [[game_logic.Cell('SAND') for y in range(loc.height)] for x in range(loc.width)]
        random.seed()
        grid_size = 20  # divide location to plots 20x20 each, making a grid 20 times smaller than map
        plan_width = width // grid_size
        plan_height = height // grid_size
        if settings:
            plan_settings = dict(settings)
        else:
            plan_settings = dict()
        plan_settings['plan_width'] = plan_width
        plan_settings['plan_height'] = plan_height
        plan_settings['grid_size'] = grid_size
        plan = generate_loc_plan(loc_type, plan_settings)
        for plot_x in range(plan_width):
            for plot_y in range(plan_height):
                plot = plan[plot_x][plot_y]
                # check for structures other from buildings
                if plot['structure'] == 'road':  # if there are road
                    if plot['road_direction'] == 'vertical':
                        start_x = 0
                        end_x = grid_size
                        start_y = plot['road_on_plot_start']
                        end_y = plot['road_on_plot_start'] + plot['road_thickness']
                    else:
                        start_x = plot['road_on_plot_start']
                        end_x = plot['road_on_plot_start'] + plot['road_thickness']
                        start_y = 0
                        end_y = grid_size
                    for x in range(end_x - start_x):
                        for y in range(end_y - start_y):
                            loc_cell_x = x + start_x + plot_x * grid_size
                            loc_cell_y = y + start_y + plot_y * grid_size
                            loc.cells[loc_cell_x][loc_cell_y].tile = 'ROAD_STONE'
                    destruct(loc=loc, start_x=start_x + plot_x * grid_size, start_y=start_y + plot_y * grid_size,
                             width=end_x - start_x, height=end_y - start_y, settings={'passes': random.randint(1, 10),
                                                                                      'destroy_tiles': 'SAND'})
                # get a building type from plan
                if 'build_type' in plot:
                    build_type = plot['build_type']
                else:
                    build_type = 'none'
                if build_type == 'house' or build_type == 'multiroom_house':  # generate a house
                    if build_type == 'house':
                        build_x = random.randrange(grid_size // 2)
                        build_y = random.randrange(grid_size // 2)
                        build_w = random.randrange(4, grid_size // 2)
                        build_h = random.randrange(4, grid_size // 2)
                    elif build_type == 'multiroom_house':
                        build_x = random.randrange(grid_size // 4)
                        build_y = random.randrange(grid_size // 4)
                        build_w = random.randrange(10, grid_size - build_x)
                        build_h = random.randrange(10, grid_size - build_y)
                    # TODO: think if 'cells' are needed in plan or not
                    plot['cells'] = [[loc.cells[x][y] for y in range(plot_y, plot_y + grid_size)] for x
                                                     in range(plot_x, plot_x + grid_size)]
                    floor_cells = []  # empty floor cells for item gen
                    building = subgen_building(building=build_type, build_w=build_w, build_h=build_h)
                    for x in range(build_w):
                        for y in range(build_h):
                            loc_cell_x = x + build_x + plot_x * grid_size
                            loc_cell_y = y + build_y + plot_y * grid_size
                            loc.cells[loc_cell_x][loc_cell_y].tile = 'FLOOR_SANDSTONE'
                            if building[x][y] == 'sand':
                                loc.cells[loc_cell_x][loc_cell_y].tile = 'SAND'
                            if building[x][y] == 'wall':
                                loc.place_entity('wall_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'door':
                                loc.place_entity('door_wooden', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'small_window':
                                loc.place_entity('window_small_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'large_window':
                                loc.place_entity('window_large_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'furniture':
                                loc.place_entity(dataset.get_entity_from_spawn_list('house_furniture'),
                                                 loc_cell_x, loc_cell_y)
                            if building[x][y] == 'debris_stone':
                                loc.place_entity('debris_large_sandstone', loc_cell_x, loc_cell_y)
                            if building[x][y] == 'debris_wooden':
                                loc.place_entity('debris_large_wooden', loc_cell_x, loc_cell_y)
                            # if cell is passable - add to floor list
                            if loc.cells[loc_cell_x][loc_cell_y].is_movement_allowed():
                                floor_cells.append((loc_cell_x, loc_cell_y))
                    destruct(loc=loc, start_x=build_x + plot_x * grid_size, start_y=build_y + plot_y * grid_size,
                             width=build_w, height=build_h, settings={'passes': random.randint(1, 10),
                                                                      'destroy_tiles': 'SAND'})  # destroy building
                    populate_prefab(ent_type='items', prefab_variant=loc_default_variant,
                                    cell_groups={'i': floor_cells}, loc=loc)  # add items
                    populate_prefab(ent_type='relics', prefab_variant=loc_default_variant,
                                    cell_groups={'i': floor_cells}, loc=loc)  # add relics
                    populate_prefab(ent_type='mobs', prefab_variant=loc_default_variant,
                                    cell_groups={'i': floor_cells}, loc=loc, exclude_affected_cells=True)  # add mobs
                    populate_prefab(ent_type='traps', prefab_variant=loc_default_variant,
                                    cell_groups={'i': floor_cells}, loc=loc, exclude_affected_cells=True)  # add traps
                elif build_type[:7] == 'prefab_':
                    prefab_name = build_type[7:]
                    place_prefab(name=prefab_name, loc=loc, plot_size=grid_size, plot_x=plot_x * grid_size,
                                 plot_y=plot_y * grid_size, settings={'loc_type': loc_type,
                                                                      'destruct': {'passes': random.randint(1, 10),
                                                                                   'destroy_tiles': 'SAND'},
                                                                      'rotate': random.randint(0, 3)})
                elif build_type == 'none':  # generate no building
                    plot['cells'] = [[loc.cells[x][y] for y in range(plot_y, plot_y + grid_size)] for x
                                                      in range(plot_x, plot_x + grid_size)]
                    outer_cells = []
                    for x in range(grid_size // 2):
                        for y in range(grid_size // 2):
                            outer_cells.append((x + plot_x * grid_size, y + plot_y * grid_size))
                    # place some mobs and loot even there are no building
                    populate_prefab(ent_type='items', prefab_variant=loc_default_variant,
                                    cell_groups={'o': outer_cells}, loc=loc)  # add items
                    populate_prefab(ent_type='relics', prefab_variant=loc_default_variant,
                                    cell_groups={'o': outer_cells}, loc=loc)  # add relics
                    populate_prefab(ent_type='mobs', prefab_variant=loc_default_variant,
                                    cell_groups={'o': outer_cells}, loc=loc, exclude_affected_cells=True)  # add mobs
                    populate_prefab(ent_type='traps', prefab_variant=loc_default_variant,
                                    cell_groups={'o': outer_cells}, loc=loc, exclude_affected_cells=True)  # add traps
        # small map features placement (in any empty spaces for now)
        # long walls - TEST
        generate_small_features(loc=loc, settings={'loc_type': loc_type, 'small_feats_num': random.randrange(2, 20),
                                                   'feature_types': [('long_wall', 100)], 'placing': {'passable'}})
        # other features
        generate_small_features(loc=loc, settings={'loc_type': loc_type, 'small_feats_num': random.randrange(30, 150),
                                                   'feature_types': [('building_fragment', 80),
                                                                     ('prefab_market_lot', 6),
                                                                     ('prefab_market_lot2', 6),
                                                                     ('prefab_market_lot3', 6),
                                                                     ('prefab_dead_adventurer', 2)],
                                                   'destruct': {'passes': (1, 5),
                                                                'destroy_tiles': 'SAND'},
                                                   'placing': {'passable'}})
    loc.path_map_recompute()  # generate pathfinding map for location
    return loc  # return generated location


def generate_small_features(loc, settings=None):
    """ Generate small features on loc """
    small_feats_num = settings['small_feats_num']
    for i in range(small_feats_num):
        # determine feature type
        feat_type = game_logic.weighted_choice(settings['feature_types'])
        if feat_type[:7] == 'prefab_':  # if small feature is a prefab
            prefab_name = feat_type[7:]
            prefab = get_prefab(prefab_name)
            place = loc.find_place({'shape': 'rect', 'size_x': prefab['width'], 'size_y': prefab['height'],
                                    'place': 'random', 'tries': 100, 'placing': settings['placing']})
            if place:
                xp, yp = place
                prefab_settings = {'rotate': random.randint(0, 3)}
                prefab_settings.update(settings)
                place_prefab(name=prefab_name, loc=loc, plot_size=prefab['width'], plot_x=xp,
                             plot_y=yp, settings=prefab_settings)
        elif feat_type == "building_fragment":
            sx = random.randrange(1, 5)
            sy = random.randrange(1, 5)
            place = loc.find_place({'shape': 'rect', 'size_x': sx, 'size_y': sy, 'place': 'random', 'tries': 100,
                                   'placing': settings['placing']})
            if place:
                xp, yp = place
                for x in range(xp, xp + sx):
                    for y in range(yp, yp + sy):
                        if not loc.cells[x][y].is_there_a(game_logic.Prop):
                            if random.randrange(100) > 70:
                                loc.place_entity('wall_sandstone', x, y)
                            elif random.randrange(100) > 50:
                                loc.place_entity('debris_large_sandstone', x, y)
        # TODO: make more complex ruins and walls
        elif feat_type == "long_wall":
            direction = game_logic.weighted_choice([('horizontal', 50), ('vertical', 50)])
            if direction == 'vertical':
                sx = random.randrange(1, 2)
                sy = random.randrange(5, 100)
            elif direction == 'horizontal':
                sx = random.randrange(5, 100)
                sy = random.randrange(1, 2)
            place = loc.find_place({'shape': 'rect', 'size_x': sx, 'size_y': sy, 'place': 'random', 'tries': 100,
                                   'placing': settings['placing']})
            if place:
                xp, yp = place
                for x in range(xp, xp + sx):
                    for y in range(yp, yp + sy):
                        if not loc.cells[x][y].is_there_a(game_logic.Prop):
                            if random.randrange(100) > 10:
                                loc.place_entity('wall_sandstone', x, y)
                            elif random.randrange(100) > 10:
                                loc.place_entity('debris_large_sandstone', x, y)


def generate_loc_plan(loc_type, settings):
    """ Generate location plan - what buildings (or else) to place in plots """
    plan_width = settings['plan_width']
    plan_height = settings['plan_height']
    grid_size = settings['grid_size']
    # create an empty plan
    plan = [[{'structure': None} for y in range(plan_height)] for x in range(plan_width)]
    if loc_type == 'clear':
        pass
    elif loc_type == 'ruins':
        # TODO: add more "big features" - squares, multi-plot buildings, etc
        roads = random.randrange(0, 3)  # 0 to 3 roads on ruins location
        # simple road generation
        for n in range(roads):
            road_direction = game_logic.weighted_choice([('horizontal', 50), ('vertical', 50)])
            road_x = random.randrange(plan_width - 1)  # road coords on plan grid
            road_y = random.randrange(plan_height - 1)
            road_thickness = random.randrange(2, grid_size - 1)
            road_on_plot_start = random.randrange(grid_size - 1)  # road coord in specific plot
            if road_direction == 'vertical':
                road_length = random.randrange((plan_height - 1) - road_x)
                for x in range(road_x, road_x + road_length):
                    plan[x][road_y]['structure'] = 'road'
                    plan[x][road_y]['road_direction'] = road_direction
                    plan[x][road_y]['road_thickness'] = road_thickness
                    plan[x][road_y]['road_on_plot_start'] = road_on_plot_start
            else:
                road_length = random.randrange((plan_width - 1) - road_y)
                for y in range(road_y, road_y + road_length):
                    plan[road_x][y]['structure'] = 'road'
                    plan[road_x][y]['road_direction'] = road_direction
                    plan[road_x][y]['road_thickness'] = road_thickness
                    plan[road_x][y]['road_on_plot_start'] = road_on_plot_start
        for x in range(plan_width):
            for y in range(plan_height):
                # choose a building type
                if plan[x][y]['structure'] is None:
                    build_type = game_logic.weighted_choice([('house', 20), ('multiroom_house', 20),
                                                             ('prefab_small_shop', 10), ('prefab_small_market', 5),
                                                             ('prefab_blacksmith_forge', 5), (None, 40)])
                    if build_type is not None:
                        plan[x][y]['structure'] = 'building'
                        plan[x][y]['build_type'] = build_type
                # TODO: make road-specific buildings like carts, wagons, small shops etc
    return plan


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
        for i in range(0, random.randrange(3)):  # make some furniture
            x = random.randrange(build_w)
            y = random.randrange(build_h)
            if pattern[x][y] == 'floor':
                pattern[x][y] = 'furniture'
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
    elif building == 'multiroom_house':  # generate a house with multiple rooms
        rooms = []
        room_needed = random.randrange(2, 5)  # TODO: replace magic numbers with gen parameters
        x1 = random.randrange(0, build_w)  # make first room
        y1 = random.randrange(0, build_h)
        x2 = random.randrange(x1, build_w)
        y2 = random.randrange(y1, build_h)
        first_room = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
        rooms.append(first_room)
        subgen_multiroom_place_room(x1=x1, y1=y1, x2=x2, y2=y2, pattern=pattern)
        tries = 0
        while len(rooms) < room_needed and tries < 100:  # generate more rooms
            tries += 1
            candidates = subgen_multiroom_get_candidates(build_w=build_w, build_h=build_h, pattern=pattern)
            if len(candidates) > 0: # check if there are suitable walls
                candidate = candidates[random.randrange(0, len(candidates) - 1)]
                room = subgen_multiroom_fit_room(build_w=build_w, build_h=build_h, pattern=pattern, candidate=candidate)
                if room:  # if room is succesifully placed
                    rooms.append(room)
            else:
                break
    return pattern


def subgen_multiroom_get_candidates(build_w, build_h, pattern):
    """ This function scans a building pattern for specific wall tiles, for creating additional rooms """
    candidates = []
    for x in range(1, build_w - 1):  # iterate through pattern (border tiles are ignored)
        for y in range(1, build_h - 1):
            # candidate = True
            if pattern[x][y] != 'wall':  # candidate must be a wall
                continue
            # candidate must have 2 adjacent walls on the same axis - |
            if not ((pattern[x - 1][y] == 'wall' and pattern[x + 1][y] == 'wall') or (
                    pattern[x][y - 1] == 'wall' and pattern[x][y - 1] == 'wall')):
                continue
            # candidate must have adjacent ground tile
            if not ((pattern[x - 1][y] == 'ground' or pattern[x + 1][y] == 'ground' or pattern[x][y - 1] == 'ground' or
                    pattern[x][y + 1] == 'ground')):
                continue
            candidates.append((x, y))
    return candidates


def subgen_multiroom_place_room(x1, y1, x2, y2, pattern):
    """ This sub places room on a pattern - actually fills cells with 'walls', 'floor', etc """
    for x in range(x1, x2):  # draw horizontal walls
        pattern[x][y1] = 'wall'
        pattern[x][y2] = 'wall'
    for y in range(y1, y2):  # draw vertical walls
        pattern[x1][y] = 'wall'
        pattern[x2][y] = 'wall'
    for x in range(x1 + 1, x2 - 1):  # fill inner space with floor
        for y in range(y1 + 1, y2 - 1):
            pattern[x][y] = 'floor'


def subgen_multiroom_fit_room(build_w, build_h, pattern, candidate):
    """ This function tries to fit a room, returns True/False """
    placed = False
    c_x, c_y = candidate
    # define new room placing side, according to wall 'candidate' coords (SOME COORD MAGIC)
    if pattern[c_x - 1][c_y] == 'ground':  # left
        x1 = random.randrange(0, c_x - 1)
        y1 = random.randrange(0, c_y)
        x2 = c_x
        y2 = random.randrange(c_y, build_h)
    elif pattern[c_x + 1][c_y] == 'ground':  # right
        x1 = c_x
        y1 = random.randrange(0, c_y)
        x2 = random.randrange(c_x + 1, build_w)
        y2 = random.randrange(c_y, build_h)
    elif pattern[c_x][c_y - 1] == 'ground':  # up
        x1 = random.randrange(0, c_x)
        y1 = random.randrange(0, c_y - 1)
        x2 = random.randrange(c_x, build_w)
        y2 = c_y
    elif pattern[c_x][c_y + 1] == 'ground':  # down
        x1 = random.randrange(0, c_x)
        y1 = c_y
        x2 = random.randrange(c_x, build_w)
        y2 = random.randrange(c_y + 1, build_h)
    else:  # that's impossible O_o
        raise RuntimeError('Wall candidate is invalid!')
    intersect = False
    for x in range(x1, x2):  # check new room for intersections with others
        for y in range(y1, y2):
            if pattern[x][y] == 'floor':
                intersect = True
                break
    if not intersect:  # if no intersection - place the room
        subgen_multiroom_place_room(x1=x1, y1=y1, x2=x2, y2=y2, pattern=pattern)
        pattern[c_x][c_y] = 'door'  # TODO: move door making to room placement code
        placed = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
    return placed


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


def destruct(loc, start_x, start_y, width, height, settings=None):
    """
        Imitates destruction of buildings. Very simple for now.
        Wreak havoc and destruction upon the map ;)
    """
    if settings is None:  # if no settings - default 1 pass
        settings = {'passes': 1, 'destroy_tiles': 'SAND'}
    if 'destructible_types' in settings:
        d_types = settings['destructible_types']
    else:
        d_types = {game_logic.Prop, game_logic.Door}
    if isinstance(settings['passes'], tuple):
        passes = random.randrange(settings['passes'][0], settings['passes'][1])
    else:
        passes = settings['passes']
    for i in range(0, passes):  # run destruction as many times as desired
        dest_cells_num = int(width * height / 10)  # one iteration affects up to 10% of the building
        for j in range(dest_cells_num):  # destroy selected number of cells
            x = random.randrange(width) + start_x  # random coords of affected cell
            y = random.randrange(height) + start_y
            if loc.is_in_boundaries(x, y):  # check for x, y in bounds
                destroyed = False
                for ent in loc.cells[x][y].entities:
                    for typ in d_types:
                        if isinstance(ent, typ):
                            try:
                                ent.death()
                            except AttributeError:  # if no death method
                                loc.remove_entity(ent)
                            destroyed = True
                            break
                        if destroyed:
                            break  # one entity destroyed at a time
                if 'destroy_tiles' in settings and not destroyed:
                    loc.cells[x][y].tile = settings['destroy_tiles']  # set tile to specified destroyed tile


# =================================== PREFAB SECTION =======================================================
@lru_cache()
def get_prefab(name):
    """ Load building from prefab, created in REXPaint
        Prefab layers for now:
        0 - tiles
        1 - props and such - walls, windows, doors
        2 - 'i'nner and 'o'uter cells - for separate mob and loot spawn
        results cached!
    """
    try:  # try load prefab info
        prefab_xp = xp_loader.load_xp_string(gzip.open('data/prefabs/' + name + '.xp').read())
    except FileNotFoundError:
        raise Exception('No file for prefab"' + name)
    return prefab_xp


@lru_cache()
def get_prefab_info(name):
    """
        Load prefab information: legend, mob/loot lists from JSON
        results cached!
    """
    try:  # try load prefab info
        fl = open('data/prefabs/' + name + '.json')
        prefab_info = jsonpickle.loads(fl.read())
        fl.close()
    except FileNotFoundError:
        raise Exception('No prefab info file for prefab"' + name + '"! Need one to generate loot and mobs.')
    return prefab_info


def get_random_prefab_variant(prefab_info, settings=None):
    """ Choose one of prefab variants (one specified or random if not) """
    if settings is None:  # if no settings - empty set
        settings = {}
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
    return prefab_variant


def fill_prefab(loc, prefab, prefab_info, prefab_variant, build_x, build_y, build_w, build_h, settings=None):
    """ Function, that fills prefab with tiles and pre-defined Entites (such as walls, windows, doors) """
    cell_groups = {}  # empty floor cells for item and mob generation
    prefabs = []  # list of sub-prefabs, if any. Placed after all other entities
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
                print('Warning! Tile ' + char_tile + ' not found in prefab info and dataset, skipped.')
            entity_cell = prefab['layer_data'][1]['cells'][x][y]  # get entity info from prefab
            char_ent = chr(entity_cell['keycode'])
            char_ent_color = (entity_cell['fore_r'], entity_cell['fore_g'], entity_cell['fore_b'])
            found_ent = False  # entity found flag
            if char_ent == ' ' and char_ent_color == (0, 0, 0):
                found_ent = True  # if empty entity glyph of black color - not look for it
            if 'legend' in prefab_info and not found_ent:  # first look in prefab legend - faster
                if 'entities' in prefab_info['legend']:
                    for entity in prefab_info['legend']['entities']:
                        # if list of entities with chances - WORKS WITH PREFABS ONLY
                        if isinstance(entity['name'], list):
                            # choices = [tuple(t) for t in entity['name']]
                            entity_id = game_logic.weighted_choice(entity['name'])  # choose one
                        else:
                            entity_id = entity['name']
                        if entity_id == 'None':  # if None entity - skip
                            found_ent = True
                            break
                        if char_ent == entity['char'] and char_ent_color == entity['color']:
                            if entity_id[:7] == 'PREFAB_':  # if sub-prefab
                                prefabs.append((entity_id[7:], loc_cell_x, loc_cell_y))  # add sub-prefab to list
                            else:  # if entity ID
                                loc.place_entity(entity_id, loc_cell_x, loc_cell_y)
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
                print('Warning! Entity ' + char_ent + ' of color' + str(char_ent_color) +
                      ' not found in prefab with variant "' + prefab_variant['name'] + '" info and dataset, skipped.')
    for sub_prefab in prefabs:  # sub-prefab placement
        pr_str, loc_cell_x, loc_cell_y = sub_prefab  # string and placement coords
        pr_set = dict(settings)  # make settings copy
        ch = pr_str.find('CH')
        if ch >= 0:  # if 'chance' keyword
            chance = int(pr_str[pr_str.find('(', ch) + 1:pr_str.find(';', ch)])
            total = int(pr_str[pr_str.find(';', ch) + 1:pr_str.find(')', ch)])
            roll = random.randint(0, total)
            if roll > chance:
                break
        offset_x = 0
        offset_y = 0
        po = pr_str.find('PO')
        if po >= 0:  # if 'position offset' keyword
            offset_x = int(pr_str[pr_str.find('(', po) + 1:pr_str.find(';', po)])
            offset_y = int(pr_str[pr_str.find(';', po) + 1:pr_str.find(')', po)])
        if pr_str.find('MV') >= 0:  # if 'match variant' keyword
            pr_set['variant'] = prefab_variant['name']
        if pr_str.find('RR') >= 0:  # if 'random rotation' keyword
            pr_set['rotate'] = random.randint(0, 3)
        if pr_str.find('DE') < 0:  # if no 'destruct' keyword
            if 'destruct' in pr_set:
                del pr_set['destruct']
        pr_name = pr_str[pr_str.find('NAME:') + 5:]
        place_prefab(name=pr_name, loc=loc, plot_x=loc_cell_x + offset_x, plot_y=loc_cell_y + offset_y, settings=pr_set)
    # make cell groups, according to prefab # TODO: Move cell groups creation to separate function
    for x in range(build_w):
        for y in range(build_h):
            loc_cell_x = x + build_x  # location cell coords - for blocked check
            loc_cell_y = y + build_y
            cell_group_char = chr(prefab['layer_data'][2]['cells'][x][y]['keycode'])
            if loc.cells[loc_cell_x][loc_cell_y].is_movement_allowed():
                if cell_group_char in cell_groups:  # if such cells are already in cell_groups
                    cell_groups[cell_group_char].add((loc_cell_x, loc_cell_y))  # add cell to group
                else:  # if not - create new group with 1 cell
                    cell_groups.update({cell_group_char: {(loc_cell_x, loc_cell_y)}})
    if len(cell_groups) == 0:
        pass
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
            if ent_type == 'items' or ent_type == 'relics':  # if any categories of Entities need special get functions - place here
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
    if settings is None:  # if no settings - empty set
        settings = {}
    prefab = get_prefab(name)  # load prefab from .xp file
    prefab_info = get_prefab_info(name=name)
    prefab_variant = get_random_prefab_variant(prefab_info=prefab_info, settings=settings)
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
    # actual pre-defined entities and tiles placing
    cell_groups = fill_prefab(loc=loc, prefab=prefab, prefab_info=prefab_info, prefab_variant=prefab_variant,
                              build_x=build_x, build_y=build_y, build_w=build_w, build_h=build_h, settings=settings)
    if 'destruct' in settings:  # prefab destruction according to settings
        destruct(loc=loc, start_x=build_x, start_y=build_y, width=build_w, height=build_h,
                 settings=settings['destruct'])
    if len(cell_groups) == 0:
        print('Warning! Empty cell groups in prefab "' + name + '"')
        return
    populate_prefab(ent_type='items', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc)  # add items
    populate_prefab(ent_type='relics', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc)  # add relics
    populate_prefab(ent_type='mobs', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc,
                    exclude_affected_cells=True)  # add mobs
    populate_prefab(ent_type='traps', prefab_variant=prefab_variant, cell_groups=cell_groups, loc=loc,
                    exclude_affected_cells=True)  # add traps

# =================================================================================================================


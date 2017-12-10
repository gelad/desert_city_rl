"""
    This file contains functions to work with data - saved templates for Entities and so on.
"""
import game_logic

import random
import os

import jsonpickle

tile_dict = {}  # dict that contains tile info
ability_dict = {}  # dict containing ability templates
entity_dict = {}  # dict containing entity templates


def initialize():
    """ Function that loads entity templates to data_set """
    # loading tileset
    tile_dict.update(jsonpickle.loads(open("data/tileset.json", 'r').read()))
    # loading ability and entity templates
    load_templates()


def load_templates():
    """ Function to load templates from files """
    # load abilities
    for subdir, dirs, files in os.walk('data/abilities'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(subdir, file)
                try:
                    f = open(file_path)
                    template = jsonpickle.loads(f.read())
                    ability_dict[template.data_id] = template
                    f.close()
                except:
                    print('Oops! Something is wrong with ' + file)
    # load entities
    for subdir, dirs, files in os.walk('data/entities'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(subdir, file)
                try:
                    f = open(file_path)
                    template = jsonpickle.loads(f.read())
                    f.close()
                    if 'blocks_los' in template.init_kwargs and template.stored_class_name in ['Item',
                                                                                                  'ItemCharges',
                                                                                                  'ItemRangedWeapon',
                                                                                                  'ItemShield']:
                        del template.init_kwargs['blocks_los']
                        f = open(file_path, 'w')
                        f.write(jsonpickle.dumps(template))
                        f.close()
                    entity_dict[template.data_id] = template

                except:
                    print('Oops! Something is wrong with ' + file)


def get_entity(data_id, add_kwargs=None):
    """
    Function that returns entity template by ID
    :param data_id: ID of the template
    :param add_kwargs: dict of kwargs to add or update, if needed
    :return: Entity object
    """
    return entity_dict[data_id].get_stored_object(add_kwargs)


def get_ability(data_id):
    """ Function that returns ability by AbilityTemplate ID """
    return ability_dict[data_id].get_stored_object()


def get_tile(tile_id):
    """ Function that returns entity template by ID """
    return tile_dict[tile_id]


def get_item_from_loot_list(list_name):
    """
        Function that returns item from loot list (random item, based on weights in list)
        Supports recursion - loot list can be supplied instead of item ID
    """
    if list_name == 'None':
        return None
    file = open('data/loot_lists/' + list_name + '.json', 'r')  # load and decode loot list
    loot_list = jsonpickle.loads(file.read())
    file.close()
    chosen = game_logic.weighted_choice(loot_list)
    if chosen == 'None':  # None string can be supplied to return no item
        chosen_item = None
    elif chosen[0:5] == 'list_':  # if chosen is another list - choose from it
        chosen_item = get_item_from_loot_list(chosen[5:])  # <--- recursion here!
    elif chosen[0:4] == 'qty_':  # if items quantity specified - now only for ItemCharges
        min_qty = int(chosen[chosen.find('(')+1:chosen.find(';')])
        max_qty = int(chosen[chosen.find(';')+1:chosen.find(')')])
        quantity = random.randint(min_qty, max_qty)
        chosen_item = get_entity(chosen[chosen.find(')')+1:])
        chosen_item.charges = quantity  # item must be ItemCharges
    else:
        chosen_item = get_entity(chosen)
    return chosen_item


def get_entity_from_spawn_list(list_name):
    """
        Function that returns entity from spawn list (random entity, based on weights in list)
        Supports recursion - entity spawn can be supplied instead of entity ID
    """
    if list_name == 'None':
        return None
    file = open('data/entity_spawns/' + list_name + '.json', 'r')  # load and decode entity list
    entity_list = jsonpickle.loads(file.read())
    file.close()
    chosen = game_logic.weighted_choice(entity_list)
    if chosen == 'None':  # None string can be supplied to return no entity
        chosen_entity = None
    elif chosen[0:5] == 'list_':  # if chosen is another list - choose from it
        chosen_entity = get_entity_from_spawn_list(chosen[5:])  # <--- recursion here!
    elif chosen[0:4] == 'qty_':  # if entity quantity specified - return list of entities
        min_qty = int(chosen[chosen.find('(')+1:chosen.find(';')])
        max_qty = int(chosen[chosen.find(';')+1:chosen.find(')')])
        quantity = random.randint(min_qty, max_qty)
        i = 0
        chosen_entity = []
        while i < quantity:
            chosen_entity.append(get_entity(chosen[chosen.find(')')+1:]))
            i += 1
        if len(chosen_entity) == 0:  # if no entities in list - return None instead of empty list
            chosen_entity = None
    else:
        chosen_entity = get_entity(chosen)
    return chosen_entity  # can be single Entity or list

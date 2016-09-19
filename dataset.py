"""
    This file contains functions to work with data - saved templates for Entities and so on.
"""
import game_logic
import effects
import abilities
import events

import pickle
import jsonpickle

data_set = {}  # a dict containing all entity templates by string ID's
tile_set = {}  # a dict that contains tile info


def initialize():
    """ Function that loads entity templates to data_set """
    # loading tileset
    tile_set.update(jsonpickle.loads(open("data/tileset.json", 'r').read()))
    # TODO: make Entities load from JSON
    # loading Entity templates
    data_set['wall_sandstone'] = game_logic.Prop(name='Wall', data_id='wall_sandstone', description='A sandstone wall.',
                                                 char='#', color=[255, 250, 205], hp=100, weight=1000)
    data_set['window_small_sandstone'] = game_logic.Prop(name='Small window', data_id='window_small_sandstone',
                                                         occupies_tile=True, blocks_los=False, blocks_shots=0.15,
                                                         description='A hole in sandstone wall.',
                                                         char='"', color=[255, 250, 205], hp=100, weight=800)
    data_set['window_large_sandstone'] = game_logic.Prop(name='Large window', data_id='window_large_sandstone',
                                                         occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                         pass_cost=2,
                                                         description='A large window in sandstone wall.',
                                                         char='_', color=[255, 250, 205], hp=100, weight=800)
    data_set['door_wooden'] = game_logic.Door(name='Door', data_id='door_wooden', description='A wooden door.',
                                              char_closed='+', char_open='.', color=[128, 0, 0],
                                              hp=100, is_closed=True, weight=50)
    data_set['item_boulder'] = game_logic.Item(name='item_boulder', data_id='item_boulder',
                                               description='A stone boulder.', categories={'rubbish'},
                                               char='*', color=[200, 200, 200], weight=10)
    data_set['item_healing_potion'] = game_logic.ItemCharges(name='healing potion', data_id='item_healing_potion',
                                                             description='A potion that heals 5 HP.',
                                                             categories={'consumable', 'potion'}, char='!',
                                                             color=[255, 0, 0],
                                                             charges=1, destroyed_after_use=True, weight=0.2)
    data_set['item_healing_potion'].effects.append(effects.Effect('HEAL', 5))
    data_set['item_sabre'] = game_logic.Item(name='sabre', data_id='item_sabre',
                                             description='A sharp sabre with pointy tip.',
                                             categories={'weapon', 'sword'},
                                             properties={'slashing': (4, 6), 'attack_speed_mod': 1},
                                             char='/', color=[200, 200, 255], weight=2)
    data_set['item_barbed_loincloth'] = game_logic.Item(name='barbed loincloth', data_id='item_barbed_loincloth',
                                                        description='It is covered in spikes. Ouch!',
                                                        categories={'armor', 'waist'}, char='~', color=[200, 0, 100],
                                                        equip_slots={'WAIST'}, weight=0.5)
    cond = abilities.Condition('EQUIPPED')
    react = {'type': 'deal_damage', 'target': 'attacker', 'damage': 1, 'dmg_type': 'piercing'}
    abil = abilities.Ability(name='Barbs', owner=data_set['item_barbed_loincloth'],
                             trigger='damaged', conditions=[cond], reactions=[react])
    data_set['item_barbed_loincloth'].add_ability(abil)

    data_set['item_misurka'] = game_logic.Item(name='misurka', data_id='item_misurka',
                                               description='A light iron helmet with spike on top.',
                                               categories={'armor'},
                                               properties={'armor_bashing': 100, 'armor_slashing': 80,
                                                           'armor_piercing': 60},
                                               char=']', color=[50, 50, 200], equip_slots={'HEAD'}, weight=1)
    data_set['item_mail_armor'] = game_logic.Item(name='mail armor', data_id='item_mail_armor',
                                                  description='A light armor made of overlapping layers of metal rings.',
                                                  categories={'armor'},
                                                  properties={'armor_bashing': 60, 'armor_slashing': 120,
                                                              'armor_piercing': 60},
                                                  char=']', color=[50, 50, 200], equip_slots={'BODY'}, weight=5)
    data_set['item_iron_pauldrons'] = game_logic.Item(name='iron pauldrons', data_id='item_iron_pauldrons',
                                                      description='A pair of iron pauldrons.',
                                                      categories={'armor'},
                                                      properties={'armor_bashing': 100, 'armor_slashing': 120,
                                                                  'armor_piercing': 100},
                                                      char=']', color=[50, 50, 200], equip_slots={'SHOULDERS'}, weight=2)
    data_set['item_iron_boots'] = game_logic.Item(name='iron_boots', data_id='item_iron_boots',
                                                  description='A pair of iron greaves.',
                                                  categories={'armor'},
                                                  properties={'armor_bashing': 100, 'armor_slashing': 120,
                                                              'armor_piercing': 100},
                                                  char=']', color=[50, 50, 200], equip_slots={'FEET'}, weight=2.5)
    data_set['item_iron_armguards'] = game_logic.Item(name='iron armguards', data_id='item_iron_armguards',
                                                      description='A pair of iron armguards.',
                                                      categories={'armor'},
                                                      properties={'armor_bashing': 100, 'armor_slashing': 120,
                                                                  'armor_piercing': 100},
                                                      char=']', color=[50, 50, 200], equip_slots={'ARMS'}, weight=2)
    data_set['item_mail_leggings'] = game_logic.Item(name='mail leggings', data_id='item_mail_leggings',
                                                     description='A pair of mail leggings.',
                                                     categories={'armor'},
                                                     properties={'armor_bashing': 60, 'armor_slashing': 120,
                                                                 'armor_piercing': 60},
                                                     char=']', color=[50, 50, 200], equip_slots={'LEGS'}, weight=4)
    data_set['item_dagger'] = game_logic.Item(name='dagger', data_id='item_dagger',
                                              description='A dagger about 20cm long.',
                                              categories={'weapon', 'dagger'},
                                              properties={'piercing': (1, 4), 'attack_speed_mod': 0.75},
                                              char=',', color=[200, 200, 255], weight=0.5)
    data_set['item_bronze_maul'] = game_logic.Item(name='bronze maul', data_id='item_bronze_maul',
                                                   description='A huge bronze sphere ot top of wooden pole.',
                                                   categories={'weapon', 'blunt'},
                                                   properties={'bashing': (8, 12), 'attack_speed_mod': 1.5},
                                                   char='/', color=[80, 50, 20], weight=10)
    data_set['item_hunting_crossbow'] = game_logic.ItemRangedWeapon(name='hunting crossbow',
                                                                    data_id='item_hunting_crossbow',
                                                                    description='A small crossbow.',
                                                                    range=14, ammo_type='bolt',
                                                                    categories={'weapon', 'blunt', 'crossbow'},
                                                                    properties={'bashing': (1, 3),
                                                                                'attack_speed_mod': 1.5},
                                                                    char=')', color=[200, 200, 200], weight=3)
    data_set['item_hunting_crossbow'].effects.append(effects.Effect('INCREASE_RANGED_DAMAGE', 4))
    data_set['item_bronze_bolt'] = game_logic.ItemCharges(name='bronze bolt', data_id='item_bronze_bolt',
                                                          description='A simple bronze bolt for crossbows.',
                                                          categories={'bolt', 'stackable'},
                                                          properties={'piercing': (1, 4)},
                                                          char='=', color=[80, 50, 20],
                                                          charges=5, destroyed_after_use=True, weight=0.2)
    data_set['mob_mindless_body'] = game_logic.Fighter(name='Mindless body', data_id='mob_mindless_body',
                                                       description='No description, normal debug monster.', char='b',
                                                       color=[109, 49, 9], hp=5, speed=100, sight_radius=14.5, damage=1,
                                                       dmg_type='bashing', ai=game_logic.SimpleMeleeChaserAI(),
                                                       weight=60)
    data_set['mob_scorpion'] = game_logic.Fighter(name='Scorpion', data_id='mob_scorpion',
                                                  description='No description, normal debug monster.', char='s',
                                                  color=[5, 5, 5], hp=3, speed=100, sight_radius=14.5, damage=3,
                                                  dmg_type='piercing', ai=game_logic.SimpleMeleeChaserAI(), weight=15)
    data_set['mob_rakshasa'] = game_logic.Fighter(name='Rakshasa', data_id='mob_rakshasa',
                                                  description='No description, fast debug monster.', char='R',
                                                  color=[255, 127, 80], hp=8, speed=80, sight_radius=18.5, damage=4,
                                                  dmg_type='slashing', ai=game_logic.SimpleMeleeChaserAI(), weight=70)
    data_set['mob_sand_golem'] = game_logic.Fighter(name='Sand golem', data_id='mob_sand_golem',
                                                    description='No description, slow debug monster.', char='S',
                                                    color=[255, 255, 0], hp=20, speed=200, sight_radius=9.5, damage=8,
                                                    dmg_type='bashing', ai=game_logic.SimpleMeleeChaserAI(), weight=300)

    events.Observer.clear()  # remove events made during init of Entities - A HACK


def get_entity(data_id):
    """ Function that returns entity template by ID """
    return pickle.loads(pickle.dumps(data_set[data_id]))  # return pickle copy of Entity template


def get_tile(tile_id):
    """ Function that returns entity template by ID """
    return tile_set[tile_id]

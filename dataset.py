"""
    This file contains functions to work with data - saved templates for Entities and so on.
"""
import game_logic
import effects
import abilities
import events

import random
import pickle

import simplejson
import jsonpickle

data_set = {}  # dict containing all entity templates by string ID's - OBSOLETE
tile_dict = {}  # dict that contains tile info
ability_dict = {}  # dict containing ability templates
entity_dict = {}  # dict containing entity templates


def initialize():
    """ Function that loads entity templates to data_set """
    # loading tileset
    tile_dict.update(jsonpickle.loads(open("data/tileset.json", 'r').read()))
    # TODO: make Entities load from JSON
    # loading Entity templates
    ent_template = game_logic.EntityTemplate(data_id='wall_sandstone', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 30),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Wall', 'description': 'A sandstone wall.',
                                                 'armor': {'bashing': 100, 'slashing': 500, 'piercing': 300},
                                                 'char': '#', 'color': [255, 250, 205], 'hp': 100, 'weight': 1000,
                                                 'corpse': 'debris_large_sandstone'})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='window_small_sandstone', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 30),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Small window',
                                                          'occupies_tile': True, 'blocks_los': False,
                                                          'blocks_shots': 0.15,
                                                          'armor': {'bashing': 100, 'slashing': 500, 'piercing': 300},
                                                          'description': 'A hole in sandstone wall.',
                                                          'char': '"', 'color': [255, 250, 205], 'hp': 100, 'weight': 800,
                                                          'corpse': 'debris_large_sandstone'})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='window_large_sandstone', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 30),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Large window',
                                                          'occupies_tile': False, 'blocks_los': False, 'blocks_shots': 0,
                                                          'armor': {'bashing': 100, 'slashing': 500, 'piercing': 300},
                                                          'pass_cost': 2,
                                                          'description': 'A large window in sandstone wall.',
                                                          'char': '_', 'color': [255, 250, 205], 'hp': 100, 'weight': 800,
                                                          'corpse': 'debris_large_sandstone'})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='debris_large_sandstone', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 30),
                                                   effects.Effect('BLOCK_SLASHING', 30),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Pile of sandstone blocks',
                                                          'occupies_tile': False, 'blocks_los': False, 'blocks_shots': 0,
                                                          'armor': {'bashing': 300, 'slashing': 500, 'piercing': 300},
                                                          'pass_cost': 2,
                                                          'description': 'A collapsed structure, like wall or pillar.',
                                                          'char': '&', 'color': [255, 250, 205], 'hp': 200, 'weight': 800})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='debris_large_wooden', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 20),
                                                   effects.Effect('BLOCK_SLASHING', 20),
                                                   effects.Effect('BLOCK_PIERCING', 20)],
                                             init_kwargs={'name': 'Pile of wooden debris',
                                                      'occupies_tile': False,'blocks_los': False, 'blocks_shots': 0,
                                                      'armor': {'bashing': 200, 'slashing': 200, 'piercing': 200},
                                                      'pass_cost': 2,
                                                      'description': 'Large destroyed wooden furniture.',
                                                      'char': '&', 'color': [128, 0, 0], 'hp': 200, 'weight': 50})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='furn_wooden_board', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 10),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Wooden board',
                                                          'occupies_tile': False, 'blocks_los': False, 'blocks_shots': 0.25,
                                                          'armor': {'bashing': 200, 'slashing': 100, 'piercing': 300},
                                                          'pass_cost': 2,
                                            'description': 'Wooden wagon board. Provides small cover from projectiles.',
                                                    'char': '▧', 'color': [128, 0, 0], 'hp': 100, 'weight': 100})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='furn_wooden_wheel', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 10),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Wooden wheel',
                                                    'occupies_tile': False, 'blocks_los': False, 'blocks_shots': 0.15,
                                                    'armor': {'bashing': 200, 'slashing': 100, 'piercing': 300},
                                                    'pass_cost': 2,
                                            'description': 'Wooden wagon wheel. Provides small cover from projectiles.',
                                                    'char': 'o', 'color': [128, 0, 0], 'hp': 100, 'weight': 70})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='furn_wooden_counter', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 10),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Wooden counter',
                                                      'occupies_tile': False, 'blocks_los': False, 'blocks_shots': 0.25,
                                                      'armor': {'bashing': 200, 'slashing': 100, 'piercing': 300},
                                                      'pass_cost': 2,
                                            'description': 'Wooden counter. Provides small cover from projectiles.',
                                                      'char': 'ʭ', 'color': [128, 0, 0], 'hp': 50, 'weight': 50})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    ent_template = game_logic.EntityTemplate(data_id='furn_wooden_table', stored_class_name='Prop',
                                             effs=[effects.Effect('BLOCK_BASHING', 10),
                                                   effects.Effect('BLOCK_SLASHING', 10),
                                                   effects.Effect('BLOCK_PIERCING', 30)],
                                             init_kwargs={'name': 'Wooden table',
                                                    'data_id': 'furn_wooden_table',
                                                    'occupies_tile': False, 'blocks_los': False, 'blocks_shots': 0.25,
                                                    'armor': {'bashing': 200, 'slashing': 100, 'piercing': 300},
                                                    'pass_cost': 2,
                                                    'description': 'Wooden table. Provides small cover from projectiles.',
                                                    'char': '■', 'color': [128, 0, 0], 'hp': 50, 'weight': 50})
    entity_dict[ent_template.data_id] = ent_template
    data_set[ent_template.data_id] = ent_template.get_stored_object()

    data_set['furn_stone_table'] = game_logic.Prop(name='Stone table',
                                                   data_id='furn_stone_table',
                                                   occupies_tile=False, blocks_los=False, blocks_shots=0.25,
                                                   armor={'bashing': 200, 'slashing': 200, 'piercing': 300},
                                                   pass_cost=2,
                                                   description='Stone table. Provides small cover from projectiles.',
                                                   char='■', color=[150, 150, 150], hp=100, weight=150)
    data_set['furn_stone_table'].effects.append(effects.Effect('BLOCK_BASHING', 20))
    data_set['furn_stone_table'].effects.append(effects.Effect('BLOCK_SLASHING', 20))
    data_set['furn_stone_table'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['furn_rusty_anvil'] = game_logic.Prop(name='Rusty anvil',
                                                   data_id='furn_rusty_anvil',
                                                   occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                   armor={'bashing': 500, 'slashing': 500, 'piercing': 500},
                                                   pass_cost=2,
                                                   description='An anvil, dirty and covered in rust.',
                                                   char='▼', color=[225, 200, 200], hp=250, weight=150)
    data_set['furn_rusty_anvil'].effects.append(effects.Effect('BLOCK_BASHING', 50))
    data_set['furn_rusty_anvil'].effects.append(effects.Effect('BLOCK_SLASHING', 50))
    data_set['furn_rusty_anvil'].effects.append(effects.Effect('BLOCK_PIERCING', 50))

    data_set['furn_iron_grate'] = game_logic.Prop(name='Iron grate',
                                                  data_id='furn_iron_grate',
                                                  occupies_tile=True, blocks_los=False, blocks_shots=0.25,
                                                  armor={'bashing': 100, 'slashing': 200, 'piercing': 300},
                                                  description='A grate made of iron, too tight for man to pass through.',
                                                  char='‡', color=[200, 200, 225], hp=50, weight=100)
    data_set['furn_iron_grate'].effects.append(effects.Effect('BLOCK_BASHING', 10))
    data_set['furn_iron_grate'].effects.append(effects.Effect('BLOCK_SLASHING', 20))
    data_set['furn_iron_grate'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['furn_furnace'] = game_logic.Prop(name='Furnace',
                                               data_id='furn_furnace',
                                               occupies_tile=True, blocks_los=True,
                                               armor={'bashing': 200, 'slashing': 200, 'piercing': 300},
                                               description='Device for heating, made with heavy stone blocks.',
                                               char='◘', color=[150, 150, 150], hp=200, weight=500)
    data_set['furn_furnace'].effects.append(effects.Effect('BLOCK_BASHING', 20))
    data_set['furn_furnace'].effects.append(effects.Effect('BLOCK_SLASHING', 20))
    data_set['furn_furnace'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['trap_corrosive_moss'] = game_logic.Prop(name='Corrosive moss', data_id='trap_corrosive_moss',
                                                      occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                      armor={'bashing': 300, 'slashing': 50, 'piercing': 300},
                                                      pass_cost=1,
                                                      description='A large patch of green acid-dripping moss.',
                                                      char='_', color=[100, 220, 100], hp=30, weight=10)
    data_set['trap_corrosive_moss'].effects.append(effects.Effect('BLOCK_BASHING', 30))
    data_set['trap_corrosive_moss'].effects.append(effects.Effect('BLOCK_SLASHING', 2))
    data_set['trap_corrosive_moss'].effects.append(effects.Effect('BLOCK_PIERCING', 30))
    cond1 = abilities.Condition('MOVED_ON')
    cond2 = abilities.Condition('MOVER_IS_A_BE')
    react = {'type': 'deal_damage', 'target': 'mover', 'damage': (1, 3), 'dmg_type': 'acid'}
    a_t = abilities.AbilityTemplate(data_id='corrosive_acid',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Corrosive acid',
                                                 'trigger': 'entity_moved',
                                                 'conditions': [cond1, ' and ', cond2],
                                                 'reactions': [react],
                                                 'message_color': [100, 220, 100]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['trap_corrosive_moss'].add_ability(abil)

    data_set['door_wooden'] = game_logic.Door(name='Door', data_id='door_wooden', description='A wooden door.',
                                              char_closed='+', char_open='.', color=[128, 0, 0],
                                              armor={'bashing': 200, 'slashing': 100, 'piercing': 300},
                                              hp=100, is_closed=True, weight=50,
                                              corpse='debris_large_wooden')
    data_set['door_wooden'].effects.append(effects.Effect('BLOCK_BASHING', 10))
    data_set['door_wooden'].effects.append(effects.Effect('BLOCK_SLASHING', 10))
    data_set['door_wooden'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['item_ancient_coin'] = game_logic.ItemCharges(name='ancient coin',
                                                           data_id='item_ancient_coin',
                                                           description='An ancient coin.',
                                                           categories={'relic', 'stackable', 'weight_per_charge'},
                                                           properties={'value': 1},
                                                           char='$', color=[255, 20, 147],
                                                           charges=1, destroyed_after_use=True, weight=0.01)

    data_set['item_ancient_scroll'] = game_logic.ItemCharges(name='ancient scroll',
                                                             data_id='item_ancient_scroll',
                                                             description='Ancient scroll, with some writing in it.',
                                                             categories={'relic', 'scroll', 'stackable',
                                                                         'weight_per_charge'},
                                                             properties={'value': 5},
                                                             char='?', color=[255, 20, 147],
                                                             charges=1, destroyed_after_use=True, weight=0.1)

    data_set['item_ancient_clay_tablet'] = game_logic.ItemCharges(name='clay tablet',
                                                                  data_id='item_ancient_clay_tablet',
                                description='Clay tablet, with some writing or picture in it.',
                                                                  categories={'relic', 'stackable', 'weight_per_charge'},
                                                                  properties={'value': 15},
                                                                  char='æ', color=[255, 20, 147],
                                                                  charges=1, destroyed_after_use=True, weight=1)

    data_set['item_ancient_pottery'] = game_logic.ItemCharges(name='ancient pottery',
                                                              data_id='item_ancient_pottery',
                                                description='Ancient jar, or pot, with some pictures or engravings.',
                                                              categories={'relic', 'stackable', 'weight_per_charge'},
                                                              properties={'value': 15},
                                                              char='§', color=[255, 20, 147],
                                                              charges=1, destroyed_after_use=True, weight=1)

    data_set['item_ancient_ring'] = game_logic.Item(name='ancient ring', data_id='item_ancient_scroll',
                                                    description='Ancient ring.',
                                                    categories={'relic', 'ring'},
                                                    properties={'value': 25}, equip_slots={'RIGHT_RING', 'LEFT_RING'},
                                                    char='˚', color=[255, 20, 147], weight=0.1)

    data_set['item_ancient_necklace'] = game_logic.Item(name='ancient necklace', data_id='item_ancient_necklace',
                                                        description='Ancient necklace.',
                                                        categories={'relic', 'ring'},
                                                        properties={'value': 30}, equip_slots={'RIGHT_RING', 'LEFT_RING'},
                                                        char='ˠ', color=[255, 20, 147], weight=0.1)

    data_set['item_boulder'] = game_logic.Item(name='item_boulder', data_id='item_boulder',
                                               description='A stone boulder.', categories={'rubbish'},
                                               char='*', color=[200, 200, 200], weight=10)

    data_set['item_adventurer_corpse'] = game_logic.Item(name="adventurer's corpse", data_id='item_adventurer_corpse',
                                                         description='A dead body of adventurer, not so lucky as you.',
                                                         categories={'corpse'},
                                                         char='%', color=[200, 0, 0], weight=70)

    data_set['item_skeleton'] = game_logic.Item(name="human skeleton", data_id='item_skeleton',
                                                description='Human skeleton.',
                                                categories={'corpse'},
                                                char='%', color=[255, 255, 255], weight=10)

    data_set['item_horse_skeleton'] = game_logic.Item(name="horse skeleton", data_id='item_horse_skeleton',
                                                      description='Horse skeleton.',
                                                      categories={'corpse'},
                                                      char='%', color=[255, 255, 255], weight=80)

    data_set['item_haste_potion'] = game_logic.ItemCharges(name='haste potion', data_id='item_haste_potion',
                                                           description='A potion that hastens user by 50%.',
                                                           categories={'consumable', 'potion'},
                                                           properties={'value': 120,
                                                                       'usable': 'self'},
                                                           char='!', color=[255, 215, 0],
                                                           charges=1, destroyed_after_use=True, weight=0.2)
    cond = abilities.Condition('USED')
    react = {'type': 'apply_timed_effect', 'target': 'default', 'time': 1000, 'effect': effects.Effect('HASTE', 50)}
    a_t = abilities.AbilityTemplate(data_id='haste',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Haste', 'trigger': 'used_on_self',
                                                 'conditions': [cond], 'reactions': [react],
                                                    'message_color': [255, 215, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_haste_potion'].add_ability(abil)

    data_set['item_antidote_potion'] = game_logic.ItemCharges(name='antidote potion', data_id='item_antidote_potion',
                    description='A potion that cures all poison effects, and protects from poison for a short time.',
                                                              categories={'consumable', 'potion'},
                                                              properties={'value': 40,
                                                                          'usable': 'self'},
                                                              char='!', color=[0, 150, 0],
                                                              charges=1, destroyed_after_use=True, weight=0.2)
    cond = abilities.Condition('USED')
    react1 = {'type': 'remove_effect', 'target': 'default', 'effect': effects.Effect('POISONED', 0),
              'effects_number': 'all'}
    react2 = {'type': 'apply_timed_effect', 'target': 'default', 'time': 500,
              'effect': effects.Effect('RESIST_POISON', 500)}
    a_t = abilities.AbilityTemplate(data_id='antidote',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Antidote', 'trigger': 'used_on_self',
                                                 'conditions': [cond], 'reactions': [react1, react2],
                                                    'message_color': [0, 150, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_antidote_potion'].add_ability(abil)

    data_set['item_lightning_scroll'] = game_logic.ItemCharges(name='scroll of Lightning', data_id='item_lightning_scroll',
                                                    description='A scroll that calls a lightning strike on enemy.',
                                                               categories={'consumable', 'scroll'},
                                                               properties={'usable': 'battle_entity', 'range': 15,
                                                                           'value': 175},
                                                               char='?', color=[255, 215, 0],
                                                               charges=1, destroyed_after_use=True, weight=0.1)
    cond = abilities.Condition('USED')
    react = {'type': 'deal_damage', 'target': 'default', 'damage': (10, 30), 'dmg_type': 'lightning'}
    a_t = abilities.AbilityTemplate(data_id='lightning',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Lightning',
                                            'trigger': 'used_on_target', 'conditions': [cond], 'reactions': [react],
                                            'message_color': [255, 215, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_lightning_scroll'].add_ability(abil)

    data_set['item_firebolt_scroll'] = game_logic.ItemCharges(name='scroll of Firebolt',
                                                              data_id='item_firebolt_scroll',
                                                              description='A scroll that hurls a firebolt at enemy.',
                                                              categories={'consumable', 'scroll'},
                                                              properties={'usable': 'battle_entity_or_point',
                                                                          'range': 15,
                                                                          'use_time_coef': 1,
                                                                          'use_time_offset': 0.7,
                                                                          'value': 125},
                                                              char='?', color=[255, 0, 0],
                                                              charges=1, destroyed_after_use=True, weight=0.1)
    cond = abilities.Condition('USED')
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=20, power=15, target=None, name='firebolt',
                                         description='An arrow of pure flame.', char='*', color=[255, 0, 0])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (3, 6), 'dmg_type': 'fire'}
    a_t = abilities.AbilityTemplate(data_id='ignite',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Ignite', 'trigger': 'projectile_hit',
                                    'conditions': [], 'reactions': [react],
                                        'message_color': [255, 0, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    proj.add_ability(abil)
    data_set['proj_firebolt'] = proj
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'default',  'projectile': 'proj_firebolt'}
    a_t = abilities.AbilityTemplate(data_id='firebolt',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Firebolt',
                                                'trigger': 'used_on_target', 'conditions': [cond], 'reactions': [react],
                                                'message_color': [255, 0, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_firebolt_scroll'].add_ability(abil)

    data_set['item_frostbolt_scroll'] = game_logic.ItemCharges(name='scroll of Frostbolt',
                                                               data_id='item_frostbolt_scroll',
                                                               description='A scroll that hurls a frostbolt at enemy.',
                                                               categories={'consumable', 'scroll'},
                                                               properties={'usable': 'battle_entity_or_point',
                                                                           'range': 15,
                                                                           'use_time_coef': 1,
                                                                           'use_time_offset': 0.7,
                                                                           'value': 135},
                                                               char='?', color=[100, 100, 255],
                                                               charges=1, destroyed_after_use=True, weight=0.1)
    cond = abilities.Condition('USED')
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=20, power=15, target=None, name='frostbolt',
                                         description='An arrow of freezing energy.', char='*', color=[100, 100, 255])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (3, 6), 'dmg_type': 'cold'}
    a_t = abilities.AbilityTemplate(data_id='freeze',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Freeze', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [100, 100, 255]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    proj.add_ability(abil)
    data_set['proj_frostbolt'] = proj
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'default', 'projectile': 'proj_frostbolt'}
    a_t = abilities.AbilityTemplate(data_id='frostbolt',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Frostbolt',
                                                 'trigger': 'used_on_target', 'conditions': [cond],
                                                 'reactions': [react],
                                                 'message_color': [100, 100, 255]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_frostbolt_scroll'].add_ability(abil)

    data_set['item_healing_potion'] = game_logic.ItemCharges(name='healing potion', data_id='item_healing_potion',
                                                             description='A potion that heals 5 HP.',
                                                             categories={'consumable', 'potion'},
                                                             properties={'value': 30,
                                                                         'usable': 'self'},
                                                             char='!', color=[255, 0, 0],
                                                             charges=1, destroyed_after_use=True, weight=0.2)
    cond = abilities.Condition('USED')
    react = {'type': 'heal', 'target': 'default', 'heal': 5}
    a_t = abilities.AbilityTemplate(data_id='heal_potion',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Heal', 'trigger': 'used_on_self',
                                                 'conditions': [cond], 'reactions': [react],
                                                    'message_color': [0, 255, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_healing_potion'].add_ability(abil)

    data_set['item_barbed_loincloth'] = game_logic.Item(name='barbed loincloth', data_id='item_barbed_loincloth',
                                                        description='It is covered in spikes. Ouch!',
                                                        categories={'armor', 'waist'}, char='~', color=[200, 0, 100],
                                                        equip_slots={'WAIST'}, weight=0.5)
    cond = abilities.Condition('EQUIPPED')
    react = {'type': 'deal_damage', 'target': 'default', 'strike_type': 'melee',
             'damage': 1, 'dmg_type': 'piercing'}
    a_t = abilities.AbilityTemplate(data_id='barbs',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Barbs', 'trigger': 'damaged',
                                                 'conditions': [cond], 'reactions': [react],
                                                    'message_color': [200, 0, 100]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_barbed_loincloth'].add_ability(abil)

    data_set['item_ring_poison_res'] = game_logic.Item(name='ring of poison resistance', data_id='item_ring_poison_res',
                                                       description='Ring that grants protection from poison.',
                                                       categories={'ring'}, equip_slots={'RIGHT_RING', 'LEFT_RING'},
                                                       properties={'value': 350},
                                                       char='˚', color=[0, 100, 0],
                                                       weight=0.1)
    data_set['item_ring_poison_res'].effects.append(effects.Effect('RESIST_POISON', 100))

    data_set['item_ring_fire_res'] = game_logic.Item(name='ring of fire resistance', data_id='item_ring_fire_res',
                                                     description='Ring that grants protection from fire.',
                                                     categories={'ring'}, equip_slots={'RIGHT_RING', 'LEFT_RING'},
                                                     properties={'value': 400},
                                                     char='˚', color=[180, 0, 0],
                                                     weight=0.1)
    data_set['item_ring_fire_res'].effects.append(effects.Effect('RESIST_FIRE', 100))

    data_set['item_ring_cold_res'] = game_logic.Item(name='ring of cold resistance', data_id='item_ring_cold_res',
                                                     description='Ring that grants protection from cold.',
                                                     categories={'ring'}, equip_slots={'RIGHT_RING', 'LEFT_RING'},
                                                     properties={'value': 400},
                                                     char='˚', color=[0, 0, 150],
                                                     weight=0.1)
    data_set['item_ring_cold_res'].effects.append(effects.Effect('RESIST_COLD', 100))

    data_set['item_ring_lightning_res'] = game_logic.Item(name='ring of lightning resistance',
                                                          data_id='item_ring_lightning_res',
                                                          description='Ring that grants protection from lightning.',
                                                          categories={'ring'}, equip_slots={'RIGHT_RING', 'LEFT_RING'},
                                                          properties={'value': 400},
                                                          char='˚', color=[255, 215, 0],
                                                          weight=0.1)
    data_set['item_ring_lightning_res'].effects.append(effects.Effect('RESIST_LIGHTNING', 100))

    data_set['item_wooden_buckler'] = game_logic.ItemShield(name='wooden buckler', data_id='item_wooden_buckler',
                                                            description='A light wooden shield.', durability=10,
                                                            categories={'shield'},
                                                            properties={'value': 75,
                                                                        'armor_bashing': 50, 'armor_slashing': 100,
                                                                        'armor_piercing': 150,
                                                                        'block_bashing': 3, 'block_slashing': 6,
                                                                        'block_piercing': 10},
                                                            char='(', color=[128, 0, 0], weight=4)

    # set of iron armor=====================================================
    data_set['item_misurka'] = game_logic.Item(name='misurka', data_id='item_misurka',
                                               description='A light iron helmet with spike on top.',
                                               categories={'armor'},
                                               properties={'armor_bashing': 100, 'armor_slashing': 80,
                                                           'armor_piercing': 60, 'value': 300},
                                               char='ˀ', color=[50, 50, 200], equip_slots={'HEAD'}, weight=1)

    data_set['item_mail_armor'] = game_logic.Item(name='mail armor', data_id='item_mail_armor',
                                                  description='An armor made of overlapping layers of metal rings.',
                                                  categories={'armor'},
                                                  properties={'armor_bashing': 60, 'armor_slashing': 120,
                                                              'armor_piercing': 60, 'value': 500},
                                                  char=']]', color=[50, 50, 200], equip_slots={'BODY'}, weight=5)

    data_set['item_iron_pauldrons'] = game_logic.Item(name='iron pauldrons', data_id='item_iron_pauldrons',
                                                      description='A pair of iron pauldrons.',
                                                      categories={'armor'},
                                                      properties={'armor_bashing': 100, 'armor_slashing': 120,
                                                                  'armor_piercing': 100, 'value': 350},
                                                      char=']]', color=[50, 50, 200], equip_slots={'SHOULDERS'},
                                                      weight=2)

    data_set['item_iron_boots'] = game_logic.Item(name='iron boots', data_id='item_iron_boots',
                                                  description='A pair of iron greaves.',
                                                  categories={'armor'},
                                                  properties={'armor_bashing': 100, 'armor_slashing': 120,
                                                              'armor_piercing': 100, 'value': 300},
                                                  char=']]', color=[50, 50, 200], equip_slots={'FEET'}, weight=2.5)

    data_set['item_iron_armguards'] = game_logic.Item(name='iron armguards', data_id='item_iron_armguards',
                                                      description='A pair of iron armguards.',
                                                      categories={'armor'},
                                                      properties={'armor_bashing': 100, 'armor_slashing': 120,
                                                                  'armor_piercing': 100, 'value': 350},
                                                      char=']]', color=[50, 50, 200], equip_slots={'ARMS'}, weight=2)

    data_set['item_mail_leggings'] = game_logic.Item(name='mail leggings', data_id='item_mail_leggings',
                                                     description='A pair of mail leggings.',
                                                     categories={'armor'},
                                                     properties={'armor_bashing': 60, 'armor_slashing': 120,
                                                                 'armor_piercing': 60, 'value': 400},
                                                     char=']]', color=[50, 50, 200], equip_slots={'LEGS'}, weight=4)
    # set of leather armor =========================================================
    data_set['item_leather_cap'] = game_logic.Item(name='leather cap', data_id='item_leather_cap',
                                                   description='A leather cap offers light protection.',
                                                   categories={'armor'},
                                                   properties={'armor_bashing': 50, 'armor_slashing': 50,
                                                               'armor_piercing': 40, 'value': 90},
                                                   char='ˀ', color=[160, 82, 45], equip_slots={'HEAD'}, weight=0.5)

    data_set['item_leather_armor'] = game_logic.Item(name='leather armor', data_id='item_leather_armor',
                                                     description='A light armor made of leather.',
                                                     categories={'armor'},
                                                     properties={'armor_bashing': 50, 'armor_slashing': 50,
                                                                 'armor_piercing': 40, 'value': 150},
                                                     char=']]', color=[160, 82, 45], equip_slots={'BODY'}, weight=3)

    data_set['item_leather_pauldrons'] = game_logic.Item(name='leather pauldrons', data_id='item_leather_pauldrons',
                                                         description='A pair of leather pauldrons.',
                                                         categories={'armor'},
                                                         properties={'armor_bashing': 50, 'armor_slashing': 50,
                                                                     'armor_piercing': 40, 'value': 100},
                                                         char=']]', color=[160, 82, 45], equip_slots={'SHOULDERS'},
                                                         weight=1.5)

    data_set['item_leather_boots'] = game_logic.Item(name='leather boots', data_id='item_leather_boots',
                                                     description='A pair of leather boots.',
                                                     categories={'armor'},
                                                     properties={'armor_bashing': 50, 'armor_slashing': 50,
                                                                 'armor_piercing': 40, 'value': 80},
                                                     char=']]', color=[160, 82, 45], equip_slots={'FEET'}, weight=2.5)

    data_set['item_leather_armguards'] = game_logic.Item(name='leather armguards', data_id='item_leather_armguards',
                                                         description='A pair of leather armguards.',
                                                         categories={'armor'},
                                                         properties={'armor_bashing': 50, 'armor_slashing': 50,
                                                                     'armor_piercing': 40, 'value': 110},
                                                         char=']]', color=[160, 82, 45], equip_slots={'ARMS'}, weight=1)

    data_set['item_leather_leggings'] = game_logic.Item(name='leather leggings', data_id='item_leather_leggings',
                                                        description='A pair of leather leggings.',
                                                        categories={'armor'},
                                                        properties={'armor_bashing': 50, 'armor_slashing': 50,
                                                                    'armor_piercing': 40, 'value': 120},
                                                        char=']]', color=[160, 82, 45], equip_slots={'LEGS'}, weight=2)
    # WEAPONS
    data_set['item_sabre'] = game_logic.Item(name='sabre', data_id='item_sabre',
                                             description='A sharp sabre with pointy tip.',
                                             categories={'weapon', 'sword'},
                                             properties={'value': 100, 'slashing': (4, 6), 'attack_speed_mod': 1},
                                             char='ϯ', color=[200, 200, 255], weight=2)

    data_set['item_khopesh'] = game_logic.Item(name='khopesh', data_id='item_khopesh',
                                               description='An ancient bronze sickle-sword.',
                                               categories={'weapon', 'sword'},
                                               properties={'slashing': (4, 7), 'attack_speed_mod': 1.05, 'value': 275},
                                               char='ϯ', color=[80, 50, 20], weight=2.5)

    data_set['item_longsword'] = game_logic.Item(name='longsword', data_id='item_longsword',
                                                 description='A double-edged straight sword.',
                                                 categories={'weapon', 'sword'},
                                                 properties={'slashing': (5, 9), 'attack_speed_mod': 1.2, 'value': 450},
                                                 char='ϯ', color=[150, 150, 255], weight=4)

    data_set['item_zweihander'] = game_logic.Item(name='zweihander', data_id='item_zweihander',
                        description='A long and heavy two-handed sword. Slow to swing, but extremely heavy-hitting.',
                                                  categories={'weapon', 'sword'},
                                                  properties={'slashing': (6, 14), 'attack_speed_mod': 1.8,
                                                              'value': 850},
                                                  char='ϯ', color=[150, 150, 175], weight=8)

    data_set['item_tabar'] = game_logic.Item(name='tabar', data_id='item_tabar',
                                             description='Fighting axe, with metal handle suitable for parrying.',
                                             categories={'weapon', 'axe'},
                                             properties={'slashing': (3, 7), 'attack_speed_mod': 1, 'value': 150},
                                             char='г', color=[150, 150, 255], weight=3)

    data_set['item_panabas'] = game_logic.Item(name='panabas', data_id='item_panabas',
                                               description='Long sword-like two-handed axe.',
                                               categories={'weapon', 'axe'},
                                               properties={'slashing': (4, 12), 'attack_speed_mod': 1.5, 'value': 550},
                                               char='Г', color=[150, 150, 255], weight=6)

    data_set['item_dagger'] = game_logic.Item(name='dagger', data_id='item_dagger',
                                              description='A dagger about 20cm long.',
                                              categories={'weapon', 'dagger'},
                                              properties={'piercing': (1, 4), 'attack_speed_mod': 0.75, 'value': 25},
                                              char=',', color=[200, 200, 255], weight=0.5)

    data_set['item_jambiyah'] = game_logic.Item(name='jambiyah', data_id='item_jambiyah',
                                                description='A knife with broad blade, suited for slashing.',
                                                categories={'weapon', 'dagger'},
                                                properties={'slashing': (1, 4), 'attack_speed_mod': 0.75, 'value': 30},
                                                char=',', color=[150, 150, 255], weight=0.5)

    data_set['item_kris'] = game_logic.Item(name='kris', data_id='item_kris',
                                            description='A dagger with flame-like blade.',
                                            categories={'weapon', 'dagger'},
                                            properties={'piercing': (2, 5), 'attack_speed_mod': 0.85, 'value': 90},
                                            char=',', color=[80, 50, 2], weight=0.7)

    data_set['item_assegai'] = game_logic.Item(name='assegai', data_id='item_assegai',
                                               description='Short spear, used for melee combat.',
                                               categories={'weapon', 'spear'},
                                               properties={'piercing': (2, 8), 'attack_speed_mod': 1, 'value': 80},
                                               char=chr(92), color=[128, 0, 0], weight=4)

    data_set['item_mace'] = game_logic.Item(name='mace', data_id='item_mace',
                                            description='A short club with iron head.',
                                            categories={'weapon', 'blunt'},
                                            properties={'bashing': (3, 5), 'attack_speed_mod': 1, 'value': 110},
                                            char='/', color=[128, 0, 0], weight=3)

    data_set['item_bronze_maul'] = game_logic.Item(name='bronze maul', data_id='item_bronze_maul',
                                                   description='A huge bronze sphere ot top of wooden pole.',
                                                   categories={'weapon', 'blunt'},
                                                   properties={'bashing': (8, 12), 'attack_speed_mod': 1.8,
                                                               'value': 420},
                                                   char='/', color=[80, 50, 20], weight=10)

    data_set['item_wall_smasher'] = game_logic.Item(name='wall smasher', data_id='item_wall_smasher',
                                                    description='A test weapon with tremendous power to smash walls.',
                                                    categories={'weapon', 'blunt'},
                                                    properties={'bashing': (150, 300), 'attack_speed_mod': 2},
                                                    char='/', color=[255, 0, 128], weight=15)

    data_set['item_hunting_crossbow'] = game_logic.ItemRangedWeapon(name='hunting crossbow',
                                                                    data_id='item_hunting_crossbow',
                                                                    description='A small crossbow.',
                                                                    range=14, ammo_type='bolt',
                                                                    categories={'weapon', 'blunt', 'crossbow'},
                                                                    properties={'bashing': (1, 3),
                                                                                'attack_speed_mod': 1.5,
                                                                                'accuracy_ranged': 1,
                                                                                'shot_speed': 2,
                                                                                'value': 600},
                                                                    char=')', color=[200, 200, 200], weight=3)
    data_set['item_hunting_crossbow'].effects.append(effects.Effect('INCREASE_RANGED_DAMAGE', 4))

    data_set['item_short_bow'] = game_logic.ItemRangedWeapon(name='short bow',
                                                             data_id='item_short_bow',
                                                             description='Short bow suited for small game hunt.',
                                                             range=10, ammo_type='arrow',
                                                             categories={'weapon', 'blunt', 'bow'},
                                                             properties={'bashing': (1, 2),
                                                                         'attack_speed_mod': 1.1,
                                                                         'accuracy_ranged': 0.9,
                                                                         'shot_speed': 3,
                                                                         'value': 175},
                                                             char='ϡ', color=[128, 0, 0], weight=1.5)
    data_set['item_short_bow'].effects.append(effects.Effect('INCREASE_RANGED_DAMAGE', 1))

    data_set['item_bronze_bolt'] = game_logic.ItemCharges(name='bronze bolt', data_id='item_bronze_bolt',
                                                          description='A simple bronze bolt for crossbows.',
                                                          categories={'bolt', 'stackable', 'weight_per_charge',
                                                                      'sticks_to_target'},
                                                          properties={'value': 10,
                                                                      'piercing': (1, 4), 'break_chance': 0.5},
                                                          char='=', color=[80, 50, 20],
                                                          charges=5, destroyed_after_use=True, weight=0.2)

    data_set['item_bronze_tipped_arrow'] = game_logic.ItemCharges(name='arrow',
                                                                  data_id='item_bronze_tipped_arrow',
                                                                  description='A simple bronze tipped arrow.',
                                                                  categories={'arrow', 'stackable', 'weight_per_charge',
                                                                              'sticks_to_target'},
                                                                  properties={'value': 5,
                                                                              'piercing': (1, 3), 'break_chance': 0.5},
                                                                  char='=', color=[128, 20, 20],
                                                                  charges=5, destroyed_after_use=True, weight=0.1)

    data_set['item_poisoned_arrow'] = game_logic.ItemCharges(name='poisoned arrow',
                                                                  data_id='item_poisoned_arrow',
                                                    description='A simple bronze tipped arrow, coated in weak poison.',
                                                                  categories={'arrow', 'stackable', 'weight_per_charge',
                                                                              'sticks_to_target'},
                                                                  properties={'piercing': (1, 3), 'break_chance': 0.5,
                                                                              'value': 50},
                                                                  char='=', color=[0, 150, 0],
                                                                  charges=3, destroyed_after_use=True, weight=0.1)
    cond1 = abilities.Condition('DEALT_DAMAGE', sign='>', number='0')
    cond2 = abilities.Condition('TARGET_IS_CATEGORY', category='living')
    react = {'type': 'deal_periodic_damage', 'target': 'default', 'damage': (0, 2),
             'dmg_type': 'poison', 'effect': effects.Effect('POISONED', 1), 'period': 1000, 'whole_time': 5000,
             'stackable': False}
    a_t = abilities.AbilityTemplate(data_id='poison_arrow',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Poisoned arrow', 'trigger': 'shot_hit',
                                                 'conditions': [cond1, ' and ', cond2], 'reactions': [react],
                                                 'message_color': [0, 150, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_poisoned_arrow'].add_ability(abil)

    data_set['item_frost_arrow'] = game_logic.ItemCharges(name='frost arrow',
                                                          data_id='item_frost_arrow',
                                                          description='Magical arrow, that deals cold damage and slows target.',
                                                          categories={'arrow', 'stackable', 'weight_per_charge',
                                                                      'sticks_to_target'},
                                                          properties={'cold': (2, 5), 'break_chance': 0.7,
                                                                      'value': 90},
                                                          char='=', color=[100, 100, 255],
                                                          charges=1, destroyed_after_use=True, weight=0.1)
    cond1 = abilities.Condition('DEALT_DAMAGE', sign='>', number='0')
    react = {'type': 'apply_timed_effect', 'target': 'projectile_hit_entity', 'time': 1000,
             'effect': effects.Effect('SLOWED', 200)}
    a_t = abilities.AbilityTemplate(data_id='frost_arrow',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Frost arrow', 'trigger': 'shot_hit',
                                                 'conditions': [cond1], 'reactions': [react],
                                                 'message_color': [100, 100, 255]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_frost_arrow'].add_ability(abil)

    data_set['item_explosive_bolt'] = game_logic.ItemCharges(name='explosive bolt',
                                                             data_id='item_explosive_bolt',
                    description='Crossbow bolt with attached alchemical explosive head.',
                                                             categories={'bolt', 'stackable', 'weight_per_charge',
                                                                         'sticks_to_target'},
                                                             properties={'bashing': (0, 3), 'break_chance': 1,
                                                                         'value': 110},
                                                             char='=', color=[255, 127, 80],
                                                             charges=1, destroyed_after_use=True, weight=0.1)
    react1 = {'type': 'deal_damage_aoe', 'aoe': 'circle', 'radius': 2.5, 'include_center': True,
              'target': 'projectile_hit_entity', 'strike_type': 'projectile',
              'damage': (7, 15), 'dmg_type': 'bashing'}
    react2 = {'type': 'kill_entity', 'target': 'ammo'}
    a_t = abilities.AbilityTemplate(data_id='bolt_explosion',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'BOOM!', 'trigger': 'projectile_hit', 'conditions': [],
                                                 'reactions': [react1, react2], 'message_color': [255, 127, 80]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_explosive_bolt'].add_ability(abil)

    data_set['item_throwing_knife'] = game_logic.ItemCharges(name='throwing knife',
                                                             data_id='item_throwing_knife',
                                                             description='A knife, balanced for quick throwing.',
                                                             categories={'throwing', 'stackable', 'weight_per_charge',
                                                                         'sticks_to_target'},
                                                             properties={'break_chance': 0.3,
                                                                         'throw_speed': 0.75,
                                                                         'accuracy_thrown': 1,
                                                                         'value': 20},
                                                             char="'", color=[110, 110, 110],
                                                             charges=1, destroyed_after_use=True, weight=0.2)
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (1, 3), 'dmg_type': 'piercing'}
    a_t = abilities.AbilityTemplate(data_id='throwing_knife_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Shank', 'trigger': 'projectile_hit', 'conditions': [],
                                                 'reactions': [react],
                                                 'message_color': [255, 255, 255]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_throwing_knife'].add_ability(abil)

    data_set['item_venom_sac'] = game_logic.ItemCharges(name='venom sac',
                                                        data_id='item_venom_sac',
            description='Small sac, full of scorpion venom. Useful alchemical ingredient. If thrown - can deal minor poison damage.',
                                                        categories={'throwing', 'stackable', 'weight_per_charge',
                                                                    'alchemy'},
                                                        properties={'break_chance': 1,
                                                                    'throw_speed': 0.75,
                                                                    'accuracy_thrown': 0.8,
                                                                    'value': 60},
                                                        char="`", color=[0, 230, 0],
                                                        charges=1, destroyed_after_use=True, weight=0.5)
    cond = abilities.Condition('TARGET_IS_CATEGORY', category='living')
    react = {'type': 'deal_damage', 'chance': 70, 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (1, 3), 'dmg_type': 'poison'}
    a_t = abilities.AbilityTemplate(data_id='venom_sac_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Splash!', 'trigger': 'projectile_hit',
                                                 'conditions': [cond], 'reactions': [react],
                                                 'message_color': [0, 150, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_venom_sac'].add_ability(abil)

    data_set['item_sparkling_dust'] = game_logic.ItemCharges(name='sparkling dust',
                                                        data_id='item_sparkling_dust',
                    description='Magical dust, sparkling with tiny lightnings. Useful alchemical ingredient. If thrown - can deal minor lightning damage.',
                                                        categories={'throwing', 'stackable', 'weight_per_charge',
                                                                    'alchemy'},
                                                        properties={'break_chance': 1,
                                                                    'throw_speed': 0.75,
                                                                    'accuracy_thrown': 0.6,
                                                                    'value': 120},
                                                        char="`", color=[255, 215, 0],
                                                        charges=1, destroyed_after_use=True, weight=0.1)
    react = {'type': 'deal_damage', 'chance': 70, 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (1, 3), 'dmg_type': 'lightning'}
    a_t = abilities.AbilityTemplate(data_id='sparkling_dust_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Zap!', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [255, 215, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_sparkling_dust'].add_ability(abil)

    data_set['item_hot_ash'] = game_logic.ItemCharges(name='hot ash',
                                                      data_id='item_hot_ash',
        description='Magical ash, radiating heat. Useful alchemical ingredient. If thrown - can deal minor fire damage.',
                                                      categories={'throwing', 'stackable', 'weight_per_charge',
                                                                  'alchemy'},
                                                      properties={'break_chance': 1,
                                                                  'throw_speed': 0.75,
                                                                  'accuracy_thrown': 0.6,
                                                                  'value': 120},
                                                      char="`", color=[160, 0, 0],
                                                      charges=1, destroyed_after_use=True, weight=0.1)
    react = {'type': 'deal_damage', 'chance': 70, 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (1, 3), 'dmg_type': 'fire'}
    a_t = abilities.AbilityTemplate(data_id='hot_ash_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Ignite', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [255, 215, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_hot_ash'].add_ability(abil)

    data_set['item_magic_snow'] = game_logic.ItemCharges(name='magic snow',
                                                      data_id='item_magic_snow',
                description="Magical snow, that doesn't melt. Useful alchemical ingredient. If thrown - can deal minor frost damage.",
                                                      categories={'throwing', 'stackable', 'weight_per_charge',
                                                                  'alchemy'},
                                                      properties={'break_chance': 1,
                                                                  'throw_speed': 0.75,
                                                                  'accuracy_thrown': 0.6,
                                                                  'value': 120},
                                                      char="`", color=[0, 0, 255],
                                                      charges=1, destroyed_after_use=True, weight=0.1)
    react = {'type': 'deal_damage', 'chance': 70, 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (1, 3), 'dmg_type': 'cold'}
    a_t = abilities.AbilityTemplate(data_id='magic_snow_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Freeze', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [100, 100, 205]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_magic_snow'].add_ability(abil)

    data_set['item_explosive_potion'] = game_logic.ItemCharges(name='explosive potion',
                                                               data_id='item_explosive_potion',
                                                               description='Unstable potion, that explodes if breaked.',
                                                               categories={'throwing', 'stackable', 'weight_per_charge',
                                                                           'sticks_to_target'},
                                                               properties={'break_chance': 1,
                                                                           'throw_speed': 0.75,
                                                                           'accuracy_thrown': 1,
                                                                           'value': 160},
                                                               char="!", color=[255, 127, 80],
                                                               charges=1, destroyed_after_use=True, weight=0.5)
    react1 = {'type': 'deal_damage_aoe', 'aoe': 'circle', 'radius': 2.5, 'include_center': True,
              'target': 'projectile_hit_entity', 'strike_type': 'projectile',
              'damage': (7, 15), 'dmg_type': 'bashing'}
    react2 = {'type': 'kill_entity', 'target': 'thrown'}
    a_t = abilities.AbilityTemplate(data_id='potion_explosion',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'BOOM!', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react1, react2],
                                                 'message_color': [255, 127, 80]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_explosive_potion'].add_ability(abil)

    data_set['item_javelin'] = game_logic.ItemCharges(name='javelin',
                                                      data_id='item_javelin',
                                                      description='A short spear, made for throwing.',
                                                      categories={'throwing', 'stackable', 'weight_per_charge',
                                                                  'sticks_to_target'},
                                                      properties={'break_chance': 0.3,
                                                                  'accuracy_thrown': 1,
                                                                  'value': 60},
                                                      char=chr(92), color=[160, 50, 50],
                                                      charges=1, destroyed_after_use=True, weight=1.5)
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (2, 8), 'dmg_type': 'piercing'}
    a_t = abilities.AbilityTemplate(data_id='javelin_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Pierce', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [255, 255, 255]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['item_javelin'].add_ability(abil)

    # ==================================== MONSTERS ============================================================
    data_set['mob_mindless_body'] = game_logic.Fighter(name='Mindless body', data_id='mob_mindless_body', char='b',
                                    description='Shaking, dehydrated human body, raised by strange magic of the City.',
                                                       armor={'bashing': 0, 'slashing': 0, 'piercing': 0},
                                                       color=[109, 49, 9], hp=5, speed=100, sight_radius=14,
                                                       damage=(1, 2),
                                                       dmg_type='bashing', ai=game_logic.SimpleMeleeChaserAI(),
                                                       categories={'living'},
                                                       properties={'loot_list': 'mob_mindless_body'},
                                                       weight=60)

    data_set['mob_scorpion'] = game_logic.Fighter(name='Scorpion', data_id='mob_scorpion',
                                                  description='Huge black scorpion, about 1 meter long.', char='s',
                                                  armor={'bashing': -50, 'slashing': 50, 'piercing': 50},
                                                  color=[5, 5, 5], hp=3, speed=100, sight_radius=14, damage=(1, 4),
                                                  dmg_type='piercing', ai=game_logic.SimpleMeleeChaserAI(),
                                                  categories={'living'}, weight=15,
                                                  properties={'loot_list': ('mob_scorpion', 'mob_scorpion_ingredients')})
    cond1 = abilities.Condition('DEALT_DAMAGE', sign='>', number='0')
    cond2 = abilities.Condition('TARGET_IS_CATEGORY', category='living')
    react = {'type': 'deal_periodic_damage', 'chance': 50, 'target': 'default', 'damage': (1, 2),
             'dmg_type': 'poison', 'effect': effects.Effect('POISONED', 1), 'period': 1000, 'whole_time': 10000,
             'stackable': False}
    a_t = abilities.AbilityTemplate(data_id='scorpion_sting',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Poisonous stinger', 'trigger': 'hit_basic_attack',
                                                 'conditions': [cond1, ' and ', cond2], 'reactions': [react],
                                                 'message_color': [0, 150, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['mob_scorpion'].add_ability(abil)

    data_set['mob_rakshasa'] = game_logic.Fighter(name='Rakshasa', data_id='mob_rakshasa',
                                                  description='A bipedal tiger with very sharp claws.', char='R',
                                                  armor={'bashing': 0, 'slashing': 0, 'piercing': 0},
                                                  color=[255, 127, 80], hp=8, speed=80, sight_radius=18,
                                                  damage=(3, 7), categories={'living'},
                                                  properties={'loot_list': 'mob_rakshasa'},
                                                  dmg_type='slashing', ai=game_logic.SimpleMeleeChaserAI(), weight=70)

    data_set['mob_ifrit'] = game_logic.Fighter(name='Ifrit', data_id='mob_ifrit',
                            description='A magical creature with human upper body floating over column of flame.',
                                               char='F', armor={'bashing': 100, 'slashing': 100, 'piercing': 100},
                                               resist={'cold': -50, 'fire': 1000}, categories={'living', 'magical'},
                                               properties={'loot_list': 'mob_ifrit'},
                                               color=[255, 50, 0], hp=25, speed=100, sight_radius=18, damage=(3, 5),
                                               dmg_type='bashing', ai=game_logic.AbilityUserAI(), weight=100)
    data_set['mob_ifrit'].effects.append(effects.Effect('BLOCK_FIRE', 100))
    react = {'type': 'deal_damage', 'target': 'default', 'strike_type': 'melee',
             'damage': (3, 6), 'dmg_type': 'fire'}
    a_t = abilities.AbilityTemplate(data_id='flaming_fists',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Flaming fists', 'cooldown': 500,
                                                 'trigger': 'hit_basic_attack', 'conditions': [], 'reactions': [react],
                                                 'message_color': [255, 50, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['mob_ifrit'].add_ability(abil)
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=20, power=15, target=None, name='fireball',
                                         description='Explosive ball of pure flame.', char='*', color=[255, 0, 0])
    react = {'type': 'deal_damage_aoe', 'aoe': 'circle', 'radius': 2, 'include_center': True,
             'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (1, 5), 'dmg_type': 'fire'}
    a_t = abilities.AbilityTemplate(data_id='fireball_hit',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Fireball!', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [255, 0, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    proj.add_ability(abil)
    data_set['proj_fireball'] = proj
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'default', 'projectile': 'proj_firebolt'}
    ai_info = {'type': 'ranged_attack', 'target': 'player', 'range': '10', 'priority': '1',
               'whole_time': 100, 'use_offset': 0.5}
    a_t = abilities.AbilityTemplate(data_id='fireball',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Firebolt', 'cooldown': 1000, 'trigger': 'ability_used',
                                                 'conditions': [], 'reactions': [react], 'ai_info': ai_info,
                                                 'message_color': [255, 50, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['mob_ifrit'].add_ability(abil)

    data_set['mob_lightning_wisp'] = game_logic.Fighter(name='Lightning wisp', data_id='mob_lightning_wisp',
                            description='A small hostile magic cloud, that zaps enemies with lightning.', char='w',
                                                        armor={'bashing': 100, 'slashing': 100, 'piercing': 1000},
                                                        resist={'cold': -100, 'lightning': 1000},
                                                        color=[255, 215, 0], hp=2, speed=100, sight_radius=15,
                                                        damage=(1, 2), dmg_type='lightning', categories={'magical'},
                                                        properties={'loot_list': 'mob_lightning_wisp_ingredients'},
                                                        ai=game_logic.AbilityUserAI(behavior='ranged',
                                                                                    properties={'preferred_range': 6}),
                                                        weight=1, corpse='no corpse')
    data_set['mob_lightning_wisp'].effects.append(effects.Effect('BLOCK_PIERCING', 100))
    data_set['mob_lightning_wisp'].effects.append(effects.Effect('BLOCK_LIGHTNING', 100))
    cond = abilities.Condition('TARGET_IN_RANGE')
    react = {'type': 'deal_damage', 'target': 'default', 'damage': (2, 4), 'dmg_type': 'lightning'}
    ai_info = {'type': 'ranged_attack', 'target': 'player', 'range': '8', 'priority': '1',
               'whole_time': 100, 'use_offset': 0.5}
    a_t = abilities.AbilityTemplate(data_id='wisp_zap',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Zap', 'cooldown': 300, 'trigger': 'ability_used',
                                                 'conditions': [cond], 'reactions': [react], 'ai_info': ai_info,
                                                 'message_color': [255, 215, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    data_set['mob_lightning_wisp'].add_ability(abil)

    data_set['mob_flame_wisp'] = game_logic.Fighter(name='Flame wisp', data_id='mob_flame_wisp',
                                        description='Hostile ball of flame, burning with hatred to all living beings.',
                                                    char='w',
                                                    armor={'bashing': 100, 'slashing': 100, 'piercing': 1000},
                                                    resist={'cold': -200, 'fire': 1000},
                                                    color=[255, 0, 0], hp=2, speed=100, sight_radius=15,
                                                    damage=(1, 2), dmg_type='fire', categories={'magical'},
                                                    properties={'loot_list': 'mob_flame_wisp_ingredients'},
                                                    ai=game_logic.AbilityUserAI(behavior='ranged',
                                                                                properties={'preferred_range': 8}),
                                                    weight=1, corpse='no corpse')
    data_set['mob_flame_wisp'].effects.append(effects.Effect('BLOCK_PIERCING', 100))
    data_set['mob_flame_wisp'].effects.append(effects.Effect('BLOCK_FIRE', 100))
    cond = abilities.Condition('TARGET_IN_RANGE')
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=30, power=15, target=None, name='firebolt',
                                         description='An arrow of pure flame.', char='*', color=[255, 0, 0])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (2, 5), 'dmg_type': 'fire'}
    a_t = abilities.AbilityTemplate(data_id='wisp_ignite',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Ignite', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [255, 0, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    proj.add_ability(abil)
    data_set['proj_wisp_firebolt'] = proj
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'default', 'strike_type': 'projectile',
             'projectile': 'proj_wisp_firebolt'}
    ai_info = {'type': 'ranged_attack', 'target': 'player', 'range': '10', 'priority': '1',
               'whole_time': 100, 'use_offset': 0.5}
    a_t = abilities.AbilityTemplate(data_id='wisp_firebolt',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Firebolt', 'cooldown': 300, 'trigger': 'ability_used',
                                                 'conditions': [cond], 'reactions': [react], 'ai_info': ai_info,
                                                 'message_color': [255, 0, 0]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    proj.add_ability(abil)
    data_set['mob_flame_wisp'].add_ability(abil)

    data_set['mob_frost_wisp'] = game_logic.Fighter(name='Frost wisp', data_id='mob_frost_wisp',
                                description='Hostile ball of cold energy, burning with hatred to all living beings.',
                                                    char='w',
                                                    armor={'bashing': 100, 'slashing': 100, 'piercing': 1000},
                                                    resist={'cold': 1000, 'fire': -200},
                                                    color=[100, 100, 255], hp=2, speed=100, sight_radius=15,
                                                    damage=(1, 2), dmg_type='cold', categories={'magical'},
                                                    properties={'loot_list': 'mob_frost_wisp_ingredients'},
                                                    ai=game_logic.AbilityUserAI(behavior='ranged',
                                                                                properties={'preferred_range': 8}),
                                                    weight=1, corpse='no corpse')
    data_set['mob_frost_wisp'].effects.append(effects.Effect('BLOCK_PIERCING', 100))
    data_set['mob_frost_wisp'].effects.append(effects.Effect('BLOCK_COLD', 100))
    cond = abilities.Condition('TARGET_IN_RANGE')
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=30, power=15, target=None, name='frostbolt',
                                         description='An arrow of pure frost.', char='*', color=[0, 0, 255])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'strike_type': 'projectile',
             'damage': (2, 5), 'dmg_type': 'cold'}
    a_t = abilities.AbilityTemplate(data_id='wisp_freeze',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Freeze', 'trigger': 'projectile_hit',
                                                 'conditions': [], 'reactions': [react],
                                                 'message_color': [0, 0, 255]})
    ability_dict[a_t.data_id] = a_t
    abil1 = a_t.get_stored_object()
    cond_chill1 = abilities.Condition('ABILITY_NAME_IS', name='Freeze')
    cond_chill2 = abilities.Condition('DEALT_DAMAGE', sign='>', number='0')

    react2 = {'type': 'apply_timed_effect', 'target': 'projectile_hit_entity', 'time': 500,
              'effect': effects.Effect('SLOWED', 150)}
    a_t = abilities.AbilityTemplate(data_id='wisp_chill',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Chill', 'trigger': 'ability_fired',
                                                 'conditions': [cond_chill1, ' and ', cond_chill2],
                                                 'reactions': [react2], 'message_color': [100, 100, 255]})
    ability_dict[a_t.data_id] = a_t
    abil2 = a_t.get_stored_object()
    proj.add_ability(abil1)
    proj.add_ability(abil2)
    data_set['proj_wisp_frostbolt'] = proj
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'default', 'strike_type': 'projectile',
             'projectile': 'proj_wisp_frostbolt'}
    ai_info = {'type': 'ranged_attack', 'target': 'player', 'range': '10', 'priority': '1',
               'whole_time': 100, 'use_offset': 0.5}
    a_t = abilities.AbilityTemplate(data_id='wisp_frostbolt',
                                    stored_class_name='Ability',
                                    init_kwargs={'name': 'Frostbolt', 'cooldown': 300, 'trigger': 'ability_used',
                                                 'conditions': [cond], 'reactions': [react], 'ai_info': ai_info,
                                                 'message_color': [0, 0, 255]})
    ability_dict[a_t.data_id] = a_t
    abil = a_t.get_stored_object()
    proj.add_ability(abil)
    data_set['mob_frost_wisp'].add_ability(abil)

    data_set['mob_sand_golem'] = game_logic.Fighter(name='Sand golem', data_id='mob_sand_golem', char='G',
                                        description='Magic-formed sand, resembling a human figure about 3m high.',
                                                    armor={'bashing': 100, 'slashing': 75, 'piercing': 300},
                                                    color=[255, 215, 0], hp=20, speed=200, sight_radius=9,
                                                    damage=(6, 10), categories={'golem', 'magical'},
                                                    properties={'loot_list': 'mob_sand_golem'},
                                                    dmg_type='bashing', ai=game_logic.SimpleMeleeChaserAI(), weight=300)
    data_set['mob_sand_golem'].effects.append(effects.Effect('BLOCK_BASHING', 2))
    data_set['mob_sand_golem'].effects.append(effects.Effect('BLOCK_SLASHING', 1))
    data_set['mob_sand_golem'].effects.append(effects.Effect('BLOCK_PIERCING', 10))

    data_set['mob_iron_golem'] = game_logic.Fighter(name='Iron golem', data_id='mob_iron_golem', char='G',
                description='Fighting mechanism made of iron, brought to life with magic. Armed with enormous blade.',
                                                    armor={'bashing': 50, 'slashing': 200, 'piercing': 300, 'acid': -50},
                                                    color=[200, 200, 255], hp=20, speed=150, sight_radius=9,
                                                    damage=(6, 12), categories={'golem', 'magical', 'iron'},
                                                    properties={'loot_list': 'mob_iron_golem'},
                                                    dmg_type='slashing', ai=game_logic.SimpleMeleeChaserAI(), weight=300)
    data_set['mob_iron_golem'].effects.append(effects.Effect('BLOCK_BASHING', 2))
    data_set['mob_iron_golem'].effects.append(effects.Effect('BLOCK_SLASHING', 5))
    data_set['mob_iron_golem'].effects.append(effects.Effect('BLOCK_PIERCING', 10))

    events.Observer.clear()  # remove events made during init of Entities - A HACK


def get_entity(data_id):
    """ Function that returns entity template by ID """
    return pickle.loads(pickle.dumps(data_set[data_id]))  # return pickle copy of Entity template


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

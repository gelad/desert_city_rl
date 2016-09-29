"""
    This file contains functions to work with data - saved templates for Entities and so on.
"""
import game_logic
import effects
import abilities
import events

import pickle
import simplejson
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
                                                 armor={'bashing': 100, 'slashing': 500, 'piercing': 300},
                                                 char='#', color=[255, 250, 205], hp=100, weight=1000,
                                                 corpse='debris_large_sandstone')
    data_set['wall_sandstone'].effects.append(effects.Effect('BLOCK_BASHING', 10))
    data_set['wall_sandstone'].effects.append(effects.Effect('BLOCK_SLASHING', 30))
    data_set['wall_sandstone'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['window_small_sandstone'] = game_logic.Prop(name='Small window', data_id='window_small_sandstone',
                                                         occupies_tile=True, blocks_los=False, blocks_shots=0.15,
                                                         armor={'bashing': 100, 'slashing': 500, 'piercing': 300},
                                                         description='A hole in sandstone wall.',
                                                         char='"', color=[255, 250, 205], hp=100, weight=800,
                                                         corpse='debris_large_sandstone')
    data_set['window_small_sandstone'].effects.append(effects.Effect('BLOCK_BASHING', 10))
    data_set['window_small_sandstone'].effects.append(effects.Effect('BLOCK_SLASHING', 30))
    data_set['window_small_sandstone'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['window_large_sandstone'] = game_logic.Prop(name='Large window', data_id='window_large_sandstone',
                                                         occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                         armor={'bashing': 100, 'slashing': 500, 'piercing': 300},
                                                         pass_cost=2,
                                                         description='A large window in sandstone wall.',
                                                         char='_', color=[255, 250, 205], hp=100, weight=800,
                                                         corpse='debris_large_sandstone')
    data_set['window_large_sandstone'].effects.append(effects.Effect('BLOCK_BASHING', 10))
    data_set['window_large_sandstone'].effects.append(effects.Effect('BLOCK_SLASHING', 30))
    data_set['window_large_sandstone'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['debris_large_sandstone'] = game_logic.Prop(name='Pile of sandstone blocks',
                                                         data_id='debris_large_sandstone',
                                                         occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                         armor={'bashing': 300, 'slashing': 500, 'piercing': 300},
                                                         pass_cost=2,
                                                         description='A collapsed structure, like wall or pillar.',
                                                         char='&', color=[255, 250, 205], hp=200, weight=800)
    data_set['debris_large_sandstone'].effects.append(effects.Effect('BLOCK_BASHING', 30))
    data_set['debris_large_sandstone'].effects.append(effects.Effect('BLOCK_SLASHING', 30))
    data_set['debris_large_sandstone'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['debris_large_wooden'] = game_logic.Prop(name='Pile of wooden debris',
                                                      data_id='debris_large_wooden',
                                                      occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                      armor={'bashing': 200, 'slashing': 200, 'piercing': 200},
                                                      pass_cost=2,
                                                      description='Large destroyed wooden furniture.',
                                                      char='&', color=[128, 0, 0], hp=200, weight=50)
    data_set['debris_large_wooden'].effects.append(effects.Effect('BLOCK_BASHING', 20))
    data_set['debris_large_wooden'].effects.append(effects.Effect('BLOCK_SLASHING', 20))
    data_set['debris_large_wooden'].effects.append(effects.Effect('BLOCK_PIERCING', 20))

    data_set['trap_corrosive_moss'] = game_logic.Prop(name='Corrosive moss', data_id='trap_corrosive_moss',
                                                      occupies_tile=False, blocks_los=False, blocks_shots=0,
                                                      armor={'bashing': 300, 'slashing': 50, 'piercing': 300},
                                                      pass_cost=1,
                                                      description='A large patch of green acid-dripping moss.',
                                                      char='_', color=[100, 220, 100], hp=30, weight=10)
    data_set['trap_corrosive_moss'].effects.append(effects.Effect('BLOCK_BASHING', 30))
    data_set['trap_corrosive_moss'].effects.append(effects.Effect('BLOCK_SLASHING', 2))
    data_set['trap_corrosive_moss'].effects.append(effects.Effect('BLOCK_PIERCING', 30))
    cond = abilities.Condition('MOVED_ON')
    react = {'type': 'deal_damage', 'target': 'mover', 'damage': (1, 3), 'dmg_type': 'acid'}
    abil = abilities.Ability(name='Corrosive acid', owner=data_set['trap_corrosive_moss'],
                             trigger='entity_moved', conditions=[cond], reactions=[react],
                             message_color=[100, 220, 100])
    data_set['trap_corrosive_moss'].add_ability(abil)

    data_set['door_wooden'] = game_logic.Door(name='Door', data_id='door_wooden', description='A wooden door.',
                                              char_closed='+', char_open='.', color=[128, 0, 0],
                                              armor={'bashing': 200, 'slashing': 100, 'piercing': 300},
                                              hp=100, is_closed=True, weight=50,
                                              corpse='debris_large_wooden')
    data_set['door_wooden'].effects.append(effects.Effect('BLOCK_BASHING', 10))
    data_set['door_wooden'].effects.append(effects.Effect('BLOCK_SLASHING', 10))
    data_set['door_wooden'].effects.append(effects.Effect('BLOCK_PIERCING', 30))

    data_set['item_boulder'] = game_logic.Item(name='item_boulder', data_id='item_boulder',
                                               description='A stone boulder.', categories={'rubbish'},
                                               char='*', color=[200, 200, 200], weight=10)

    data_set['item_haste_potion'] = game_logic.ItemCharges(name='haste potion', data_id='item_haste_potion',
                                                           description='A potion that hastens user by 50%.',
                                                           categories={'consumable', 'potion'},
                                                           properties={'usable': 'self'},
                                                           char='!', color=[255, 255, 0],
                                                           charges=1, destroyed_after_use=True, weight=0.2)
    cond = abilities.Condition('USED')
    react = {'type': 'apply_timed_effect', 'target': 'item_owner', 'time': 1000, 'effect': effects.Effect('HASTE', 50)}
    abil = abilities.Ability(name='Haste', owner=data_set['item_haste_potion'],
                             trigger='used_on_self', conditions=[cond], reactions=[react],
                             message_color=[255, 255, 0])
    data_set['item_haste_potion'].add_ability(abil)

    data_set['item_antidote_potion'] = game_logic.ItemCharges(name='antidote potion', data_id='item_antidote_potion',
                    description='A potion that cures all poison effects, and protects from poison for a short time.',
                                                              categories={'consumable', 'potion'},
                                                              properties={'usable': 'self'},
                                                              char='!', color=[0, 150, 0],
                                                              charges=1, destroyed_after_use=True, weight=0.2)
    cond = abilities.Condition('USED')
    react1 = {'type': 'remove_effect', 'target': 'item_owner', 'effect': effects.Effect('POISONED', 0),
              'effects_number': 'all'}
    react2 = {'type': 'apply_timed_effect', 'target': 'item_owner', 'time': 500,
              'effect': effects.Effect('RESIST_POISON', 500)}
    abil = abilities.Ability(name='Antidote', owner=data_set['item_antidote_potion'],
                             trigger='used_on_self', conditions=[cond], reactions=[react1, react2],
                             message_color=[0, 150, 0])
    data_set['item_antidote_potion'].add_ability(abil)

    data_set['item_lightning_scroll'] = game_logic.ItemCharges(name='scroll of Lightning', data_id='item_lightning_scroll',
                                                    description='A scroll that calls a lightning strike on enemy.',
                                                               categories={'consumable', 'scroll'},
                                                               properties={'usable': 'battle_entity', 'range': 15},
                                                               char='?', color=[255, 255, 0],
                                                               charges=1, destroyed_after_use=True, weight=0.1)
    cond = abilities.Condition('USED')
    react = {'type': 'deal_damage', 'target': 'attacked_entity', 'damage': (10, 30), 'dmg_type': 'lightning'}
    abil = abilities.Ability(name='Lightning', owner=data_set['item_lightning_scroll'],
                             trigger='used_on_target', conditions=[cond], reactions=[react],
                             message_color=[255, 255, 0])
    data_set['item_lightning_scroll'].add_ability(abil)

    data_set['item_firebolt_scroll'] = game_logic.ItemCharges(name='scroll of Firebolt',
                                                              data_id='item_firebolt_scroll',
                                                              description='A scroll that hurls a firebolt at enemy.',
                                                              categories={'consumable', 'scroll'},
                                                              properties={'usable': 'battle_entity_or_point',
                                                                          'range': 15,
                                                                          'use_time_coef': 1,
                                                                          'use_time_offset': 0.7},
                                                              char='?', color=[255, 0, 0],
                                                              charges=1, destroyed_after_use=True, weight=0.1)
    cond = abilities.Condition('USED')
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=20, power=15, target=None, name='firebolt',
                                         description='An arrow of pure flame.', char='*', color=[255, 0, 0])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'damage': (3, 6), 'dmg_type': 'fire'}
    abil = abilities.Ability(name='Ignite', owner=proj, trigger='projectile_hit', conditions=[], reactions=[react],
                             message_color=[255, 0, 0])
    proj.add_ability(abil)
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'attacked_entity', 'projectile': proj}
    abil = abilities.Ability(name='Firebolt', owner=data_set['item_firebolt_scroll'],
                             trigger='used_on_target', conditions=[cond], reactions=[react],
                             message_color=[255, 0, 0])
    data_set['item_firebolt_scroll'].add_ability(abil)

    data_set['item_frostbolt_scroll'] = game_logic.ItemCharges(name='scroll of Frostbolt',
                                                               data_id='item_frostbolt_scroll',
                                                               description='A scroll that hurls a frostbolt at enemy.',
                                                               categories={'consumable', 'scroll'},
                                                               properties={'usable': 'battle_entity_or_point',
                                                                           'range': 15,
                                                                           'use_time_coef': 1,
                                                                           'use_time_offset': 0.7},
                                                               char='?', color=[100, 100, 255],
                                                               charges=1, destroyed_after_use=True, weight=0.1)
    cond = abilities.Condition('USED')
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=20, power=15, target=None, name='frostbolt',
                                         description='An arrow of freezing energy.', char='*', color=[100, 100, 255])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'damage': (3, 6), 'dmg_type': 'cold'}
    abil = abilities.Ability(name='Freeze', owner=proj, trigger='projectile_hit', conditions=[], reactions=[react],
                             message_color=[100, 100, 255])
    proj.add_ability(abil)
    # === end of projectile
    react = {'type': 'launch_projectile', 'target': 'attacked_entity', 'projectile': proj}
    abil = abilities.Ability(name='Frostbolt', owner=data_set['item_frostbolt_scroll'],
                             trigger='used_on_target', conditions=[cond], reactions=[react],
                             message_color=[100, 100, 255])
    data_set['item_frostbolt_scroll'].add_ability(abil)

    data_set['item_healing_potion'] = game_logic.ItemCharges(name='healing potion', data_id='item_healing_potion',
                                                             description='A potion that heals 5 HP.',
                                                             categories={'consumable', 'potion'},
                                                             properties={'usable': 'self'},
                                                             char='!', color=[255, 0, 0],
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
                             trigger='damaged', conditions=[cond], reactions=[react],
                             message_color=[200, 0, 100])
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
                                                      char=']', color=[50, 50, 200], equip_slots={'SHOULDERS'},
                                                      weight=2)

    data_set['item_iron_boots'] = game_logic.Item(name='iron boots', data_id='item_iron_boots',
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
                                                                                'accuracy_ranged': 1},
                                                                    char=')', color=[200, 200, 200], weight=3)
    data_set['item_hunting_crossbow'].effects.append(effects.Effect('INCREASE_RANGED_DAMAGE', 4))

    data_set['item_short_bow'] = game_logic.ItemRangedWeapon(name='short bow',
                                                             data_id='item_short_bow',
                                                             description='Short bow suited for small game hunt.',
                                                             range=10, ammo_type='arrow',
                                                             categories={'weapon', 'blunt', 'bow'},
                                                             properties={'bashing': (1, 2),
                                                                         'attack_speed_mod': 1.1,
                                                                         'accuracy_ranged': 0.9},
                                                             char=')', color=[128, 0, 0], weight=1.5)
    data_set['item_short_bow'].effects.append(effects.Effect('INCREASE_RANGED_DAMAGE', 1))

    data_set['item_bronze_bolt'] = game_logic.ItemCharges(name='bronze bolt', data_id='item_bronze_bolt',
                                                          description='A simple bronze bolt for crossbows.',
                                                          categories={'bolt', 'stackable'},
                                                          properties={'piercing': (1, 4), 'break_chance': 0.5},
                                                          char='=', color=[80, 50, 20],
                                                          charges=5, destroyed_after_use=True, weight=0.2)

    data_set['item_bronze_tipped_arrow'] = game_logic.ItemCharges(name='bronze tipped arrow',
                                                                  data_id='item_bronze_tipped_arrow',
                                                                  description='A simple bronze tipped arrow.',
                                                                  categories={'arrow', 'stackable'},
                                                                  properties={'piercing': (1, 3), 'break_chance': 0.5},
                                                                  char='=', color=[128, 20, 20],
                                                                  charges=5, destroyed_after_use=True, weight=0.1)

    data_set['item_poisoned_arrow'] = game_logic.ItemCharges(name='poisoned arrow',
                                                                  data_id='item_poisoned_arrow',
                                                    description='A simple bronze tipped arrow, coated in weak poison.',
                                                                  categories={'arrow', 'stackable'},
                                                                  properties={'piercing': (1, 3), 'break_chance': 0.5},
                                                                  char='=', color=[128, 150, 20],
                                                                  charges=3, destroyed_after_use=True, weight=0.1)
    react = {'type': 'deal_periodic_damage', 'target': 'attacked_entity', 'damage': (0, 2),
             'dmg_type': 'poison', 'effect': effects.Effect('POISONED', 1), 'period': 1000, 'whole_time': 5000,
             'stackable': False}
    abil = abilities.Ability(name='Poisoned arrow', owner=data_set['item_poisoned_arrow'],
                             trigger='shot_hit', conditions=[], reactions=[react],
                             message_color=[0, 150, 0])
    data_set['item_poisoned_arrow'].add_ability(abil)

    data_set['mob_mindless_body'] = game_logic.Fighter(name='Mindless body', data_id='mob_mindless_body', char='b',
                                    description='Shaking, dehydrated human body, raised by strange magic of the City.',
                                                       armor={'bashing': 0, 'slashing': 0, 'piercing': 0},
                                                       color=[109, 49, 9], hp=5, speed=100, sight_radius=14.5,
                                                       damage=(1, 2),
                                                       dmg_type='bashing', ai=game_logic.SimpleMeleeChaserAI(),
                                                       weight=60)

    data_set['mob_scorpion'] = game_logic.Fighter(name='Scorpion', data_id='mob_scorpion',
                                                  description='Huge black scorpion, about 1 meter long.', char='s',
                                                  armor={'bashing': -50, 'slashing': 50, 'piercing': 50},
                                                  color=[5, 5, 5], hp=3, speed=100, sight_radius=14.5, damage=(1, 4),
                                                  dmg_type='piercing', ai=game_logic.SimpleMeleeChaserAI(), weight=15)
    react = {'type': 'deal_periodic_damage', 'chance': 50, 'target': 'attacked_entity', 'damage': (1, 2),
             'dmg_type': 'poison', 'effect': effects.Effect('POISONED', 1), 'period': 1000, 'whole_time': 10000,
             'stackable': False}
    abil = abilities.Ability(name='Poisonous stinger', owner=data_set['mob_scorpion'],
                             trigger='hit_basic_attack', conditions=[], reactions=[react],
                             message_color=[0, 150, 0])
    data_set['mob_scorpion'].add_ability(abil)

    data_set['mob_rakshasa'] = game_logic.Fighter(name='Rakshasa', data_id='mob_rakshasa',
                                                  description='A bipedal tiger with very sharp claws.', char='R',
                                                  armor={'bashing': 0, 'slashing': 0, 'piercing': 0},
                                                  color=[255, 127, 80], hp=8, speed=80, sight_radius=18.5,
                                                  damage=(3, 7),
                                                  dmg_type='slashing', ai=game_logic.SimpleMeleeChaserAI(), weight=70)

    data_set['mob_ifrit'] = game_logic.Fighter(name='Ifrit', data_id='mob_ifrit',
                            description='A magical creature with human upper body floating over column of flame.',
                                               char='F', armor={'bashing': 100, 'slashing': 100, 'piercing': 100},
                                               resist={'cold': -50, 'fire': 1000},
                                               color=[255, 50, 0], hp=25, speed=100, sight_radius=18.5, damage=(3, 5),
                                               dmg_type='bashing', ai=game_logic.AbilityUserAI(), weight=100)
    data_set['mob_ifrit'].effects.append(effects.Effect('BLOCK_FIRE', 100))
    react = {'type': 'deal_damage', 'target': 'attacked_entity', 'damage': (3, 6), 'dmg_type': 'fire'}
    abil = abilities.Ability(name='Flaming fists', owner=data_set['mob_ifrit'], cooldown=500,
                             trigger='hit_basic_attack', conditions=[], reactions=[react],
                             message_color=[255, 50, 0])
    data_set['mob_ifrit'].add_ability(abil)
    # TODO: remake Firebolt into Fireball when explosions will be done
    # === projectile
    proj = game_logic.UnguidedProjectile(launcher=None, speed=20, power=15, target=None, name='firebolt',
                                         description='An arrow of pure flame.', char='*', color=[255, 0, 0])
    react = {'type': 'deal_damage', 'target': 'projectile_hit_entity', 'damage': (1, 5), 'dmg_type': 'fire'}
    abil = abilities.Ability(name='Ignite', owner=proj, trigger='projectile_hit', conditions=[], reactions=[react],
                             message_color=[255, 0, 0])
    proj.add_ability(abil)
    # === end of projectile
    cond = abilities.Condition('TARGET_IN_RANGE')
    react = {'type': 'launch_projectile', 'target': 'attacked_entity', 'projectile': proj}
    ai_info = {'type': 'ranged_attack', 'target': 'player', 'range': '10', 'priority': '1',
               'whole_time': 100, 'use_offset': 0.5}
    abil = abilities.Ability(name='Firebolt', owner=data_set['mob_ifrit'], cooldown=1000,
                             trigger='ability_used', conditions=[cond], reactions=[react], ai_info=ai_info,
                             message_color=[255, 50, 0])
    data_set['mob_ifrit'].add_ability(abil)

    data_set['mob_lightning_wisp'] = game_logic.Fighter(name='Lightning wisp', data_id='mob_lightning_wisp',
                            description='A small hostile magic cloud, that zaps enemies with lightning.', char='w',
                                                        armor={'bashing': 100, 'slashing': 100, 'piercing': 1000},
                                                        resist={'cold': -100, 'lightning': 1000},
                                                        color=[255, 255, 0], hp=2, speed=100, sight_radius=15.5,
                                                        damage=(1, 2), dmg_type='lightning',
                                                        ai=game_logic.AbilityUserAI(behavior='ranged',
                                                                                    properties={'preferred_range': 6}),
                                                        weight=1)
    data_set['mob_lightning_wisp'].effects.append(effects.Effect('BLOCK_PIERCING', 100))
    data_set['mob_lightning_wisp'].effects.append(effects.Effect('BLOCK_LIGHTNING', 100))
    cond = abilities.Condition('TARGET_IN_RANGE')
    react = {'type': 'deal_damage', 'target': 'attacked_entity', 'damage': (2, 4), 'dmg_type': 'lightning'}
    ai_info = {'type': 'ranged_attack', 'target': 'player', 'range': '8', 'priority': '1',
               'whole_time': 100, 'use_offset': 0.5}
    abil = abilities.Ability(name='Zap', owner=data_set['mob_lightning_wisp'], cooldown=300,
                             trigger='ability_used', conditions=[cond], reactions=[react], ai_info=ai_info,
                             message_color=[255, 255, 0])
    data_set['mob_lightning_wisp'].add_ability(abil)

    data_set['mob_sand_golem'] = game_logic.Fighter(name='Sand golem', data_id='mob_sand_golem', char='S',
                                        description='Magic-formed sand, resembling a human figure about 3m high.',
                                                    armor={'bashing': 100, 'slashing': 75, 'piercing': 300},
                                                    color=[255, 255, 0], hp=20, speed=200, sight_radius=9.5,
                                                    damage=(6, 10),
                                                    dmg_type='bashing', ai=game_logic.SimpleMeleeChaserAI(), weight=300)
    data_set['mob_sand_golem'].effects.append(effects.Effect('BLOCK_BASHING', 2))
    data_set['mob_sand_golem'].effects.append(effects.Effect('BLOCK_SLASHING', 1))
    data_set['mob_sand_golem'].effects.append(effects.Effect('BLOCK_PIERCING', 10))

    events.Observer.clear()  # remove events made during init of Entities - A HACK


def get_entity(data_id):
    """ Function that returns entity template by ID """
    return pickle.loads(pickle.dumps(data_set[data_id]))  # return pickle copy of Entity template


def get_tile(tile_id):
    """ Function that returns entity template by ID """
    return tile_set[tile_id]

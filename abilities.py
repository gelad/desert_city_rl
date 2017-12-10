"""
    This file contains abilities.
"""
import game_logic
import events
import actions
import bool_eval

from messages import _  # translation function

import pickle
import random
from math import hypot


class Condition:
    """ Class for ability condition """

    def __init__(self, condition='', **kwargs):
        self.condition = condition  # condition identificator
        self.kwargs = kwargs  # arguments to check condition

    def evaluate(self, **kwargs):
        """ Method to evaluate condition, returning True or False """
        if self.kwargs:  # if any arguments given on condition creation - add them
            kwargs.update(self.kwargs)
        if self.condition == 'TARGET_IS_CATEGORY':  # TARGET_IS_CATEGORY condition
            category = self.kwargs['category']
            try:
                if category in kwargs['target'].categories:
                    return True
                else:
                    return False
            except AttributeError:  # if no categories at all - False
                return False
        elif self.condition == 'OWNER_HP_PERCENT':  # OWNER_HP_PERCENT condition
            sign = self.kwargs['sign']
            number = self.kwargs['number']
            return eval(
                str(kwargs['owner'].hp / kwargs['owner'].maxhp) + sign + str(number))  # check hp percent condition
        elif self.condition == 'DEALT_DAMAGE':  # DEALT_DAMAGE condition
            sign = self.kwargs['sign']
            number = self.kwargs['number']
            if 'damage' in kwargs:
                return eval(str(kwargs['damage']) + sign + str(number))  # check damage condition
            else:  # if no 'damage' arg - False
                return False
        elif self.condition == 'EQUIPPED' and kwargs['owner']:  # EQUIPPED condition
            if kwargs['owner_item'] in kwargs['owner'].equipment.values():  # check if item equipped
                return True
            else:
                return False
        elif self.condition == 'USED':  # USED condition
            if kwargs['owner_item'] == kwargs['item']:  # check if item used is item with ability
                return True
            else:
                return False
        elif self.condition == 'MOVED_ON':  # MOVED_ON condition
            # check if positions and locations of owner and entity match
            if kwargs['owner'].position == kwargs['entity'].position and \
                            kwargs['owner'].location == kwargs['entity'].location:
                return True
            else:
                return False
        elif self.condition == 'TARGET_IN_RANGE':  # TARGET IN RANGE condition
            if isinstance(kwargs['target'], game_logic.BattleEntity):  # if target is a BE
                target = (kwargs['target'].position[0], kwargs['target'].position[1])
            else:  # if not - it must be a point tuple
                target = kwargs['target']
            origin = (kwargs['owner'].position[0], kwargs['owner'].position[1])
            # check if target is in range
            if hypot(origin[0] - target[0], origin[1] - target[1]) <= float(kwargs['range']):
                return True
            else:
                return False
        elif self.condition == 'MOVER_IS_A_BE':  # MOVER IS A BE condition
            if isinstance(kwargs['entity'], game_logic.BattleEntity):  # if target is a BE
                return True
            else:
                return False
        elif self.condition == 'ABILITY_NAME_IS':  # ABILITY NAME IS condition
            if kwargs['ability'].data_id == kwargs['name']:
                return True
            else:
                return False
        return True


class Ability(events.Observer):
    """ Base class for Ability object """

    def __init__(self, trigger, reactions, owner=None, conditions=None, enabled=True, cooldown=0, name='',
                 description='', data_id='', message_color=None, ai_info=None):
        self._owner = owner
        self.enabled = enabled  # is ability enabled or not
        self.trigger = trigger  # ability trigger
        self.conditions = conditions  # ability condition
        self.reactions = reactions  # ability reactions
        self.cooldown = cooldown  # ability internal cooldown in ticks
        self.ticks_to_cd = 0  # ticks to cooldown
        self.ability_on_cd = False  # is ability on cd
        self.name = name  # name of the ability
        self.data_id = data_id  # ability ID in dataset
        self.description = description  # description of ability
        self.ai_info = ai_info  # info for AI how and when to use the ability
        if message_color is None:
            self.message_color = [255, 255, 255]
        else:
            self.message_color = message_color  # if ability shows any messages - they use this color
        if self.owner:
            self.reobserve()

    @property
    def owner(self):
        try:  # if ability belongs to an item - check owner of item
            if self._owner.owner:  # if item is equipped or in inventory - get owning Entity
                o = self._owner.owner
            else:
                o = self._owner
        except AttributeError:
            o = self._owner
        return o

    def reobserve(self):
        """ Method that registers Ability to observe events """
        events.Observer.__init__(self)  # register self as observer
        self.observe(self.owner, self.on_event)
        if self.owner != self._owner:
            self.observe(self._owner, self.on_event)
        if self.owner.location:
            self.observe(self.owner.location, self.on_event)
        self.observe('time', self.on_event)

    def set_owner(self, owner):
        """ Method to set owner and refresh observer """
        if self._owner:
            self.close()  # unregister observing old owner
        self._owner = owner  # set owner
        self.reobserve()  # register observers

    def on_event(self, data):
        """ Method that is called if any owner-related event fires """
        if data['type'] == 'ticks_passed':  # if tick event
            if self.cooldown > 0 and self.enabled and self.ability_on_cd:  # if ability is on cooldown
                self.ticks_to_cd -= data['ticks']
                if self.ticks_to_cd <= 0:  # if ability is ready
                    self.ability_on_cd = False  # finish cooldown
        if data['type'] == self.trigger and not self.ability_on_cd:  # if trigger is valid
            if self.conditions_met(data):  # if conditions are passed - react
                # TODO: make reaction chain - subsequent reaction have info on previous ones results
                for reaction in self.reactions:
                    if 'chance' in reaction:  # if reaction occurs with some random chance (percent)
                        if random.randint(1, 100) > reaction['chance']:  # take a chance
                            self.react(reaction, data)
                    else:  # if not - react
                        self.react(reaction, data)

    def conditions_met(self, data):
        """ Method that checks if conditions are met """
        if not self.enabled:  # if not enabled - conditions aren't met by default
            return False
        expression = ''
        for cond in self.conditions:
            if isinstance(cond, Condition):
                # event data is passed to condition as is
                # if other kwargs needed - add here
                data.update({'owner': self.owner, 'owner_item': self._owner})
                if self.ai_info:  # if ai_info exists - pass some additional arguments
                    if self.ai_info['type'] == 'ranged_attack':
                        data.update({'range': self.ai_info['range']})
                expression += str(cond.evaluate(**data))  # add evaluation of condition result
            else:
                expression += cond  # add '(', ')', 'and', 'or' etc
        return bool_eval.nested_bool_eval(expression)  # evaluate result expression and return

    def react(self, reaction, event_data):
        """ Method that converts reaction dicts to game actions """
        if reaction['type'] == 'deal_damage':  # dealing damage reaction
            reaction_result = self.react_deal_damage(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'deal_damage_aoe':  # dealing damage in AOE reaction
            reaction_result = self.react_deal_damage_aoe(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'kill_entity':  # removing entity reaction
            reaction_result = self.react_kill_entity(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'launch_projectile':  # launch projectile reaction
            reaction_result = self.react_launch_projectile(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'heal':  # healing reaction
            reaction_result = self.react_heal(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'apply_timed_effect':  # applying timed effect reaction
            reaction_result = self.react_apply_timed_effect(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'remove_effect':  # remove effect reaction
            reaction_result = self.react_remove_effect(reaction=reaction, event_data=event_data)
        elif reaction['type'] == 'deal_periodic_damage':  # deal periodic damage
            reaction_result = self.react_deal_periodic_damage(reaction=reaction, event_data=event_data)
        else:
            raise Exception('Unknown reaction - ' + reaction['type'])
        if self.cooldown > 0:  # if ability has cooldown
            self.ability_on_cd = True  # start cooldown
            self.ticks_to_cd = self.cooldown
        # fire an ability event
        ability_event_data = {'type': 'ability_fired', 'ability': self}
        if reaction_result:
            ability_event_data.update(reaction_result)
        events.Event(self.owner, ability_event_data)
        events.Event('location', ability_event_data)
        return reaction_result

    # ===========================================REACTIONS=================================================
    def react_deal_damage(self, reaction, event_data):
        """ Reaction, that deals damage """
        reaction_result = {'success': False, 'damage': 0, 'target': None}  # reaction result dict
        if 'strike_type' in reaction:  # determine strike type
            strike_type = reaction['strike_type']
        else:
            strike_type = 'default'
        strike = game_logic.Strike(strike_type=strike_type, damage=reaction['damage'], dmg_type=reaction['dmg_type'])
        if reaction['target'] == 'projectile_hit_entity':  # if target is hit by projectile
            target = event_data['target']
            attacker = event_data['attacker']
        elif reaction['target'] == 'mover':  # if target is mover
            target = event_data['entity']
            attacker = self.owner
        else:  # default target and attacker
            target = event_data['target']
            attacker = self.owner
        if isinstance(target, game_logic.BattleEntity):  # if target is a damageable BE
            damage_dealt = attacker.land_strike(strike=strike, target=target)  # land strike
            game_logic.Game.add_message(message=
                _('{ability_name}: {target_name} takes {damage} {dmg_type} damage!').format(ability_name=_(self.name),
                                                                                            target_name=str(target),
                                                                                            damage=str(damage_dealt),
                                                                                            dmg_type=
                                                                                            _(reaction['dmg_type'])),
                level='PLAYER', color=self.message_color)
            reaction_result['damage'] = damage_dealt
            reaction_result['target'] = target
            if damage_dealt > 0:
                reaction_result['success'] = True
        else:  # tried to deal damage to not BattleEntity
            game_logic.Game.add_message(
                self.name + ': attempted to deal damage to not BE.',
                'DEBUG', self.message_color)
        return reaction_result

    def react_deal_damage_aoe(self, reaction, event_data):
        """ Reaction, that deals damage in AOE """
        # if reaction is AOE - apply reaction to all cells in specified area
        reaction_result = {'success': False}  # result dict TODO: make more complicate result - list of targets
        if reaction['aoe'] == 'circle':
            radius = reaction['radius']
            include_center = reaction['include_center']
            points = game_logic.circle_points(r=radius, include_center=include_center)  # get points in AOE
            if isinstance(event_data['target'], game_logic.Entity):  # if target is an entity - target cell with it
                target = (event_data['target'].position[0], event_data['target'].position[1])
            else:  # if not - it must be a tuple
                target = event_data['target']
            for point in points:  # iterate through every point in AOE and deal damage to BattleEntities
                cell = (point[0] + target[0], point[1] + target[1])
                if self.owner.location.is_in_boundaries(cell[0], cell[1]):
                    be = self.owner.location.cells[cell[0]][cell[1]].is_there_a(game_logic.BattleEntity)
                    if be:  # if BE found
                        conds_met = True  # conditions met flag - true by default
                        event_data['target'] = be  # set target in event data to found BE
                        if 'aoe_conditions' in reaction:
                            conds = reaction['aoe_conditions']
                            if not check_conditions(conditions=conds, data=event_data):
                                conds_met = False
                        if conds_met:
                            res = self.react_deal_damage(reaction, event_data)
                            if res['success']:  # if at least one target damaged - set success to true
                                reaction_result['success'] = True
        return reaction_result

    def react_launch_projectile(self, reaction, event_data):
        """ Reaction, that launches projectile """
        # if there will be different reaction targets - specify here
        if isinstance(event_data['target'], game_logic.Entity):  # if target is an entity - target cell with it
            target = (event_data['target'].position[0], event_data['target'].position[1])
        else:  # if not - it must be a tuple
            target = event_data['target']
        launcher = self.owner  # default
        launcher.location.action_mgr.register_action(0, actions.act_launch_projectile, reaction['projectile'],
                                                     launcher, target, self.message_color)
        return {'success': True}  # PLACEHOLDER launch is always successiful now

    def react_heal(self, reaction, event_data):
        """ Reaction, that heals """
        reaction_result = {'success': False}  # result dict
        # if there will be different reaction targets - specify here
        target = self.owner  # default
        healed_hp = self.owner.heal(reaction['heal'], target)
        if healed_hp > 0:  # success if some hp healed
            reaction_result['success'] = True
        return reaction_result

    def react_kill_entity(self, reaction, event_data):
        """ Reaction, that kills reaction target from location """
        reaction_result = {'success': False}  # result dict
        # if there will be different reaction targets - specify here
        target = self.owner  # default
        if reaction['target'] == 'thrown':
            target = self._owner  # set target to thrown item
        if reaction['target'] == 'ammo':
            target = self._owner  # set target to ammo item
        if target:
            target.location.dead.append(target)
            reaction_result['success'] = True
        return reaction_result

    def react_apply_timed_effect(self, reaction, event_data):
        """ Reaction, that applies a timed effect """
        # if there will be different reaction targets - specify here
        target = self.owner  # default
        if reaction['target'] == 'projectile_hit_entity':
            target = event_data['target']
            if isinstance(event_data['owner'].launcher, game_logic.Player):  # if player attacks - inform him of effect
                game_logic.Game.add_message(message=_('{ent_name} is now {eff_name}: {eff_descr} for {time} ticks.').
                                                                    format(ent_name=str(target), eff_name=
                                                                        _(reaction['effect'].eff).
                                                                        capitalize().replace('_', ' '),
                                                                        eff_descr=reaction['effect'].description,
                                                                        time=str(reaction['time'])),
                                            level='PLAYER', color=self.message_color)
        self.owner.location.action_mgr.register_action(reaction['time'], actions.act_apply_timed_effect,
                                                       target, reaction['effect'], self.message_color)
        if isinstance(target, game_logic.Player):  # if player uses - inform him of effect
            game_logic.Game.add_message(message=_('{eff_name}: {eff_descr} for {time} ticks.').format(eff_name=
                                                                 _(reaction['effect'].eff).
                                                                 capitalize().replace('_', ' '),
                                                                 eff_descr=reaction['effect'].description,
                                                                 time=str(reaction['time'])),
                                        level='PLAYER', color=self.message_color)
        return {'success': True}  # PLACEHOLDER effect applying is always successiful now
    
    def react_remove_effect(self, reaction, event_data):
        """ Reaction, that removes effects """
        reaction_result = {'success': False, 'removed_effects_count': 0}  # result dict
        # if there will be different reaction targets - specify here
        target = self.owner  # default
        if reaction['effects_number'] == 'all':  # if all effects has to be removed
            r = 0  # number of removed effects
            for effect in target.effects[:]:  # remove all such effects
                if effect.eff == reaction['effect'].eff:
                    target.effects.remove(effect)
                    r += 1
            if r > 0:  # if at least one effect removed - reaction successiful
                reaction_result['success'] = True
                reaction_result['removed_effects_count'] = r
            if isinstance(target, game_logic.Player):  # if player uses - inform him of effect
                game_logic.Game.add_message(message=
                    _('{ability_name}: removed all {eff_name} effects.').format(
                        ability_name=_(self.name).capitalize(),
                        eff_name=_(reaction['effect'].eff).upper()),
                    level='PLAYER', color=self.message_color)
        else:  # if specific number of effects has to be removed
            # choose needed effects
            needed_effects = [e for e in target.effects if e.eff == reaction['effect'].eff]
            if len(needed_effects) > 0:  # if there are
                r = 0  # number of removed effects
                # if effects to be removed number less than present effects
                if len(needed_effects) < reaction['effects_number']:
                    # remove random effects
                    for effect in random.sample(needed_effects, reaction['effects_number']):
                        target.effects.remove(effect)
                        r += 1
                    if isinstance(target, game_logic.Player):  # if player uses - inform him of effect
                        game_logic.Game.add_message(message=
                            _('{ability_name}: removed {eff_number} {eff_name} effects.').format(
                                ability_name=_(self.name).capitalize(),
                                eff_number=str(len(needed_effects)),
                                eff_name=_(reaction['effect'].eff).upper()),
                            level='PLAYER', color=self.message_color)
                else:  # if not
                    for effect in target.effects[:]:  # remove all such effects
                        if effect.eff == reaction['effect'].eff:
                            target.effects.remove(effect)
                            r += 1
                    if isinstance(target, game_logic.Player):  # if player uses - inform him of effect
                        game_logic.Game.add_message(message=
                            _('{ability_name}: removed all {eff_name} effects.').format(
                                ability_name=_(self.name).capitalize(),
                                eff_name=_(reaction['effect'].eff).upper()),
                            level='PLAYER', color=self.message_color)
                if r > 0:  # if at least one effect removed - reaction successiful
                    reaction_result['success'] = True
                    reaction_result['removed_effects_count'] = r
        return reaction_result

    def react_deal_periodic_damage(self, reaction, event_data):
        """ Reaction, that applies periodic damage """
        # if there will be different reaction targets - specify here
        target = event_data['target']  # default target and attacker
        attacker = event_data['attacker']
        self.owner.location.action_mgr.register_action(1, actions.act_deal_periodic_damage,
                                                       self.owner.location.action_mgr, target,
                                                       pickle.loads(pickle.dumps(reaction['effect'])),
                                                       reaction['damage'],
                                                       reaction['dmg_type'], reaction['period'],
                                                       reaction['whole_time'], self.message_color,
                                                       reaction['stackable'])
        # doing pickle copy of effect to make every stack separate
        if isinstance(attacker, game_logic.Player):  # if player applies - inform him of effect
            game_logic.Game.add_message(message=
                _('{target_name} is {eff_name}.').format(
                    target_name=str(target).capitalize(),
                    eff_name=_(reaction['effect'].eff).lower()),
                level='PLAYER', color=self.message_color)
        return {'success': True}  # PLACEHOLDER applying periodic damage is always successiful now


class AbilityTemplate:
    """ A class intended to be stored in JSON and generate an Ability object """
    def __init__(self, data_id, stored_class_name, init_kwargs=None):
        """
        :param data_id: and ID string 
        :param stored_class_name: a name of class stored in this template
        :param init_kwargs: a dict with arguments to pass to __init__ method of newly created class
        """
        self.data_id = data_id
        self.stored_class_name = stored_class_name
        if init_kwargs:
            self.init_kwargs = init_kwargs
        else:
            self.init_kwargs = {}

    def get_stored_object(self):
        """
        Method to get new object of stored class
        :return: object of stored class 
        """
        if self.stored_class_name in globals():
            new_ability = globals()[self.stored_class_name](**self.init_kwargs)
            new_ability.data_id = self.data_id
            return new_ability
        else:
            raise RuntimeError('There are no such class in abilities module: ' + self.stored_class_name)


# ============================== UTILITY FUNCTIONS ===========================================


def check_conditions(conditions, data):
    """ Function that checks if conditions are met """
    expression = ''
    for cond in conditions:
        if isinstance(cond, Condition):
            expression += str(cond.evaluate(**data))  # add evaluation of condition result
        else:
            expression += cond  # add '(', ')', 'and', 'or' etc
    return bool_eval.nested_bool_eval(expression)  # evaluate result expression and return

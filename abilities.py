"""
    This file contains abilities.
"""
import game_logic
import events
import actions
import bool_eval

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
        # TODO: get rid of eval()
        if self.condition == 'OWNER_HP_PERCENT':  # OWNER_HP_PERCENT condition
            sign = self.kwargs['sign']
            number = self.kwargs['number']
            return eval(
                str(kwargs['owner'].hp / kwargs['owner'].maxhp) + sign + str(number))  # check hp percent condition
        if self.condition == 'EQUIPPED' and kwargs['owner']:  # EQUIPPED condition
            if kwargs['owner_item'] in kwargs['owner'].equipment.values():  # check if item equipped
                return True
            else:
                return False
        if self.condition == 'USED':  # USED condition
            if kwargs['owner_item'] == kwargs['item']:  # check if item used is item with ability
                return True
            else:
                return False
        if self.condition == 'MOVED_ON':  # MOVED_ON condition
            if kwargs['owner'].position == kwargs['entity'].position:  # check if positions of owner and entity match
                return True
            else:
                return False
        if self.condition == 'TARGET_IN_RANGE':  # TARGET IN RANGE condition
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
        return True


class Ability(events.Observer):
    """ Base class for Ability object """

    def __init__(self, owner, trigger, reactions, conditions=None, enabled=True, cooldown=0, name='', ability_id='',
                 description='', message_color=None, ai_info=None):
        self.owner = owner
        if isinstance(owner, game_logic.Item):  # if it's an item - set owner to owning Entity
            self.owner_item = owner  # if Item - Item object
        else:
            self.owner_item = None  # if Item - Item object
        self.enabled = enabled  # is ability enabled or not
        self.trigger = trigger  # ability trigger
        self.conditions = conditions  # ability condition
        self.reactions = reactions  # ability reactions
        self.cooldown = cooldown  # ability internal cooldown in ticks
        self.ticks_to_cd = 0  # ticks to cooldown
        self.ability_on_cd = False  # is ability on cd
        self.name = name  # name of the ability
        self.ability_id = ability_id  # ability ID in dataset
        self.description = description  # description of ability
        self.ai_info = ai_info  # info for AI how and when to use the ability
        if message_color is None:
            self.message_color = [255, 255, 255]
        else:
            self.message_color = message_color  # if ability shows any messages - they use this color
        self.reobserve()

    def reobserve(self):
        """ Method that registers Ability to observe events """
        events.Observer.__init__(self)  # register self as observer
        self.observe(self.owner, self.on_event)
        self.observe('location', self.on_event)
        self.observe('time', self.on_event)

    def set_owner(self, owner):
        """ Method to set owner and refresh observer """
        self.close()  # unregister observing old owner
        try:  # if ability belongs to an item - check owner of item
            if owner.owner:  # if item is equipped or in inventory - set owning Entity
                self.owner = owner.owner
            else:
                self.owner = owner  # set owner
        except AttributeError:
            self.owner = owner  # set owner
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
                for reaction in self.reactions:
                    if 'chance' in reaction:  # if reaction occurs with some random chance (percent)
                        if random.randint(1, 100) > reaction['chance']:  # take a chance
                            self.react(reaction, data)
                            if self.cooldown > 0:  # if ability has cooldown
                                self.ability_on_cd = True  # start cooldown
                                self.ticks_to_cd = self.cooldown
                                events.Event(self.owner,
                                             {'type': 'ability_fired', 'ability': self})  # fire an ability event
                                events.Event('location', {'type': 'ability_fired', 'ability': self})
                    else:  # if not - react
                        self.react(reaction, data)
                        self.ability_on_cd = True  # start cooldown
                        self.ticks_to_cd = self.cooldown
                        events.Event(self.owner, {'type': 'ability_fired', 'ability': self})  # fire an ability event
                        events.Event('location', {'type': 'ability_fired', 'ability': self})

    def conditions_met(self, data):
        """ Method that checks if conditions are met """
        if not self.enabled:  # if not enabled - conditions aren't met by default
            return False
        expression = ''
        for cond in self.conditions:
            if isinstance(cond, Condition):
                # event data is passed to condition as is
                # if other kwargs needed - add here
                data.update({'owner': self.owner, 'owner_item': self.owner_item})
                if self.ai_info:  # if ai_info exists - pass some additional arguments
                    if self.ai_info['type'] == 'ranged_attack':
                        data.update({'range': self.ai_info['range']})
                expression += str(cond.evaluate(**data))  # add evaluation of condition result
            else:
                expression += cond  # add '(', ')', 'and', 'or' etc
        return bool_eval.nested_bool_eval(expression)  # evaluate result expression and return

    # TODO: decompose this method - separate each type of reaction to own method (or function)
    def react(self, reaction, event_data):
        """ Method that converts reaction dicts to game actions """
        if reaction['type'] == 'deal_damage':  # dealing damage reaction
            if reaction['target'] == 'attacker':  # if target is attacker
                damage_dealt = self.owner.deal_damage(event_data['attacker'], reaction['damage'], reaction['dmg_type'])
                game_logic.Game.add_message(
                    self.name + ': ' + event_data['attacker'].name + ' takes ' + str(damage_dealt) + ' ' +
                    str(reaction['dmg_type']) + ' damage!', 'PLAYER', self.message_color)
            if reaction['target'] == 'attacked_entity':  # if target is attacked entity (by melee attack i.e. )
                damage_dealt = self.owner.deal_damage(event_data['target'], reaction['damage'], reaction['dmg_type'])
                game_logic.Game.add_message(
                    self.name + ': ' + event_data['target'].name + ' takes ' + str(damage_dealt) + ' ' +
                    reaction['dmg_type'] + ' damage!', 'PLAYER', self.message_color)
            if reaction['target'] == 'mover':  # if target is mover
                damage_dealt = self.owner.deal_damage(event_data['entity'], reaction['damage'], reaction['dmg_type'])
                game_logic.Game.add_message(
                    self.name + ': ' + event_data['entity'].name + ' takes ' + str(damage_dealt) + ' ' +
                    str(reaction['dmg_type']) + ' damage!', 'PLAYER', self.message_color)
        if reaction['type'] == 'apply_timed_effect':  # applying timed effect reaction
            if reaction['target'] == 'item_owner':  # if target is owner of item
                self.owner.location.action_mgr.register_action(reaction['time'], actions.act_apply_timed_effect,
                                                               self.owner, reaction['effect'])
                if isinstance(self.owner, game_logic.Player):  # if player uses - inform him of effect
                    game_logic.Game.add_message(reaction['effect'].eff.capitalize().replace('_', ' ') + ': ' +
                                                reaction['effect'].description + ' for ' + str(reaction['time']) +
                                                ' ticks.', 'PLAYER', self.message_color)
        if reaction['type'] == 'remove_effect':  # remove effect reaction
            if reaction['target'] == 'item_owner':  # if target is owner of item
                if reaction['effects_number'] == 'all':  # if all effects has to be removed
                    for effect in self.owner.effects[:]:  # remove all such effects
                        if effect.eff == reaction['effect'].eff:
                            self.owner.effects.remove(effect)
                    if isinstance(self.owner, game_logic.Player):  # if player uses - inform him of effect
                        game_logic.Game.add_message(self.name.capitalize() + ': removed all ' +
                                                    reaction['effect'].eff.upper() + ' effects.',
                                                    'PLAYER', self.message_color)
                else:  # if specific number of effects has to be removed
                    # choose needed effects
                    needed_effects = [e for e in self.owner.effects if e.eff == reaction['effect'].eff]
                    if len(needed_effects) > 0:  # if there are
                        # if effects to be removed number less than present effects
                        if len(needed_effects) < reaction['effects_number']:
                            # remove random effects
                            for effect in random.sample(needed_effects, reaction['effects_number']):
                                self.owner.effects.remove(effect)
                            if isinstance(self.owner, game_logic.Player):  # if player uses - inform him of effect
                                game_logic.Game.add_message(self.name.capitalize() + ': removed ' +
                                                            str(len(needed_effects)) + ' ' +
                                                            reaction['effect'].eff.upper() + ' effects.',
                                                            'PLAYER', self.message_color)
                        else:  # if not
                            for effect in self.owner.effects[:]:  # remove all such effects
                                if effect.eff == reaction['effect'].eff:
                                    self.owner.effects.remove(effect)
                            if isinstance(self.owner, game_logic.Player):  # if player uses - inform him of effect
                                game_logic.Game.add_message(self.name.capitalize() + ': removed all ' +
                                                            reaction['effect'].eff.upper() + ' effects.',
                                                            'PLAYER', self.message_color)
        if reaction['type'] == 'deal_periodic_damage':  # deal periodic damage
            if reaction['target'] == 'attacked_entity':  # if target is attacked entity (by melee attack i.e. )
                self.owner.location.action_mgr.register_action(1, actions.act_deal_periodic_damage,
                                                               self.owner.location.action_mgr, event_data['target'],
                                                               pickle.loads(pickle.dumps(reaction['effect'])),
                                                               reaction['damage'],
                                                               reaction['dmg_type'], reaction['period'],
                                                               reaction['whole_time'], reaction['stackable'])
                                                        # doing pickle copy of effect to make every stack separate


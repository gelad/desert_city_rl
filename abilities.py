"""
    This file contains abilities.
"""
import game_logic
import events
import actions
import bool_eval

import pickle
import random


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
        return True


class Ability(events.Observer):
    """ Base class for Ability object """

    def __init__(self, owner, trigger, reactions, conditions=None, enabled=True, cooldown=0, name='', description=''):
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
        self.name = name
        self.description = description
        self.reobserve()

    def reobserve(self):
        """ Method that registers Ability to observe events """
        events.Observer.__init__(self)  # register self as observer
        self.observe(self.owner, self.on_event)
        self.observe('location', self.on_event)

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
        if data['type'] == self.trigger and self.enabled:  # if trigger is valid
            expression = ''
            for cond in self.conditions:
                if isinstance(cond, Condition):
                    kwargs = {'owner': self.owner, 'owner_item': self.owner_item}  # if other kwargs needed - add here
                    if data['type'] == 'used_on_self':  # if used on self type - add used item
                        kwargs.update({'item': data['item']})
                    if data['type'] == 'entity_moved':  # if moved event type - add moved entity
                        kwargs.update({'entity': data['entity']})
                    if data['type'] == 'hit_basic_attack':  # if hit basic attack event type - add damage dealt
                        kwargs.update({'damage': data['damage']})
                    expression += str(cond.evaluate(**kwargs))  # add evaluation of condition result
                else:
                    expression += cond  # add '(', ')', 'and', 'or' etc
            if bool_eval.nested_bool_eval(expression):  # if conditions are passed - react
                for reaction in self.reactions:
                    if 'chance' in reaction:  # if reaction occurs with some random chance (percent)
                        if random.randint(1, 100) > reaction['chance']:  # take a chance
                            self.react(reaction, data)
                    else:  # if not - react
                        self.react(reaction, data)
                events.Event(self.owner, {'type': 'ability_fired', 'ability': self})  # fire an ability event
                events.Event('location', {'type': 'ability_fired', 'ability': self})

    def react(self, reaction, event_data):
        """ Method that converts reaction dicts to game actions """
        if reaction['type'] == 'deal_damage':  # dealing damage reaction
            if reaction['target'] == 'attacker':  # if target is attacker
                damage_dealt = self.owner.deal_damage(event_data['attacker'], reaction['damage'], reaction['dmg_type'])
                game_logic.Game.add_message(
                    self.name + ': ' + event_data['attacker'].name + ' takes ' + str(damage_dealt) + ' damage!',
                    'PLAYER', [255, 255, 255])
            if reaction['target'] == 'mover':  # if target is mover
                damage_dealt = self.owner.deal_damage(event_data['entity'], reaction['damage'], reaction['dmg_type'])
                game_logic.Game.add_message(
                    self.name + ': ' + event_data['entity'].name + ' takes ' + str(damage_dealt) + ' damage!',
                    'PLAYER', [255, 255, 255])
        if reaction['type'] == 'apply_timed_effect':  # applying timed effect reaction
            if reaction['target'] == 'item_owner':  # if target is owner of item
                self.owner.location.action_mgr.register_action(reaction['time'], actions.act_apply_timed_effect,
                                                               self.owner, reaction['effect'])
                color = [255, 255, 255]
                if reaction['effect'].eff == 'HASTE': color = [255, 255, 0]
                game_logic.Game.add_message(reaction['effect'].eff.capitalize() + ': all actions quickened for ' +
                                            str(reaction['time']) + ' ticks.', 'PLAYER', color)
        if reaction['type'] == 'deal_periodic_damage':  # deal periodic damage
            if reaction['target'] == 'attacked_entity':  # if target is attacked entity (by melee attack i.e. )
                self.owner.location.action_mgr.register_action(1, actions.act_deal_periodic_damage,
                                                               self.owner.location.action_mgr, event_data['target'],
                                                               pickle.loads(pickle.dumps(reaction['effect'])),
                                                               reaction['damage'],
                                                               reaction['dmg_type'], reaction['period'],
                                                               reaction['whole_time'], reaction['stackable'])
                                                        # doing pickle copy of effect to make every stack separate


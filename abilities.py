"""
    This file contains abilities.
"""
import game_logic
import events
import bool_eval


class Condition:
    """ Class for ability condition """

    def __init__(self, condition, **kwargs):
        self.condition = condition  # condition identificator
        self.kwargs = kwargs  # arguments to check condition

    def evaluate(self, **kwargs):
        """ Method to evaluate condition, returning True or False """
        # TODO: get rid of eval()
        if self.condition == 'OWNER_HP_PERCENT':
            sign = self.kwargs['sign']
            number = self.kwargs['number']
            return eval(
                str(kwargs['owner'].hp / kwargs['owner'].maxhp) + sign + str(number))  # check hp percent condition
        return False


class Ability(events.Observer):
    """ Base class for Ability object """

    def __init__(self, owner, trigger, reactions, conditions=None, disabled=False, name='', description=''):
        self.owner = owner
        self.disabled = disabled  # is ability disabled or not
        self.trigger = trigger  # ability trigger
        self.conditions = conditions  # ability condition
        self.reactions = reactions  # ability reactions
        self.name = name
        self.description = description
        events.Observer.__init__(self)  # register self as observer
        self.observe(owner, self.on_event_owner)

    def set_owner(self, owner):
        """ Method to set owner and refresh observer """
        self.close()  # unregister observing old owner
        if isinstance(owner, game_logic.Item):  # if it's an item - set owner to owning Entity
            if owner.owner:
                self.owner = owner.owner
            else:
                self.owner = owner  # set owner
        else:
            self.owner = owner  # set owner
        events.Observer.__init__(self)  # register observing new owner
        self.observe(owner, self.on_event_owner)

    def on_event_owner(self, data):
        """ Method that is called if any owner-related event fires """
        if data['type'] == self.trigger and not self.disabled:  # if trigger is valid
            expression = ''
            for cond in self.conditions:
                if isinstance(cond, Condition):
                    kwargs = {'owner': self.owner}  # if other kwargs needed - add here
                    expression += str(cond.evaluate(**kwargs))  # add evaluation of condition result
                else:
                    expression += cond  # add '(', ')', 'and', 'or' etc
            if bool_eval.nested_bool_eval(expression):  # if conditions are passed - react
                for reaction in self.reactions:
                    self.react(reaction, data)
                events.Event(self.owner, {'type': 'ability_fired', 'ability': self})  # fire an ability event
                events.Event('location', {'type': 'ability_fired', 'ability': self})

    def react(self, reaction, event_data):
        """ Method that converts reaction dicts to game actions """
        if reaction['type'] == 'deal_damage':  # dealing damage reaction
            if reaction['target'] == 'attacker':  # if target is attacker
                self.owner.deal_damage(event_data['attacker'], reaction['damage'])
                game_logic.Game.add_message(
                    self.name + ': ' + event_data['attacker'].name + ' takes ' + str(reaction['damage']) + ' damage!',
                    'PLAYER', [255, 255, 255])

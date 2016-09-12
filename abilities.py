"""
    This file contains abilities.
"""
import game_logic
import events


class Condition:
    """ Class for ability condition """
    def __init__(self, condition, **kwargs):
        self.condition = condition  # condition identificator
        self.kwargs = kwargs  # arguments to check condition

    def evaluate(self, **kwargs):
        """ Method to evaluate condition, returning True or False """
        if self.condition == 'OWNER_HP_PERCENT':
            sign = self.kwargs['sign']
            number = self.kwargs['number']
            return eval(str(kwargs['owner'].hp / kwargs['owner'].maxhp)+sign+str(number))  # check hp percent condition
        return False


class Ability(events.Observer):
    """ Base class for Ability object """
    def __init__(self, owner, trigger, condition=None, disabled=False):
        self.owner = owner
        self.disabled = disabled  # is ability disabled or not
        self.trigger = trigger  # ability trigger
        self.condition = condition  # ability condition
        events.Observer.__init__(self)  # register self as observer
        self.observe(owner, self.on_event_owner)
        # TODO: implement ability actions

    def on_event_owner(self, data):
        """ Method that is called if any owner-related event fires """
        if data['type'] == self.trigger:
            print(self.condition.evaluate(owner=self.owner))

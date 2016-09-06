"""
    This file contains effects.
"""


class Effect:
    """ A base class of effect """
    def __init__(self, eff, magnitude):
        self.eff = eff  # an effect identificator
        self.magnitude = magnitude  # effect magnitude
        if eff == 'INCREASE_MELEE_DAMAGE': self.description = 'Increases melee damage by '+str(magnitude)
        if eff == 'HEAL': self.description = 'Heals '+str(magnitude)+' hitpoints.'

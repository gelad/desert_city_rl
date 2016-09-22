"""
    This file contains effects.
"""


class Effect:
    """ A base class of effect """
    def __init__(self, eff, magnitude):
        self.eff = eff  # an effect identificator
        self.magnitude = magnitude  # effect magnitude
        if eff == 'BLOCK_BASHING': self.description = 'Blocks ' + str(magnitude) + ' bashing damage'
        elif eff == 'BLOCK_SLASHING': self.description = 'Blocks ' + str(magnitude) + ' slashing damage'
        elif eff == 'BLOCK_PIERCING': self.description = 'Blocks ' + str(magnitude) + ' piercing damage'
        elif eff == 'BLOCK_FIRE': self.description = 'Blocks ' + str(magnitude) + ' fire damage'
        elif eff == 'BLOCK_COLD': self.description = 'Blocks ' + str(magnitude) + ' cold damage'
        elif eff == 'BLOCK_LIGHTNING': self.description = 'Blocks ' + str(magnitude) + ' lightning damage'
        elif eff == 'BLOCK_POISON': self.description = 'Blocks ' + str(magnitude) + ' poison damage'
        elif eff == 'BLOCK_ACID': self.description = 'Blocks ' + str(magnitude) + ' acid damage'
        elif eff == 'BLOCK_DEATH': self.description = 'Blocks ' + str(magnitude) + ' death damage'
        elif eff == 'BLOCK_MENTAL': self.description = 'Blocks ' + str(magnitude) + ' mental damage'
        elif eff == 'BLOCK_STRANGE': self.description = 'Blocks ' + str(magnitude) + ' strange damage'
        elif eff == 'INCREASE_MELEE_DAMAGE': self.description = 'Increases melee damage by '+str(magnitude)
        elif eff == 'INCREASE_RANGED_DAMAGE': self.description = 'Increases ranged damage by ' + str(magnitude)
        elif eff == 'HEAL': self.description = 'Heals '+str(magnitude)+' hitpoints'
        elif eff == 'HASTE': self.description = 'Quickens all actions by ' + str(magnitude) + '%'
        elif eff == 'POISONED': self.description = 'Affected by poison'
        else: self.description = eff  # if no description - simply set description to effect name

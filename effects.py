"""
    This file contains effects.
"""
from messages import _  # translation function

# effect descriptions, now stored here
eff_descriptions = {
        'BLOCK_BASHING': 'Blocks {magn} bashing damage',
        'BLOCK_SLASHING': 'Blocks {magn} slashing damage',
        'BLOCK_PIERCING': 'Blocks {magn} piercing damage',
        'BLOCK_FIRE': 'Blocks {magn} fire damage',
        'BLOCK_COLD': 'Blocks {magn} cold damage',
        'BLOCK_LIGHTNING': 'Blocks {magn} lightning damage',
        'BLOCK_POISON': 'Blocks {magn} poison damage',
        'BLOCK_ACID': 'Blocks {magn} acid damage',
        'BLOCK_DEATH': 'Blocks {magn} death damage',
        'BLOCK_MENTAL': 'Blocks {magn} mental damage',
        'BLOCK_STRANGE': 'Blocks {magn} strange damage',
        'RESIST_BASHING': 'Resists {magn} bashing',
        'RESIST_SLASHING': 'Resists {magn} slashing',
        'RESIST_PIERCING': 'Resists {magn} piercing',
        'RESIST_FIRE': 'Resists {magn} fire',
        'RESIST_COLD': 'Resists {magn} cold',
        'RESIST_LIGHTNING': 'Resists {magn} lightning',
        'RESIST_POISON': 'Resists {magn} poison',
        'RESIST_ACID': 'Resists {magn} acid',
        'RESIST_DEATH': 'Resists {magn} death',
        'RESIST_MENTAL': 'Resists {magn} mental',
        'RESIST_STRANGE': 'Resists {magn} strange',
        'INCREASE_MELEE_DAMAGE': 'Increases melee damage by {magn}',
        'INCREASE_RANGED_DAMAGE': 'Increases ranged damage by {magn}',
        'HASTE': 'Quickens all actions by {magn}%',
        'SLOWED': 'Slows all actions by {magn}%',
        'POISONED': 'Affected by poison',
        'HEAL': 'Heals {magn} hitpoints'
}


class Effect:
    """ A base class of effect """
    def __init__(self, eff, magnitude, categories=None, properties=None):
        self.eff = eff  # an effect identificator
        self.magnitude = magnitude  # effect magnitude
        if categories:
            self.categories = categories  # categories - a potion, a sword, etc
        else:
            self.categories = set()
        if properties:
            self.properties = properties  # properties - armor values, accuracy for weapons, etc
        else:
            self.properties = {}

    @property
    def description(self):
        kwargs = self.properties
        if self.eff in eff_descriptions:
            descr = eff_descriptions[self.eff]
        else:
            descr = self.eff
        return _(descr).format(magn=str(self.magnitude), **kwargs)

    def __getattr__(self, item):
        """ Search for missing attributes in properties """
        if item == 'properties':  # to prevent recursion
            return super().__getattribute__(item)
        if item in self.properties:
            return self.properties[item]
        raise AttributeError()

    def __setattr__(self, key, value):
        """ Search for missing attributes in properties """
        if 'properties' in self.__dict__:
            if key in self.properties:
                self.properties[key] = value
                return
        return super().__setattr__(key, value)


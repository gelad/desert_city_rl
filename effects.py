"""
    This file contains effects.
"""
from messages import _  # translation function


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
        # BLOCK effects
        if eff == 'BLOCK_BASHING': self._description = 'Blocks {magn} bashing damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_SLASHING': self._description = 'Blocks {magn} slashing damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_PIERCING': self._description = 'Blocks {magn} piercing damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_FIRE': self._description = 'Blocks {magn} fire damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_COLD': self._description = 'Blocks {magn} cold damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_LIGHTNING': self._description = 'Blocks {magn} lightning damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_POISON': self._description = 'Blocks {magn} poison damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_ACID': self._description = 'Blocks {magn} acid damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_DEATH': self._description = 'Blocks {magn} death damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_MENTAL': self._description = 'Blocks {magn} mental damage'.format(magn=str(magnitude))
        elif eff == 'BLOCK_STRANGE': self._description = 'Blocks {magn} strange damage'.format(magn=str(magnitude))
        # resistance effects
        elif eff == 'RESIST_BASHING': self._description = 'Resists {magn} bashing'.format(magn=str(magnitude))
        elif eff == 'RESIST_SLASHING': self._description = 'Resists {magn} slashing'.format(magn=str(magnitude))
        elif eff == 'RESIST_PIERCING': self._description = 'Resists {magn} piercing'.format(magn=str(magnitude))
        elif eff == 'RESIST_FIRE': self._description = 'Resists {magn} fire'.format(magn=str(magnitude))
        elif eff == 'RESIST_COLD': self._description = 'Resists {magn} cold'.format(magn=str(magnitude))
        elif eff == 'RESIST_LIGHTNING': self._description = 'Resists {magn} lightning'.format(magn=str(magnitude))
        elif eff == 'RESIST_POISON': self._description = 'Resists {magn} poison'.format(magn=str(magnitude))
        elif eff == 'RESIST_ACID': self._description = 'Resists {magn} acid'.format(magn=str(magnitude))
        elif eff == 'RESIST_DEATH': self._description = 'Resists {magn} death'.format(magn=str(magnitude))
        elif eff == 'RESIST_MENTAL': self._description = 'Resists {magn} mental'.format(magn=str(magnitude))
        elif eff == 'RESIST_STRANGE': self._description = 'Resists {magn} strange'.format(magn=str(magnitude))
        # buff/debuff effects
        elif eff == 'INCREASE_MELEE_DAMAGE': self._description = 'Increases melee damage by {magn}'.format(magn=str(magnitude))
        elif eff == 'INCREASE_RANGED_DAMAGE': self._description = 'Increases ranged damage by {magn}'.format(magn=str(magnitude))
        elif eff == 'HASTE': self._description = 'Quickens all actions by {magn}%'.format(magn=str(magnitude))
        elif eff == 'SLOWED': self._description = 'Slows all actions by {magn}%'.format(magn=str(magnitude))
        elif eff == 'POISONED': self._description = 'Affected by poison'
        elif eff == 'HEAL': self._description = 'Heals {magn} hitpoints'.format(magn=str(magnitude))
        else: self._description = eff  # if no description - simply set description to effect name

    @property
    def description(self):
        return _(self._description)

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


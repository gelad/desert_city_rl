"""
    This file contains effects.
"""
from messages import _  # translation function


class Effect:
    """ A base class of effect """
    def __init__(self, eff, magnitude):
        self.eff = eff  # an effect identificator
        self.magnitude = magnitude  # effect magnitude
        # BLOCK effects
        if eff == 'BLOCK_BASHING': self.description = _('Blocks {magn} bashing damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_SLASHING': self.description = _('Blocks {magn} slashing damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_PIERCING': self.description = _('Blocks {magn} piercing damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_FIRE': self.description = _('Blocks {magn} fire damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_COLD': self.description = _('Blocks {magn} cold damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_LIGHTNING': self.description = _('Blocks {magn} lightning damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_POISON': self.description = _('Blocks {magn} poison damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_ACID': self.description = _('Blocks {magn} acid damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_DEATH': self.description = _('Blocks {magn} death damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_MENTAL': self.description = _('Blocks {magn} mental damage').format(magn=str(magnitude))
        elif eff == 'BLOCK_STRANGE': self.description = _('Blocks {magn} strange damage').format(magn=str(magnitude))
        # resistance effects
        elif eff == 'RESIST_BASHING': self.description = _('Resists {magn} bashing').format(magn=str(magnitude))
        elif eff == 'RESIST_SLASHING': self.description = _('Resists {magn} slashing').format(magn=str(magnitude))
        elif eff == 'RESIST_PIERCING': self.description = _('Resists {magn} piercing').format(magn=str(magnitude))
        elif eff == 'RESIST_FIRE': self.description = _('Resists {magn} fire').format(magn=str(magnitude))
        elif eff == 'RESIST_COLD': self.description = _('Resists {magn} cold').format(magn=str(magnitude))
        elif eff == 'RESIST_LIGHTNING': self.description = _('Resists {magn} lightning').format(magn=str(magnitude))
        elif eff == 'RESIST_POISON': self.description = _('Resists {magn} poison').format(magn=str(magnitude))
        elif eff == 'RESIST_ACID': self.description = _('Resists {magn} acid').format(magn=str(magnitude))
        elif eff == 'RESIST_DEATH': self.description = _('Resists {magn} death').format(magn=str(magnitude))
        elif eff == 'RESIST_MENTAL': self.description = _('Resists {magn} mental').format(magn=str(magnitude))
        elif eff == 'RESIST_STRANGE': self.description = _('Resists {magn} strange').format(magn=str(magnitude))
        # buff/debuff effects
        elif eff == 'INCREASE_MELEE_DAMAGE': self.description = _('Increases melee damage by {magn}').format(magn=str(magnitude))
        elif eff == 'INCREASE_RANGED_DAMAGE': self.description = _('Increases ranged damage by {magn}').format(magn=str(magnitude))
        elif eff == 'HASTE': self.description = _('Quickens all actions by {magn}%').format(magn=str(magnitude))
        elif eff == 'SLOWED': self.description = _('Slows all actions by {magn}%').format(magn=str(magnitude))
        elif eff == 'POISONED': self.description = _('Affected by poison')
        elif eff == 'HEAL': self.description = _('Heals {magn} hitpoints').format(magn=str(magnitude))
        else: self.description = eff  # if no description - simply set description to effect name

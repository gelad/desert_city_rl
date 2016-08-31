"""
    This file contains FOV (Field Of View) and LOS (Line Of Sight) related things.
"""
import tdl


def get_fov(x, y, loc, radius):
    """ Function that calculates FOV. Now just a wrapper around tdl function """
    # TODO: fix bug, that set contains out-of-bounds cells
    return tdl.map.quick_fov(x, y, loc.is_cell_transparent, 'SHADOW', radius)

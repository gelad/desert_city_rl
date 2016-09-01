"""
    This file contains FOV (Field Of View) and LOS (Line Of Sight) related things.
"""
import tdl


def get_fov(x, y, loc, radius):
    """ Function that calculates FOV. Now just a wrapper around tdl function """
    q_fov = tdl.map.quick_fov(x, y, loc.is_cell_transparent, 'BASIC', radius)  # get a FOV set of (x,y) points
    out_of_bounds = set()  # a set of out of bounds points
    for point in q_fov:  # check if any of them are out of bounds (tdl includes borders)
        if not loc.is_in_boundaries(point[0], point[1]):
            out_of_bounds.add(point)  # add out of bounds point to set
    q_fov.difference_update(out_of_bounds)  # remove out of bounds points
    return q_fov


def get_los(x1, y1, x2, y2):
    """ Function that calculates LOS. Now just a wrapper around tdl function """
    return tdl.map.bresenham(x1, y1, x2, y2)

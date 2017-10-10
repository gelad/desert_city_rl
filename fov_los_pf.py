"""
    This file contains FOV (Field Of View) and LOS (Line Of Sight) related things.
"""
import tdl
from pypaths import astar

import math


def get_fov(x, y, loc, radius):
    """ Function that calculates FOV. Now just a wrapper around tdl function """
    q_fov = tdl.map.quick_fov(x, y, loc.is_cell_transparent, 'PERMISSIVE8', radius)  # get a FOV set of (x,y) points
    out_of_bounds = set()  # a set of out of bounds points
    for point in q_fov:  # check if any of them are out of bounds (tdl includes borders)
        if not loc.is_in_boundaries(point[0], point[1]):
            out_of_bounds.add(point)  # add out of bounds point to set
    q_fov.difference_update(out_of_bounds)  # remove out of bounds points
    return q_fov


def line(x1, y1, x2, y2):
    """ Function that returns points in line. Now just a wrapper around tdl function """
    return tdl.map.bresenham(x1, y1, x2, y2)


def ray(x1, y1, x2, y2, width, height, power):
    """ Function that casts a ray through two points """
    rng = math.hypot(x2 - x1, y2 - y1)
    ax = (x2 - x1) / rng
    ay = (y2 - y1) / rng
    x = x1
    y = y1
    ray = []
    for i in range(power):  # cast the ray
        x += ax
        y += ay
        if x < 0 or y < 0 or x > width or y > height:  # if ray is out of boundaries
            break
        ray.append((round(x), round(y)))
    return ray


def ray_angle(x1, y1, angle, width, height, power):
    """ Function that casts a ray from point at given angle (in degrees) """
    pi = 3.141592  # precise enough
    ax = math.sin(angle * (pi / 180))
    ay = -math.cos(angle * (pi / 180))  # minus because coord system is turned upside-down
    x = x1
    y = y1
    ray = []
    for i in range(power):  # cast the ray
        x += ax
        y += ay
        if x < 0 or y < 0 or x > width or y > height:  # if ray is out of boundaries
            break
        ray.append((round(x), round(y)))
    return ray


def get_path(loc, x1, y1, x2, y2):
    """ Function that returns path, using A* algorithm """
    if loc.get_move_cost((x1, y1), (x2, y2)) == 0:  # if cell is impassable - return empty path without using A*
        return []
    finder = astar.pathfinder(neighbors=grid_neighbors_diagonal(loc.width, loc.height),
                              cost=loc.get_move_cost)
    length, path = finder((x1, y1), (x2, y2))
    del path[0]  # remove first element - it's the start
    return path


def grid_neighbors_diagonal(height, width):
    """
    Calculate neighbors for a simple grid where
    a movement can be made up, down, left, right or diagonal.

    """

    def func(coord):
        neighbor_list = [(coord[0], coord[1] + 1),
                         (coord[0], coord[1] - 1),
                         (coord[0] + 1, coord[1]),
                         (coord[0] - 1, coord[1]),
                         (coord[0] - 1, coord[1] + 1),
                         (coord[0] + 1, coord[1] - 1),
                         (coord[0] - 1, coord[1] - 1),
                         (coord[0] + 1, coord[1] + 1)]

        return [c for c in neighbor_list
                if c != coord
                and c[0] >= 0 and c[0] < width
                and c[1] >= 0 and c[1] < height]

    return func

"""
    This file contains FOV (Field Of View) and LOS (Line Of Sight) related things.
"""
import tdl
import math
import pathfinding
import los
import fov


def get_fov(x, y, loc, radius, visit_func):
    """ Function that calculates FOV. Now just a wrapper around tdl function """
    fov.fieldOfView(x, y, loc.width, loc.height, radius, visit_func, loc.is_cell_transparent)


def line(x1, y1, x2, y2):
    """ Function that returns points in line. """
    return los.get_line((x1, y1), (x2, y2))


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
    finder = pathfinding.pathfinder(neighbors=pathfinding.grid_neighbors_diagonal(loc.width, loc.height),
                                    cost=loc.get_move_cost)
    length, path = finder((x1, y1), (x2, y2))
    del path[0]  # remove first element - it's the start
    return path

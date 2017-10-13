"""
    This file contains raycasting functions.
"""
import math


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

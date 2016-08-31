"""
    This file contains game logic objects.
"""
import actions
import fov_los

import random


class Cell:
    """
        Class represents a single cell in location grid
    """
    def __init__(self, tile_type, blocks_move=False, blocks_los=False, explored=False):
        self.explored = explored  # is tile explored?
        self.tile = tile_type  # tile type for drawing purposes (i.e. 'WALL', 'FLOOR')
        self.blocks_move = blocks_move  # is tile blocking movement?
        self.blocks_los = blocks_los  # is tile blocking line of sight?
        self.entities = []  # entities, positioned in this tile

    def is_movement_allowed(self):
        """ Method returns if tile is passable """
        if self.blocks_move:
            return False
        for ent in self.entities:
            if ent.occupies_tile:
                return False
        return True

    def is_there_a(self, thing):
        """ Method for checking some kind of entity present in cell(monster, door, item, etc) """
        # TODO: add method for multiple entities (if needed a list of items or monsters)
        for ent in self.entities:
            if type(ent) == thing:
                return ent
        return False

    def is_transparent(self):
        """ Method that returns if the cell is transparent for light """
        if self.blocks_los:  # check if tile blocks los itself
            return False
        for ent in self.entities:  # check if any of placed entities blocks los
            if ent.blocks_los:
                return False
        return True


class Entity:
    """
        Base class for all game entities - monsters, items, walls, etc.
    """
    def __init__(self, name='', char=' ', location=None, position=None, occupies_tile=False, blocks_los=False):
        self.name = name  # entity name
        self.location = location  # Location object, where entity is placed
        self.position = position  # (x, y) tuple, represents position in the location
        self.occupies_tile = occupies_tile  # entity occupy tile? (no other occupying entity can be placed there)
        self.blocks_los = blocks_los  # is it blocking line of sight? walls do, monsters (usually) don't
        self.char = char  # char that represents entity in graphics ('@') TODO: move graphics info to render.py?


class BattleEntity:
    """
        Mixin class, adds combat related functionality to the Entity.
        Hp, taking/inflicting damage, that kind of stuff.
    """
    def __init__(self, hp):
        self.hp = hp  # current hitpoints
        self.maxhp = hp  # maximum hitpoints


class Seer(Entity):
    """
        Mixin class, adds visibility (FOV & LOS) functionality to Entity.
    """
    def __init__(self, sight_radius):
        self.sight_radius = sight_radius  # sight radius in tiles
        self.fov_set = ()  # field of view - set of (x, y) points

    def compute_fov(self):
        """ Method that calculates FOV """
        self.fov_set = fov_los.get_fov(self.position[0], self.position[1], self.location, self.sight_radius)
        if isinstance(self, Player):
            for point in self.fov_set:
                if self.location.is_in_boundaries(point[0], point[1]):
                    self.location.cells[point[0]][point[1]].explored = True

    def is_in_fov(self, x, y):
        """ Method that determines is a cell in Seer's FOV """
        return (x, y) in self.fov_set


class Actor(Entity):
    """
        Mixin class, adds acting functionality to the Entity.
        Time-system related stuff.
    """
    def __init__(self, speed, state='ready'):
        self.speed = speed  # overall speed factor of actions
        self.state = state  # actor state - ready, acting or withdrawal (for now)

    def move(self, dx, dy):
        """ Movement method, checks if it is allowed to move. For player, monster movement. """
        # checks if entity is positioned in location
        if self.position:
            new_x = self.position[0] + dx
            new_y = self.position[1] + dy
            # check if new position is in the location boundaries
            if self.location.is_in_boundaries(new_x, new_y):
                # checks if tile allows movement
                if self.location.cells[new_x][new_y].is_movement_allowed():
                    # remove from old cell
                    self.location.cells[self.position[0]][self.position[1]].entities.remove(self)
                    self.location.cells[new_x][new_y].entities.append(self)  # add to new cell
                    self.position = (new_x, new_y)  # update entity position
                    return True
        else:
            raise Exception('Attempted to move entity not positioned in any location. ', self.name)
        return False

    def close(self, door):
        """ Door closing method """
        if door:
            return door.close()
        else:
            raise Exception('Attempted to close non-existing door. ', self.name)

    def open(self, door):
        """ Door opening method """
        if door:
            return door.open()
        else:
            raise Exception('Attempted to open non-existing door. ', self.name)

    def perform(self, action, *args, **kwargs):
        """ Method for performing an action in a location (maybe in future will be actions outside)
             Handles state change """
        if self.location:
            if self.state == 'ready':
                self.location.action_mgr.register_action(self.speed, action, *args, **kwargs)
                self.state = 'performing'
                return True
            return False
        else:
            raise Exception('Attempted to perform action with entity not positioned in any location. ', self.name)


class Item (Entity):
    """
        Mixed class, simple Item.
    """
    def __init__(self, name, char):
        # calling constructors
        Entity.__init__(self, name=name, char=char, occupies_tile=False)


class Fighter(BattleEntity, Actor, Seer, Entity):
    """
        Mixed class, basic monster, that can participate in combat and perform actions.
    """
    def __init__(self, name, char, hp, speed, sight_radius, ai=None):
        # calling constructors of mixins
        Entity.__init__(self, name=name, char=char, occupies_tile=True)
        BattleEntity.__init__(self, hp)
        Actor.__init__(self, speed)
        Seer.__init__(self, sight_radius=sight_radius)
        self.ai = ai  # ai component - PLACEHOLDER for now


class Player(Fighter):
    """
        Child class, adds player-specific functionality to Fighter.
    """
    def __init__(self, name, char, hp, speed, sight_radius):
        # calling constructor of parent class
        Fighter.__init__(self, name=name, char=char, hp=hp,speed=speed, sight_radius=sight_radius, ai=None)


class Wall(BattleEntity, Entity):
    """
        Mixed class of a wall, that has HP and can be destroyed, but lacks acting ability.
    """
    def __init__(self, name, char, hp, blocks_los=True):
        Entity.__init__(self, name=name, char=char, occupies_tile=True, blocks_los=blocks_los)
        BattleEntity.__init__(self, hp)


class Door(BattleEntity, Entity):
    """
        Mixed class of a door, that has HP and can be destroyed, has open/closed state, blocks los when closed.
    """
    # TODO: handle blocks_los in opened/closed state
    def __init__(self, name, char_closed, char_open, hp, is_closed=True):
        self.char_closed = char_closed  # char representing closed door
        self.char_open = char_open  # char representing open door
        self.is_closed = is_closed  # is door closed or open
        if is_closed:
            blocks_los = True
        else:
            blocks_los = False
        self.__set_char()  # set current char for drawing purposes # TODO: move graphic to render
        Entity.__init__(self, name=name, char=self.char, occupies_tile=self.is_closed, blocks_los=blocks_los)
        BattleEntity.__init__(self, hp)

    def __set_char(self):
        """ Method sets current character to display according to open/closed state """
        if self.is_closed:
            self.char = self.char_closed
        else:
            self.char = self.char_open

    def open(self):
        """ Method that opens the door """
        if self.is_closed:
            self.is_closed = False
            self.occupies_tile = False
            self.__set_char()
            self.blocks_los = False
            return True  # if action successful
        return False  # if it's not

    def close(self):
        """ Method that closes the door """
        if not self.is_closed:
            self.is_closed = True
            self.occupies_tile = True
            self.__set_char()
            self.blocks_los = True
            return True  # if action successful
        return False  # if it's not


class Location:
    """
        Represents a location, has a grid (nested list) of Cells
    """
    def __init__(self, height, width):
        self.height = height  # height of location in tiles
        self.width = width  # width of location in tiles
        self.cells = []  # list of Cell objects
        self.action_mgr = actions.ActionMgr()  # action manager for this location
        # self.entities = []  # a list of Entities
        self.seers = []  # a list of Seer objects, to recompute their FOV if map changes
        # WARNING! it's a hack, graphic-related info stored in loc, to save/load it with the loc
        self.out_of_sight_map = {}  # dict for storing explored, but invisible tiles

    def is_in_boundaries(self, x, y):
        """ Method validating coordinates, to avoid out of range errors  """
        if (x >= 0) and (y >= 0) and (x < self.width) and (y < self.height):
            return True
        return False

    def generate(self, pattern):
        """ Mapgen method, mostly placeholder for now."""
        if pattern == 'clear':  # simply make a location full of sand tiles
            self.cells.clear()
            self.cells = [[Cell('SAND') for y in range(self.height)] for x in range(self.width)]
        if pattern == 'ruins':  # simply make a location of sand and few wall and door elements
            self.cells.clear()
            self.cells = [[Cell('SAND') for y in range(self.height)] for x in range(self.width)]
            random.seed()
            for i in range(1, random.randint(2, 40)):
                wall = Wall('Wall', '#', 100)
                self.place_entity(wall, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(1, random.randint(2, 20)):
                door = Door(name='Door', char_closed='+', char_open='.', hp=100, is_closed=True)
                self.place_entity(door, random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            for i in range(1, random.randint(2, 20)):
                item = Item(name='Boulder', char='*')
                self.place_entity(item, random.randint(0, self.width - 1), random.randint(0, self.height - 1))

    def place_entity(self, entity, x, y):
        """ Method that places given entity on the location """
        if self.is_in_boundaries(x, y):  # validate coordinates
            self.cells[x][y].entities.append(entity)  # add entity to Cell list
            entity.position = (x, y)  # update entity position
            entity.location = self  # update entity location
            if isinstance(entity, Seer):  # check if entity is a Seer
                entity.compute_fov()  # recompute it's FOV
                self.seers.append(entity)  # add it to Seers list
        else:
            raise Exception('Attempted to place entity outside of location.', entity.name)

    def is_cell_transparent(self, x, y):
        """ Method that determines, is cell at x, y is transparent """
        if self.is_in_boundaries(x, y):  # check if cell coords are in boundaries
            return self.cells[x][y].is_transparent()  # return if cell is transparent
        return False  # if out of bounds, edge of the map certainly block los ;)


class Game:
    """
        Representation of whole game model, list of locations, game state, some between-locations info in the future.
    """
    def __init__(self, game_type='new'):
        self.current_loc = None  # current location
        self.player = None  # player object
        self.state = ''  # game state, like 'playing', 'paused' etc
        self.locations = []  # list of locations
        self.time_system = actions.TimeSystem()  # time system object
        if game_type == 'new':  # constructor option for new game start
            self.new_game()

    def new_game(self):
        """ Method that starts a new game. Mostly a placeholder now. """
        self.current_loc = Location(100, 100)
        self.add_location(self.current_loc)
        self.current_loc.generate('ruins')
        self.player = Player('Player', '@', 10, 100, 23.5)  # TODO: lessen sight radius or optimize FOV algorithm
        self.current_loc.place_entity(self.player, 10, 10)

    def add_location(self, location):
        """ Method that adds a location to the game """
        self.time_system.register_act_mgr(location.action_mgr)  # register act manager to time system
        self.locations.append(location)


import player_input
import render


class Cell:
    """
        Class represents a single cell in location grid
    """
    def __init__(self, tile_type, blocks_move=False, blocks_los=False, explored=False):
        self.explored = explored  # is tile explored?
        self.type = tile_type  # tile type for drawing purposes (i.e. 'WALL', 'FLOOR')
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


class Entity:
    """
        Base class for all game entities - monsters, items, walls, etc.
    """
    def __init__(self, name, char=' ', location=None, position=None, occupies_tile=False, blocks_los=False):
        self.name = name  # entity name
        self.location = location  # Location object, where entity is placed
        self.position = position  # (x, y) tuple, represents position in the location
        self.occupies_tile = occupies_tile  # entity occupy tile? (no other occupying entity can be placed there)
        self.blocks_los = blocks_los  # is it blocking line of sight? walls do, monsters (usually) don't
        self.char = char  # char that represents entity in graphics ('@') TODO: move graphics info to render.py?

    def move(self, dx, dy):
        """ Movement method, checks if it is allowed to move. For player, monster movement. """
        # checks if entity is positioned in location
        if self.position:
            new_x = self.position[0] + dx
            new_y = self.position[1] + dy
            # check if new position is in the location boundaries
            if (new_x >= 0) and (new_y >= 0) and (new_x < self.location.width) and (new_y < self.location.height):
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


class BattleEntity:
    """
        Mixin class, adds combat related functionality to the Entity.
        Hp, taking/inflicting damage, that kind of stuff.
    """
    def __init__(self, hp):
        self.hp = hp  # current hitpoints
        self.maxhp = hp  # maximum hitpoints


class Actor:
    """
        Mixin class, adds acting functionality to the Entity.
        Time-system related stuff.
    """
    def __init__(self, speed):
        self.speed = speed  # overall speed factor of actions


class Fighter(BattleEntity, Actor, Entity):
    """
        Mixed class, basic monster, that can participate in combat and perform actions.
    """
    def __init__(self, name, char, hp, speed, ai=None):
        # calling constructors of mixins
        Entity.__init__(self, name=name, char=char, occupies_tile=True)
        BattleEntity.__init__(self, hp)
        Actor.__init__(self, speed)
        self.ai = ai  # ai component - PLACEHOLDER for now


class Wall(BattleEntity, Entity):
    """
        Mixed class of a wall, that has HP and can be destroyed, but lacks acting ability.
    """
    def __init__(self, name, char, hp, blocks_los=True):
        Entity.__init__(self, name=name, char=char, occupies_tile=True, blocks_los=blocks_los)
        BattleEntity.__init__(self, hp)


class Location:
    """
        Represents a location, has a grid (nested list) of Cells
    """
    def __init__(self, height, width):
        self.height = height  # height of location in tiles
        self.width = width  # width of location in tiles
        self.cells = []  # list of Cell objects
        # self.entities = []  # TODO: decide, is it necessary to store a list of all entities on map

    def generate(self, pattern):
        """ Mapgen method, mostly placeholder for now."""
        if pattern == 'clear':  # simply make a location full of sand tiles
            self.cells.clear()
            self.cells = [[Cell('SAND') for y in range(self.height)] for x in range(self.width)]

    def place_entity(self, entity, x, y):
        """ Method that places given entity on the location """
        if (x >= 0) and (y >= 0) and (x < self.width) and (y < self.height):  # validate coordinates
            self.cells[x][y].entities.append(entity)  # add entity to Cell list
            entity.position = (x, y)  # update entity position
            entity.location = self  # update entity location
        else:
            raise Exception('Attempted to place entity outside of location.', entity.name)


class Game:
    """
        Representation of whole game model, list of locations, game state, some between-locations info in the future.
    """
    def __init__(self, game_type='new'):
        self.current_loc = None  # current location
        self.player = None  # player object
        self.state = ''  # game state, like 'playing', 'paused' etc
        self.locations = []  # list of locations
        if game_type == 'new':  # constructor option for new game start
            self.new_game()

    def new_game(self):
        """ Method that starts a new game. """
        self.current_loc = Location(100, 100)
        self.locations.append(self.current_loc)
        self.current_loc.generate('clear')
        self.player = Fighter('Player', '@', 10, 100)
        self.current_loc.place_entity(self.player, 10, 10)
        self.state = 'playing'


def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        control_events = player_input.handle_input()  # get list of player desired actions
        for event in control_events:
            if event == 'exit':
                game.state = 'exit'
            if event == 'move_up':
                game.player.move(0, -1)
            if event == 'move_down':
                game.player.move(0, 1)
            if event == 'move_right':
                game.player.move(1, 0)
            if event == 'move_left':
                game.player.move(-1, 0)
        graphics.render_all(game.current_loc, game.player)  # call a screen rendering function

graphics = render.Graphics()
game = Game()
main_loop()

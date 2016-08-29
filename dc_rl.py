import player_input
import render

import random
import pickle


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

    def close(self, dx, dy):
        """ Door closing method """
        # checks if entity is positioned in location
        if self.position:
            door_x = self.position[0] + dx
            door_y = self.position[1] + dy
            # check is there a door
            if self.location.is_in_boundaries(door_x, door_y):
                for ent in self.location.cells[door_x][door_y].entities:
                    if type(ent) == Door:
                        return ent.close()
        else:
            raise Exception('Attempted to close door with entity not positioned in any location. ', self.name)
        return False

    def open(self, dx, dy):
        """ Door opening method """
        # checks if entity is positioned in location
        if self.position:
            door_x = self.position[0] + dx
            door_y = self.position[1] + dy
            # check is there a door
            if self.location.is_in_boundaries(door_x, door_y):
                for ent in self.location.cells[door_x][door_y].entities:
                    if type(ent) == Door:
                        return ent.open()
        else:
            raise Exception('Attempted to open door with entity not positioned in any location. ', self.name)
        return False


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


class Door(BattleEntity, Entity):
    """
        Mixed class of a door, that has HP and can be destroyed, has open/closed state.
    """
    # TODO: handle blocks_los in opened/closed state
    def __init__(self, name, char_closed, char_open, hp, blocks_los=True, is_closed=True):
        self.char_closed = char_closed  # char representing closed door
        self.char_open = char_open  # char representing open door
        self.is_closed = is_closed  # is door closed or open
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
            return True  # if action successful
        return False  # if it's not

    def close(self):
        """ Method that closes the door """
        if not self.is_closed:
            self.is_closed = True
            self.occupies_tile = True
            self.__set_char()
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
        # self.entities = []  # TODO: decide, is it necessary to store a list of all entities on map

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
                door = Door(name='Door', char_closed='+', char_open='.', hp=100, is_closed=False)
                self.place_entity(door, random.randint(0, self.width - 1), random.randint(0, self.height - 1))

    def place_entity(self, entity, x, y):
        """ Method that places given entity on the location """
        if self.is_in_boundaries(x, y):  # validate coordinates
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
        """ Method that starts a new game. Mostly a placeholder now. """
        self.current_loc = Location(100, 100)
        self.locations.append(self.current_loc)
        self.current_loc.generate('ruins')
        self.player = Fighter('Player', '@', 10, 100)
        self.current_loc.place_entity(self.player, 10, 10)
        self.state = 'playing'


# =========================== global functions, save/load, loop, etc =================================
def save_game(game):
    """ Game saving function """
    pickle.dump(game, open('savegame', 'wb'))


def load_game():
    """ Game loading function """
    try:
        loaded_game = pickle.load(open('savegame', 'rb'))
        if loaded_game.state == 'exit':  # TODO: find out why game saves in exit state
            loaded_game.state = 'playing'
        return loaded_game
    except FileNotFoundError:
        return False


def main_loop():
    """ Main game loop function """
    while not game.state == 'exit':
        commands = player_input.handle_input(game)  # get list of player commands
        player_x = game.player.position[0]
        player_y = game.player.position[1]
        loc = game.current_loc
        for command in commands:
            if command == 'exit':
                save_game(game)  # save game before exit
                game.state = 'exit'
            # TODO: make a move-open-attack handling function to avoid code duplication
            elif command == 'move_n':
                if not game.player.move(0, -1):
                    if loc.is_in_boundaries(player_x, player_y - 1):
                        door = loc.cells[player_x][player_y - 1].is_there_a(Door)
                        if door:
                            game.player.open(0, -1)
            elif command == 'move_s':
                if not game.player.move(0, 1):
                    if loc.is_in_boundaries(player_x, player_y + 1):
                        door = loc.cells[player_x][player_y + 1].is_there_a(Door)
                        if door:
                            game.player.open(0, 1)
            elif command == 'move_w':
                if not game.player.move(-1, 0):
                    if loc.is_in_boundaries(player_x - 1, player_y):
                        door = loc.cells[player_x - 1][player_y].is_there_a(Door)
                        if door:
                            game.player.open(-1, 0)
            elif command == 'move_e':
                if not game.player.move(1, 0):
                    if loc.is_in_boundaries(player_x + 1, player_y):
                        door = loc.cells[player_x + 1][player_y].is_there_a(Door)
                        if door:
                            game.player.open(1, 0)
            elif command == 'move_nw':
                if not game.player.move(-1, -1):
                    if loc.is_in_boundaries(player_x - 1, player_y - 1):
                        door = loc.cells[player_x - 1][player_y - 1].is_there_a(Door)
                        if door:
                            game.player.open(-1, -1)
            elif command == 'move_ne':
                if not game.player.move(1, -1):
                    if loc.is_in_boundaries(player_x + 1, player_y - 1):
                        door = loc.cells[player_x + 1][player_y - 1].is_there_a(Door)
                        if door:
                            game.player.open(1, -1)
            elif command == 'move_sw':
                if not game.player.move(-1, 1):
                    if loc.is_in_boundaries(player_x - 1, player_y + 1):
                        door = loc.cells[player_x - 1][player_y + 1].is_there_a(Door)
                        if door:
                            game.player.open(-1, 1)
            elif command == 'move_se':
                if not game.player.move(1, 1):
                    if loc.is_in_boundaries(player_x + 1, player_y + 1):
                        door = loc.cells[player_x + 1][player_y + 1].is_there_a(Door)
                        if door:
                            game.player.open(1, 1)
            elif command == 'close_n':
                game.player.close(0, -1)
            elif command == 'close_s':
                game.player.close(0, 1)
            elif command == 'close_w':
                game.player.close(-1, 0)
            elif command == 'close_e':
                game.player.close(1, 0)
            elif command == 'close_nw':
                game.player.close(-1, -1)
            elif command == 'close_ne':
                game.player.close(1, -1)
            elif command == 'close_sw':
                game.player.close(-1, 1)
            elif command == 'close_se':
                game.player.close(1, 1)
        graphics.render_all(game.current_loc, game.player, game)  # call a screen rendering function

graphics = render.Graphics()
game = load_game()
if not game:
    game = Game()
main_loop()

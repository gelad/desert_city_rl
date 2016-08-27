import tdl
import player_input
import render


class Cell:
    def __init__(self, tile_type, glyph, blocks_move=False, blocks_los=False, explored=False):
        self.explored = explored
        self.type = tile_type
        self.blocks_move = blocks_move
        self.blocks_los = blocks_los
        self.glyph = glyph
        self.entities = []

    def is_movement_allowed(self):
        if self.blocks_move:
            return False
        for ent in self.entities:
            if ent.occupies_tile:
                return False
        return True


class Entity:
    def __init__(self, name, location=None, position=None, occupies_tile=False):
        self.name = name
        self.location = location
        self.position = position
        self.occupies_tile = occupies_tile

    def move(self, dx, dy):
        if self.position:
            new_x = self.position[0] + dx
            new_y = self.position[1] + dy
            if (new_x >= 0) and (new_y >= 0) and (new_x < self.location.width) and (new_y < self.location.height):
                if self.location.cells[new_x][new_y].is_movement_allowed():
                    self.location.cells[self.position[0]][self.position[1]].entities.remove(self)
                    self.location.cells[new_x][new_y].entities.append(self)
                    self.position = (new_x, new_y)
                    return True
        else:
            raise Exception('Attempted to move entity not positioned in any location. ', self.name)
        return False


class BattleEntity:
    def __init__(self, hp):
        self.hp = hp
        self.maxhp = hp


class Actor:
    def __init__(self, speed):
        self.speed = speed


class Fighter(BattleEntity, Actor, Entity):
    def __init__(self, name, hp, speed, ai=None):
        Entity.__init__(self, name=name, occupies_tile=True)
        BattleEntity.__init__(self, hp)
        Actor.__init__(self, speed)
        self.ai = ai


class Location:
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.cells = []
        self.entities = []

    def generate(self, pattern):
        if pattern == 'clear':
            self.cells.clear()
            self.cells = [[Cell('FLOOR', '.') for y in range(self.height)] for x in range(self.width)]

    def place_entity(self, entity, x, y):
        if (x >= 0) and (y >= 0) and (x < self.width) and (y < self.height):
            self.cells[x][y].entities.append(entity)
            entity.position = (x, y)
            entity.location = self
        else:
            raise Exception('Attempted to place entity outside of location.', entity.name)


def main_loop():
    while not tdl.event.isWindowClosed():  # TODO: убрать в input, менять там game_state когда он будет, убрать импорт
        events = player_input.handle_input()
        for event in events:
            if event == 'exit':
                return
            if event == 'move_up':
                player.move(0, -1)
            if event == 'move_down':
                player.move(0, 1)
            if event == 'move_right':
                player.move(1, 0)
            if event == 'move_left':
                player.move(-1, 0)
        render.render_all(current_loc, player)

current_loc = Location(50, 50)
current_loc.generate('clear')
player = Fighter('Player', 10, 100)
current_loc.place_entity(player, 10, 10)

main_loop()

import tdl


RENDERER = 'TDL'
FPS_LIMIT = 60

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 65

MAP_WIDTH = 80
MAP_HEIGHT = 50

if RENDERER == 'TDL':
    tdl.set_font('consolas_unicode_16x16.png', greyscale=True)
    console = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Desert City")
    map_console = tdl.Console(MAP_WIDTH, MAP_HEIGHT)
    tdl.set_fps(FPS_LIMIT)


# TODO: вынести данные (типа тайлсет) куда-то и брать оттуда
def cell_graphics(cell):
    char = ' '
    color = [255, 255, 255]
    bgcolor = [0, 0, 0]
    if cell.type == 'SAND':
        char = '.'
        color = [150, 150, 0]
        bgcolor = [60, 60, 20]
    for ent in cell.entities:
        if ent.occupies_tile:
            return ent.char, [255, 255, 255], bgcolor  # TODO: Хардкод!
    return char, color, bgcolor


def render_all(loc, player):
    if RENDERER == 'TDL':
        player_x = player.position[0]
        player_y = player.position[1]
        camera_x = MAP_WIDTH // 2
        camera_y = MAP_HEIGHT // 2
        for x in range(0, MAP_WIDTH):
            for y in range(0, MAP_HEIGHT):
                rel_x = x - camera_x + player_x
                rel_y = y - camera_y + player_y
                if (rel_x >= 0) and (rel_y >= 0) and (rel_x < loc.width) and (rel_y < loc.height):
                    cg = cell_graphics(loc.cells[rel_x][rel_y])
                    map_console.draw_char(x, y, cg[0], cg[1], cg[2])
                else:
                    map_console.draw_char(x, y, ' ')
        console.blit(map_console)
        tdl.flush()

"""
    This file contains graphics and user interface.
"""
import jsonpickle
from clubsandwich.director import DirectorLoop
from clubsandwich.ui import (
    WindowView,
    SettingsListView,
    LayoutOptions,
    UIScene,
    CyclingButtonView,
    SingleLineTextInputView,
    IntStepperView,
    RectView,
    View
)
from clubsandwich.geom import Size, Point
from bearlibterminal import terminal

from clubsandwich_fixed import ButtonViewFixed, LabelViewFixed

import game_logic
import save_load
import actions
import dataset
import generation

#  temporary shit
LOGO = """
            =================================================
====================== Welcome to Desert City! ==========================
            =================================================
                     \ =======================/
"""
character_bg_descriptions=[
                                             'Many adventurers are lured to the City - in search of treasures, power,' +
                                             ' glory or something else. You are among the others - jack of all trades,' +
                                             ' master of nothing.'
                                             ,
                                             'Mighty warriors visit Neth-Nikakh to prove their strength by fighting' +
                                             ' horrors, created by dark magic. Treasures are also nice bonus. You are ' +
                                             'such warrior, proficient in melee combat and wearing a set of armor.'
                                             ,
                                             'Mercenaries from distant Northern country called Gantra are well-known ' +
                                             'as trustworthy soldiers. One of them - with your sturdy crossbow' +
                                             ' and shooting skills - you headed south, to obtain treasures of mysterious'
                                             + ' City.'
                                             ,
                                             'A talent to use magic is rare among the people of Vaerthol. ' +
                                             'You lack one, but unlike others, you desperately crave ' +
                                             'for magic. One man told you a rumor, that in the sands lies a magic city' +
                                             ' of Neth-Nikakh, where among the other wonders, ordinary people can' +
                                             ' become powerful ' +
                                             'mages. So, you packed your spellbooks (useless for non-mage, of course)' +
                                             ', scrolls (not-so-useless), and headed South, to finally obtain desired' +
                                             ' magic gift.']
character_backgrounds = ['Adventurer', 'Warrior', 'Gantra mercenary', 'Magic seeker']
#  /temporary shit


class GameLoop(DirectorLoop):
    """ GameLoop class """
    def terminal_init(self):
        super().terminal_init()

    def get_initial_scene(self):
        return MainMenuScene()


class MainMenuScene(UIScene):
    """ Scene with main menu options """
    def __init__(self, *args, **kwargs):
        views = []
        self.game = save_load.load_game()  # try to load game
        views.append(LabelViewFixed(
                LOGO[1:].rstrip(),
                layout_options=LayoutOptions.row_top(0.5)))
        views.append(LabelViewFixed(
                "Choose one of the options below:",
                layout_options=LayoutOptions.centered('intrinsic', 'intrinsic')))
        if self.game:  # is game succesfully loaded - show Continue button
            views.append(ButtonViewFixed(
                text="Continue", callback=self.continue_game,
                layout_options=LayoutOptions.row_bottom(4).with_updates(
                    left=0.2, width=0.2, right=None)))
        else:  # if no savegame - show option greyed-out
            views.append(LabelViewFixed(
                text="[color=grey]Continue",
                layout_options=LayoutOptions.row_bottom(4).with_updates(
                    left=0.2, width=0.2, right=None)))
        views.append(ButtonViewFixed(
                text="New Game", callback=self.new_game,
                layout_options=LayoutOptions.row_bottom(4).with_updates(
                    left=0.4, width=0.2, right=None)))
        views.append(ButtonViewFixed(
                text="Quit",
                callback=lambda: self.director.pop_scene(),
                layout_options=LayoutOptions.row_bottom(4).with_updates(
                    left=0.6, width=0.2, right=None)))
        super().__init__(views, *args, **kwargs)

    def become_active(self):
        self.ctx.clear()

    def new_game(self):
        self.director.push_scene(CharacterSelectScene())

    def continue_game(self):
        self.director.push_scent(MainGameScene(self.game))


class CharacterSelectScene(UIScene):
    """ Scene displays character background variants with descriptions """
    def __init__(self, *args, **kwargs):
        self.options = character_backgrounds
        self.bg_texts = character_bg_descriptions
        self.selected = 0
        views = []
        views.append(RectView(style='double', layout_options=LayoutOptions(left=0, top=0)))
        top_offset = 0
        for option in self.options:
            top_offset += 1
            views.append(ButtonViewFixed(text=option,
                                         callback=self.option_activated,
                                         layout_options=LayoutOptions(
                                             left=2,
                                             top=top_offset,
                                             width='intrinsic',
                                             height=1,
                                             bottom=None,
                                             right=None)))
        self.description_view = LabelViewFixed(text=self.bg_texts[self.selected],
                                               align_horz='left',
                                               align_vert='top',
                                               layout_options=LayoutOptions(
                                                    left=0.5,
                                                    top=1,
                                                    width=0.45,
                                                    height='intrinsic',
                                                    bottom=None,
                                                    right=None
                                                ))
        views.append(self.description_view)
        super().__init__(views, *args, **kwargs)

    def become_active(self):
        self.ctx.clear()

    def terminal_read(self, val):
        super().terminal_read(val)
        # cycle descriptions with selected options
        if val in (terminal.TK_TAB, terminal.TK_KP_8, terminal.TK_KP_2, terminal.TK_UP, terminal.TK_DOWN):
            # allow traverse with arrows and numpad
            if val == terminal.TK_TAB:
                if self.selected < len(self.options) - 1:
                    self.selected += 1
                else:
                    self.selected = 0
            elif val in (terminal.TK_KP_8, terminal.TK_UP):
                self.view.find_prev_responder()
                if self.selected > 0:
                    self.selected -= 1
                else:
                    self.selected = len(self.options) - 1
            elif val in (terminal.TK_KP_2, terminal.TK_DOWN):
                self.view.find_next_responder()
                if self.selected < len(self.options) - 1:
                    self.selected += 1
                else:
                    self.selected = 0
            self.ctx.clear()
            self.description_view.text = self.bg_texts[self.selected]
            self.description_view.needs_layout = True

    def option_activated(self):
        """ Method to call when option is activated (ENTER key pressed) - New Game start """
        # TODO: make LOADING scene appear
        self.director.push_scene(LoadingScene())
        self.director.active_scene.terminal_update()
        game = game_logic.Game()  # start a new game
        sg_file = open('data/starting_gear.json', 'r')  # load starting gear
        sg_dict = jsonpickle.loads(sg_file.read())
        for item_id in sg_dict[self.options[self.selected]]:
            game.player.add_item(item_id)
        sg_file.close()
        self.director.push_scene(MainGameScene(game))


class LoadingScene(UIScene):
    """ Loading scene - currently a placeholder """
    def __init__(self, *args, **kwargs):
        views = [LabelViewFixed(
                LOGO[1:].rstrip(),
                layout_options=LayoutOptions.row_top(0.5))]
        super().__init__(views, *args, **kwargs)

    def become_active(self):
        self.ctx.clear()


class MainGameScene(UIScene):
    """ Main game scene """
    def __init__(self, game, *args, **kwargs):
        self.game = game
        views = [MapView(game=game,
                         layout_options=LayoutOptions(
                             left=1,
                             width=0.75,
                             top=1,
                             height=None,
                             bottom=1,
                             right=None
                            ))]
        super().__init__(views, *args, **kwargs)

    def become_active(self):
        self.ctx.clear()


class MapView(View):
    """ View with game map """
    def __init__(self, game, *args, **kwargs):
        self.game = game  # game object reference for obtaining map info
        self.cam_offset = (0, 0)
        super().__init__(*args, **kwargs)

    @property
    def intrinsic_size(self):
        return Size(self.bounds.width, self.bounds.height)

    @staticmethod
    def cell_graphics(x, y, cell, loc, visible):
        """ Method that returns graphic representation of tile. """
        char = ' '
        color = [255, 255, 255]
        bgcolor = [0, 0, 0]
        if visible:  # check if cell is visible
            tile = dataset.get_tile(cell.tile)
            char = tile[0]
            color = tile[1]
            bgcolor = tile[2]
            brk = False
            for ent in cell.entities:  # iterate through list of entities,if there are any, display them instead of tile
                char = ent.char
                color = ent.color
                if not color:
                    color = [255, 255, 255]
                if ent.occupies_tile:  # check if there is entity, occupying tile - display it on top
                    color = ent.color
                    brk = True
                if len(cell.entities) > 1:  # if there are multiple items, replace bgcolor
                    bgcolor = cell.entities[0].color
                    if color == bgcolor:
                        bgcolor = [c - 50 for c in bgcolor]
                        i = 0
                        for c in bgcolor:
                            if c < 0:
                                bgcolor[i] = 0
                            i += 1
                if brk:
                    break
            # update visited cells map (for displaying grey out of vision explored tiles)
            loc.out_of_sight_map[(x, y)] = [char, color, bgcolor]
            return [char, color, bgcolor]
        elif cell.explored:  # check if it was previously explored
            prev_seen_cg = loc.out_of_sight_map[(x, y)]  # take cell graphic from out_of_sight map of Location
            prev_seen_cg[1] = [100, 100, 100]  # make it greyish
            prev_seen_cg[2] = [50, 50, 50]
            return prev_seen_cg
        return [char, color, bgcolor]

    def draw(self, ctx):
        # player on-map coords
        player_x = self.game.player.position[0]
        player_y = self.game.player.position[1]
        # player on-screen coords
        player_scr_x = self.bounds.width // 4 - self.cam_offset[0]
        player_scr_y = self.bounds.height // 2 - self.cam_offset[1]
        for x in range(0, self.bounds.width // 2):  # iterate through every x, y in map_console
            for y in range(0, self.bounds.height):
                rel_x = x - player_scr_x + player_x  # game location coordinates in accordance to screen coordinates
                rel_y = y - player_scr_y + player_y
                # checks if location coordinates are valid (in boundaries)
                if self.game.current_loc.is_in_boundaries(rel_x, rel_y):
                    # obtain cell graphics
                    cg = self.cell_graphics(rel_x, rel_y, self.game.current_loc.cells[rel_x][rel_y],
                                            self.game.current_loc,
                                            self.game.player.is_in_fov(rel_x, rel_y))
                    ctx.color(terminal.color_from_argb(255, cg[1][0], cg[1][1], cg[1][2]))
                    ctx.bkcolor(terminal.color_from_argb(255, cg[2][0], cg[2][1], cg[2][2]))
                    ctx.print(Point(x * 2 + 1, y), ' ')
                    ctx.print(Point(x * 2, y), '[font=map]' + cg[0])
                else:
                    ctx.bkcolor(terminal.color_from_argb(255, 0, 0, 0))
                    ctx.print(Point(x * 2 + 1, y), ' ')
                    ctx.print(Point(x, y), '[font=map] ')   # if out of bounds then draw blank space
                if not self.cam_offset == (0, 0):
                    # if camera is not centered on player - draw there a red 'X'
                    ctx.color(terminal.color_from_argb(255, 255, 0, 0))
                    ctx.bkcolor(terminal.color_from_argb(255, 0, 0, 0))
                    ctx.print(Point(self.bounds.width + 1, self.bounds.height // 2), ' ')
                    ctx.print(Point(self.bounds.width, self.bounds.height // 2), '[font=map]X')


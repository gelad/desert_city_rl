"""
    This file contains graphics and user interface.
"""

from clubsandwich.director import DirectorLoop
from clubsandwich.ui import (
    WindowView,
    SettingsListView,
    LayoutOptions,
    UIScene,
    CyclingButtonView,
    SingleLineTextInputView,
    IntStepperView,
    RectView
)
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
        loaded = save_load.load_game()  # try to load game
        views.append(LabelViewFixed(
                LOGO[1:].rstrip(),
                layout_options=LayoutOptions.row_top(0.5)))
        views.append(LabelViewFixed(
                "Choose one of the options below:",
                layout_options=LayoutOptions.centered('intrinsic', 'intrinsic')))
        if loaded:  # is game succesfully loaded - show Continue button
            views.append(ButtonViewFixed(
                text="Continue", callback=self.continue_game(loaded),
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

    def continue_game(self, game):
        pass


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
                                         callback_selected=self.option_selected,
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
                                                    top=2,
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
        if val == terminal.TK_TAB:
            if self.selected < len(self.options) - 1:
                self.selected += 1
            else:
                self.selected = 0

    def option_selected(self):
        """ Method to call when option is selected (highlighted) """
        self.description_view.text = self.bg_texts[self.selected]
        self.description_view.needs_layout = True

    def option_activated(self):
        """ Method to call when option is activated (ENTER key pressed) """
        pass

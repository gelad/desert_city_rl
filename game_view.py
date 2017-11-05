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

import time
import sys
import threading
import os
import textwrap

import game_logic
import save_load
import actions
import dataset
import generation
import commands

#  temporary shit
LOGO = """
    ___                    _       ___ _ _         
   /   \___  ___  ___ _ __| |_    / __(_) |_ _   _ 
  / /\ / _ \/ __|/ _ \ '__| __|  / /  | | __| | | |
 / /_//  __/\__ \  __/ |  | |_  / /___| | |_| |_| |
/___,' \___||___/\___|_|   \__| \____/|_|\__|\__, |
                                             |___/ 
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
    def __init__(self):
        self.last_frame_time = time.time()
        self.game = None  # reference to Game object - to save it if closed
        super().__init__()

    def terminal_init(self):
        super().terminal_init()

    def quit(self):
        """ Added game saving on quit """
        if self.game:  # if game in progress - save it
            if self.game.player.state != 'dead':
                save_load.save_game(self.game)
            else:  # delete save if player dead
                try:
                    os.remove('savegame')
                except FileNotFoundError:
                    pass
        super().quit()

    def get_initial_scene(self):
        return MainMenuScene()

    def loop_until_terminal_exits(self):
        """ Loop changed, added sleep(), to prevent unnecessary high CPU load """
        try:
            has_run_one_loop = False
            current_time = time.time()
            while self.run_loop_iteration():
                sleep_time = 1. / self.fps - (current_time - self.last_frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.last_frame_time = current_time
                has_run_one_loop = True
            if not has_run_one_loop:
                print(
                    "Exited after only one loop iteration. Did you forget to" +
                    " return True from terminal_update()?",
                    file=sys.stderr)
        except KeyboardInterrupt:
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
            return True

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
        self.director.game = game

# List menu scenes


class ListSelectionScene(UIScene):
    """ Scene displays a list with selectable options """
    # TODO: refactor and comment this shit..
    def __init__(self, options, caption='', layout_options=None, alphabet=True, *args, **kwargs):
        self.options = options
        self.alphabet = alphabet
        self.selected = 0
        self.clear = True
        top_offset = 0
        subviews = []
        self.buttons = []
        letter_index = ord('a')  # start menu item indexing from 'a'
        max_option_length = 0  # longest option string - to determine window width
        for option in self.options:
            if alphabet:
                button_text = chr(letter_index) + ') ' + str(option)
            else:
                button_text = str(option)
            max_option_length = max(len(button_text), max_option_length)
            button = ButtonViewFixed(text=button_text,
                                     callback=self.option_activated,
                                     layout_options=LayoutOptions(
                                        left=1,
                                        top=top_offset,
                                        width='intrinsic',
                                        height=1,
                                        bottom=None,
                                        right=None))
            button.is_hidden = True
            subviews.append(button)
            self.buttons.append(button)
            top_offset += 1
            letter_index += 1
        if layout_options == 'intrinsic':  # if layout must derive from options
            layout_options = LayoutOptions.centered(height=len(options) + 2,
                                                    width=max(max_option_length + 2, len(caption)) + 2)
        self.window_view = WindowView(title=caption,
                                      style='double',
                                      layout_options=layout_options or LayoutOptions(left=0, top=0),
                                      subviews=subviews)
        views = [self.window_view]
        super().__init__(views, *args, **kwargs)
        self.scrolling_mode = False
        self.scroll_pos = self.selected

    def terminal_update(self, is_active=False):
        """ Cannot determine view bounds in __init__, doing scroll check here """
        super().terminal_update(is_active=is_active)
        self._scrolling_mode_check()
        if not self.scrolling_mode:
            for button in self.buttons:
                button.is_hidden = False

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
            if self.scrolling_mode:
                self._scroll()
            return True
        elif val in range(terminal.TK_A, len(self.options) + 4) and self.alphabet:  # select by key
            self.selected = val - 4  # because TK_A = 4
            self.option_activated()
        elif val == terminal.TK_ESCAPE:
            self.director.pop_scene()
            return True
        elif val == terminal.TK_RESIZED:
            self._scrolling_mode_check()
        return False

    def _scrolling_mode_check(self):
        """ Checks for height and enables/disables scrolling """
        list_height = self.window_view.bounds.height - 2
        if list_height < len(self.options):
            self.scrolling_mode = True
            self._scroll()
        else:
            self.scrolling_mode = False

    def _scroll(self):
        """ Method for scrolling the options list """
        list_height = self.window_view.bounds.height - 2
        if self.selected < self.scroll_pos:
            self.scroll_pos = self.selected
        elif self.selected > self.scroll_pos + list_height - 1:
            self.scroll_pos = self.selected - list_height + 1
        button_y = 0
        for i in range(len(self.options)):
            if self.scroll_pos <= i < (self.scroll_pos + list_height):
                self.buttons[i].is_hidden = False
                self.buttons[i].layout_options = self.buttons[i].layout_options.with_updates(top=button_y)
                button_y += 1
            else:
                self.buttons[i].is_hidden = True
            self.buttons[i].superview.set_needs_layout()
        self.window_view.needs_layout = True

    def option_activated(self):
        """ Method to call when option is activated (ENTER key pressed) """
        self.director.pop_scene()


class DescribedListSelectionScene(UIScene):
    """ Scene displays a list with selectable options and their descriptions to the left """
    # TODO: refactor and comment this shit..
    def __init__(self, options, descriptions, caption='', layout_options=None, alphabet=True, views=None,
                 *args, **kwargs):
        self.options = options
        self.descriptions = descriptions
        self.alphabet = alphabet
        self.selected = 0
        self.clear = True
        top_offset = 0
        subviews = []
        self.buttons = []
        letter_index = ord('a')  # start menu item indexing from 'a'
        for option in self.options:
            if alphabet:
                button_text = chr(letter_index) + ') ' + str(option)
            else:
                button_text = str(option)
            button = ButtonViewFixed(text=button_text,
                                     callback=self.option_activated,
                                     layout_options=LayoutOptions(
                                        left=1,
                                        top=top_offset,
                                        width='intrinsic',
                                        height=1,
                                        bottom=None,
                                        right=None))
            button.is_hidden = True
            subviews.append(button)
            self.buttons.append(button)
            top_offset += 1
            letter_index += 1
        self.description_view = LabelViewFixed(text=self.descriptions[self.selected],
                                               align_horz='left',
                                               align_vert='top',
                                               layout_options=LayoutOptions(
                                                    left=0.5,
                                                    top=0,
                                                    width=0.45,
                                                    height='intrinsic',
                                                    bottom=None,
                                                    right=None
                                                ))
        subviews.append(self.description_view)
        if views:
            subviews = subviews + views
        self.window_view = WindowView(title=caption,
                                      style='double',
                                      layout_options=layout_options or LayoutOptions(left=0, top=0),
                                      subviews=subviews)
        views = [self.window_view]
        super().__init__(views, *args, **kwargs)
        self.scrolling_mode = False
        self.scroll_pos = self.selected

    def terminal_update(self, is_active=False):
        """ Cannot determine view bounds in __init__, doing scroll check here """
        super().terminal_update(is_active=is_active)
        self._scrolling_mode_check()
        if not self.scrolling_mode:
            for button in self.buttons:
                button.is_hidden = False

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
            if self.scrolling_mode:
                self._scroll()
            self.description_view.text = self.descriptions[self.selected]
            self.description_view.needs_layout = True
            return True
        elif val in range(terminal.TK_A, len(self.options) + 4) and self.alphabet:  # select by key
            self.selected = val - 4  # because TK_A = 4
            self.option_activated()
        elif val == terminal.TK_ESCAPE:
            self.director.pop_scene()
            return True
        elif val == terminal.TK_RESIZED:
            self._scrolling_mode_check()
        return False

    def _scrolling_mode_check(self):
        """ Checks for height and enables/disables scrolling """
        list_height = self.window_view.bounds.height - 2
        if list_height < len(self.options):
            self.scrolling_mode = True
            self._scroll()
        else:
            self.scrolling_mode = False

    def _scroll(self):
        """ Method for scrolling the options list """
        list_height = self.window_view.bounds.height - 2
        if self.selected < self.scroll_pos:
            self.scroll_pos = self.selected
        elif self.selected > self.scroll_pos + list_height - 1:
            self.scroll_pos = self.selected - list_height + 1
        button_y = 0
        for i in range(len(self.options)):
            if self.scroll_pos <= i < (self.scroll_pos + list_height):
                self.buttons[i].is_hidden = False
                self.buttons[i].layout_options = self.buttons[i].layout_options.with_updates(top=button_y)
                button_y += 1
            else:
                self.buttons[i].is_hidden = True
            self.buttons[i].superview.set_needs_layout()
        self.window_view.needs_layout = True

    def option_activated(self):
        """ Method to call when option is activated (ENTER key pressed) """
        self.director.pop_scene()


class ItemManipulationSelectionScene(DescribedListSelectionScene):
    """ Item manipulation Scene subclass, not intended to use directly (to write less code in item manipulation menus)
     Does nothing to selected item. 
    """
    def __init__(self, items, game, *args, **kwargs):
        descriptions = []
        for item in items:
            text = ''
            text += item.description + '\n'
            text += 'Weight: ' + str(item.weight) + ' kg.\n'
            if item.properties:
                if 'bashing' in item.properties:
                    text += 'Deals ' + str(item.properties['bashing'][0]) + '-' + str(
                        item.properties['bashing'][1]) + ' bashing damage.\n'
                if 'slashing' in item.properties:
                    text += 'Deals ' + str(item.properties['slashing'][0]) + '-' + str(
                        item.properties['slashing'][1]) + ' slashing damage.\n'
                if 'piercing' in item.properties:
                    text += 'Deals ' + str(item.properties['piercing'][0]) + '-' + str(
                        item.properties['piercing'][1]) + ' piercing damage.\n'
                if 'fire' in item.properties:
                    text += 'Deals ' + str(item.properties['fire'][0]) + '-' + str(
                        item.properties['fire'][1]) + ' fire damage.\n'
                if 'cold' in item.properties:
                    text += 'Deals ' + str(item.properties['cold'][0]) + '-' + str(
                        item.properties['cold'][1]) + ' cold damage.\n'
                if 'lightning' in item.properties:
                    text += 'Deals ' + str(item.properties['lightning'][0]) + '-' + str(
                        item.properties['lightning'][1]) + ' lightning damage.\n'
            if len(item.effects) > 0:
                text += 'Effects: '
                for effect in item.effects:
                    text += effect.description + '\n'
            if len(item.abilities) > 0:
                text += 'Abilities: '
                for ability in item.abilities:
                    text += ability.name + '\n'
            descriptions.append(text)
        self.game = game
        self.weight_bar = LabelViewFixed(text='Weight: ' + str(round(self.game.player.carried_weight, 2)) + '/' +
                                         str(round(self.game.player.properties['max_carry_weight'], 2)) + ' kg.',
                                         layout_options=LayoutOptions().row_bottom(0).with_updates(width='intrinsic',
                                                                                                   left=None,
                                                                                                   right=0))
        if self.game.player.carried_weight > self.game.player.properties['max_carry_weight']:
            self.weight_bar.color_fg = terminal.color_from_name('red')
        super().__init__(options=items, descriptions=descriptions, views=[self.weight_bar], *args, **kwargs)

    def option_activated(self, game_update_needed=True):
        """ Method to drop item when option is activated (ENTER key pressed) """
        if game_update_needed:
            self.game.start_update_thread()
        super().option_activated()


class DropItemSelectionScene(ItemManipulationSelectionScene):
    """ Scene displays a list of items to drop one """
    def option_activated(self, *args, **kwargs):
        """ Method to drop item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_drop_item, self.game.player, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class UseItemSelectionScene(ItemManipulationSelectionScene):
    """ Scene displays a list of items to use one """
    def option_activated(self, *args, **kwargs):
        """ Method to use item when option is activated (ENTER key pressed) """
        commands.command_use_item(self.game, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class TakeOffItemSelectionScene(ItemManipulationSelectionScene):
    """ Scene displays a list of equipped items to take off one """
    def option_activated(self, *args, **kwargs):
        """ Method to take off item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_unequip_item, self.game.player, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class PickUpItemSelectionScene(ItemManipulationSelectionScene):
    """ Scene displays a list of items to pick up one """
    def option_activated(self, *args, **kwargs):
        """ Method to pick up item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_pick_up_item, self.game.player, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class WieldItemSelectionScene(ItemManipulationSelectionScene):
    """ Scene displays a list of items to wield one """
    def option_activated(self, *args, **kwargs):
        """ Method to wield item or display slot dialog when option is activated (ENTER key pressed) """
        slot = False
        if len(self.options[self.selected].equip_slots) > 1:
            director = self.director
            super().option_activated(*args, **kwargs)  # first pop this scene
            director.push_scene(WieldSlotSelectionScene(game=self.game,
                                                        item=self.options[self.selected],
                                                        caption='Select slot:',
                                                        layout_options='intrinsic'))
            return  # no need to pop Slot Selection scene
        elif len(self.options[self.selected].equip_slots) == 1:
            slot = list(self.options[self.selected].equip_slots)[0]
        if slot:  # if selected - equip item
            self.game.player.perform(actions.act_equip_item, self.game.player, self.options[self.selected], slot)
        super().option_activated(*args, **kwargs)


class WieldSlotSelectionScene(ListSelectionScene):
    """ Scene displays a list of suitable slots to wield item """
    def __init__(self, game, item, *args, **kwargs):
        self.game = game
        self.item = item
        options = list(item.equip_slots)
        super().__init__(options=options, *args, **kwargs)

    def option_activated(self):
        """ Method to wield item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_equip_item, self.game.player, self.item, self.options[self.selected])
        self.game.start_update_thread()
        super().option_activated()

# Other scenes


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

    def terminal_read(self, val):
        # allow menu selection with left/right arrows
        super().terminal_read(val)
        if val in (terminal.TK_KP_4, terminal.TK_LEFT):
            self.view.find_prev_responder()
            return True
        elif val in (terminal.TK_KP_6, terminal.TK_RIGHT):
            self.view.find_next_responder()
            return True
        self.ctx.clear()

    def become_active(self):
        self.ctx.clear()

    def new_game(self):
        self.director.push_scene(CharacterSelectScene())

    def continue_game(self):
        self.director.push_scene(MainGameScene(self.game))
        self.director.game = self.game


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
        self.health_bar = LabelViewFixed(text='', layout_options=LayoutOptions(left=0,
                                                                               top=0,
                                                                               height=1,
                                                                               bottom=None,
                                                                               right=1))
        self.health_bar.align_horz = 'left'
        self.player_right_hand = LabelViewFixed(text='', layout_options=LayoutOptions(left=0,
                                                                                      top=2,
                                                                                      height=1,
                                                                                      bottom=None,
                                                                                      right=1))
        self.player_right_hand.align_horz = 'left'
        self.player_left_hand = LabelViewFixed(text='', layout_options=LayoutOptions(left=0,
                                                                                     top=3,
                                                                                     height=1,
                                                                                     bottom=None,
                                                                                     right=1))
        self.player_left_hand.align_horz = 'left'
        self.money = LabelViewFixed(text='', layout_options=LayoutOptions(left=0,
                                                                          top=5,
                                                                          height=1,
                                                                          bottom=None,
                                                                          right=1))
        self.money.align_horz = 'left'
        self.map_view = MapView(game=game,
                                layout_options=LayoutOptions(
                                    left=1,
                                    width=0.60,
                                    top=1,
                                    height=None,
                                    bottom=1,
                                    right=None))
        self.bars_view = View(subviews=[self.health_bar, self.player_right_hand, self.player_left_hand, self.money],
                              layout_options=LayoutOptions(
                                left=0.62,
                                top=1,
                                right=1,
                                bottom=7))
        self.bars_view.clear = True
        self.log_view = LogView(game=game, layout_options=LayoutOptions(
                                    left=0.62,
                                    top=8,
                                    right=1,
                                    bottom=1))
        self.log_view.clear = True
        views = [self.map_view,
                 RectView(style='double', layout_options=LayoutOptions(left=0, top=0)),
                 RectView(style='double', layout_options=LayoutOptions().column_left(1).with_updates(
                     left=0.61,
                     right=None)),
                 self.bars_view,
                 self.log_view]
        super().__init__(views, *args, **kwargs)

    def become_active(self):
        self.ctx.clear()
        self.map_view.tick = 11  # to draw map right after

    def terminal_update(self, is_active=False):
        """ Update values in bars and tabs before drawing """
        player = self.game.player
        if is_active:
            self.health_bar.text = str(player.hp) + '/' + str(player.maxhp) + ' HP'
            # hp becomes red when hurt
            hp_percent = player.hp / player.maxhp
            if hp_percent < 0:
                hp_percent = 0
            if hp_percent > 1:
                hp_percent = 1
            self.health_bar.color_fg = terminal.color_from_argb(255,
                                                                int(255 * (1 - hp_percent)),
                                                                int(255 * hp_percent),
                                                                0)
            right = player.equipment['RIGHT_HAND']
            self.player_right_hand.text = 'Right: ' + str(right)
            left = player.equipment['LEFT_HAND']
            self.player_left_hand.text = 'Left:  ' + str(left)
            money = player.properties['money']
            self.money.text = 'Money: ' + str(money) + ' coins.'
        super().terminal_update(is_active=is_active)

    def terminal_read(self, val):
        """ This method handles player input in main scene """
        player_input = val
        game = self.game
        player = game.player
        handled = False  # input handled flag
        if game.is_waiting_input:
            if player_input == terminal.TK_ESCAPE:  # game quit on ESC - will be y/n prompt in the future
                self.director.quit()
            # movement commands
            elif player_input in (terminal.TK_KP_4, terminal.TK_LEFT):
                commands.command_default_direction(game=game, dx=-1, dy=0)
            elif player_input in (terminal.TK_KP_6, terminal.TK_RIGHT):
                commands.command_default_direction(game=game, dx=1, dy=0)
            elif player_input in (terminal.TK_KP_8, terminal.TK_UP):
                commands.command_default_direction(game=game, dx=0, dy=-1)
            elif player_input in (terminal.TK_KP_2, terminal.TK_DOWN):
                commands.command_default_direction(game=game, dx=0, dy=1)
            elif player_input == terminal.TK_KP_7:
                commands.command_default_direction(game=game, dx=-1, dy=-1)
            elif player_input == terminal.TK_KP_9:
                commands.command_default_direction(game=game, dx=1, dy=-1)
            elif player_input == terminal.TK_KP_1:
                commands.command_default_direction(game=game, dx=-1, dy=1)
            elif player_input == terminal.TK_KP_3:
                commands.command_default_direction(game=game, dx=1, dy=1)
            elif player_input == terminal.TK_KP_5:  # wait for ticks=player.speed (1 turn)
                player.perform(actions.act_wait, game.player, game.player.speed)
            elif player_input == 53:  # on '`' show debug messages in log
                if game.show_debug_log:
                    game.show_debug_log = False
                else:
                    game.show_debug_log = True
            elif player_input == terminal.TK_G:  # pick up item
                commands.command_pick_up(director=self.director, game=game, dx=0, dy=0)
            elif player_input == terminal.TK_D:  # drop item
                self.director.push_scene(DropItemSelectionScene(items=player.inventory,
                                                                game=game,
                                                                caption='Drop item:',
                                                                layout_options=LayoutOptions(
                                                                    top=0.1, bottom=0.1,
                                                                    left=0.2, right=0.2)))
            elif player_input == terminal.TK_U:  # use item
                self.director.push_scene(UseItemSelectionScene(items=player.inventory,
                                                               game=game,
                                                               caption='Use item:',
                                                               layout_options=LayoutOptions(
                                                                   top=0.1, bottom=0.1,
                                                                   left=0.2, right=0.2)))
            elif player_input == terminal.TK_W:  # wield item
                self.director.push_scene(WieldItemSelectionScene(items=player.inventory,
                                                                 game=game,
                                                                 caption='Wield item:',
                                                                 layout_options=LayoutOptions(
                                                                    top=0.1, bottom=0.1,
                                                                    left=0.2, right=0.2)))
            elif player_input == terminal.TK_O:  # take 'o'ff
                self.director.push_scene(TakeOffItemSelectionScene(items=[sl for sl in
                                                                          list(player.equipment.values()) if sl],
                                                                   game=game,
                                                                   caption='Take off item:',
                                                                   layout_options=LayoutOptions(
                                                                        top=0.1, bottom=0.1,
                                                                        left=0.2, right=0.2)))
            handled = True
            game.start_update_thread()
        super().terminal_read(val)
        return handled

# Views


class MapView(View):
    """ View with game map """
    def __init__(self, game, *args, **kwargs):
        self.game = game  # game object reference for obtaining map info
        self.cam_offset = (0, 0)  # camera offset (if looking or targeting)
        self.last_game_time = game.time_system.current_time()  # last game time (to know when redraw needed)
        self.tick = 0  # frame count (to know when redraw needed)
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
            if (x, y) in loc.out_of_sight_map:  # TODO: HACK, there must not be explored tiles not in out_of_sight
                prev_seen_cg = loc.out_of_sight_map[(x, y)]  # take cell graphic from out_of_sight map of Location
                prev_seen_cg[1] = [100, 100, 100]  # make it greyish
                prev_seen_cg[2] = [50, 50, 50]
                return prev_seen_cg
        return [char, color, bgcolor]

    def draw(self, ctx):
        # TODO: further refactoring needed (to speed up this)
        # X coordinate divided by 2 because map font is square - 1 map char = 2 text chars
        # player on-map coords
        self.tick += 1
        # redraw only if game time changed or every 10 frames
        if self.last_game_time != self.game.time_system.current_time() or self.tick > 10:
            player_x = self.game.player.position[0]
            player_y = self.game.player.position[1]
            # player on-screen coords
            player_scr_x = self.bounds.width // 4 - self.cam_offset[0]
            player_scr_y = self.bounds.height // 2 - self.cam_offset[1]
            for x in range(0, self.bounds.width // 2):  # iterate through every x, y
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
                        terminal.printf(self.layout_options.left + x * 2 + 1, self.layout_options.top + y, ' ')
                        terminal.printf(self.layout_options.left + x * 2, self.layout_options.top + y, '[font=map]' + cg[0])
                        # ctx.print(Point(x * 2 + 1, y), ' ')  # draw blank space with bkcolor (big chars bug?)
                        # ctx.print(Point(x * 2, y), '[font=map]' + cg[0])
                    else:
                        ctx.bkcolor(terminal.color_from_argb(255, 0, 0, 0))
                        terminal.printf(self.layout_options.left + x * 2 + 1, self.layout_options.top + y, ' ')
                        terminal.printf(self.layout_options.left + x * 2, self.layout_options.top + y, '[font=map] ')
                        # ctx.print(Point(x * 2 + 1, y), ' ')  # draw blank space with bkcolor (big chars bug?)
                        # ctx.print(Point(x, y), '[font=map] ')   # if out of bounds then draw blank space
                    if not self.cam_offset == (0, 0):
                        # if camera is not centered on player - draw there a red 'X'
                        ctx.color(terminal.color_from_argb(255, 255, 0, 0))
                        ctx.bkcolor(terminal.color_from_argb(255, 0, 0, 0))
                        # draw blank space with bkcolor (big chars bug?)
                        terminal.printf(self.layout_options.left + self.bounds.width // 2 + 1,
                                        self.layout_options.top + self.bounds.height // 2, ' ')
                        terminal.printf(self.layout_options.left + self.bounds.width // 2,
                                        self.layout_options.top + self.bounds.height // 2, '[font=map]X')
                        # ctx.print(Point(self.bounds.width // 2 + 1, self.bounds.height // 2), ' ')
                        # ctx.print(Point(self.bounds.width // 2, self.bounds.height // 2), '[font=map]X')
            self.last_game_time = self.game.time_system.current_time()
            self.tick = 0


class LogView(View):
    """ View with game log """
    def __init__(self, game, *args, **kwargs):
        self.game = game  # game object reference for obtaining map info
        self.clear = True  # clear before each draw
        super().__init__(*args, **kwargs)

    @property
    def intrinsic_size(self):
        return Size(self.bounds.width, self.bounds.height)

    def draw(self, ctx):
        # TODO: draw log only if it changes
        # get log messages, intended to be shown to player
        if self.game.show_debug_log:
            msgs = [m for m in game_logic.Game.log if m[1] == 'DEBUG']
        else:
            msgs = [m for m in game_logic.Game.log if m[1] == 'PLAYER']
        msgs = msgs[-self.bounds.height:]  # make a slice for last ones log_height ammount
        log_lines = []
        for msg in msgs:  # iterate through messages
            for line in textwrap.wrap(msg[0], self.bounds.width):  # wrap them in lines of log_width
                log_lines.append((line, msg[2]))  # store them in list
        log_lines = log_lines[-(self.bounds.height - 1):]  # slice list to log_height elements
        y = 0
        for line in log_lines:
            y += 1
            ctx.color(terminal.color_from_argb(255, line[1][0], line[1][1], line[1][2]))
            ctx.print(Point(0, y), line[0])  # draw each line

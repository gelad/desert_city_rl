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
import itertools
from math import hypot, floor

import game_logic
import save_load
import actions
import dataset
import generation
import commands

from messages import _  # translation function
from messages import missing_translations

#  temporary shit
LOGO = """
    ___                    _       ___ _ _         
   /   \___  ___  ___ _ __| |_    / __(_) |_ _   _ 
  / /\ / _ \/ __|/ _ \ '__| __|  / /  | | __| | | |
 / /_//  __/\__ \  __/ |  | |_  / /___| | |_| |_| |
/___,' \___||___/\___|_|   \__| \____/|_|\__|\__, |
                                             |___/ 
"""

LOADING = """
 _      ____          _____ _____ _   _  _____ 
| |    / __ \   /\   |  __ \_   _| \ | |/ ____|
| |   | |  | | /  \  | |  | || | |  \| | |  __ 
| |   | |  | |/ /\ \ | |  | || | | . ` | | |_ |
| |___| |__| / ____ \| |__| || |_| |\  | |__| |
|______\____/_/    \_\_____/_____|_| \_|\_____|                                     
"""

HELP_TEXT = _("""Movement: Arrow keys and Keypad 1-9 
Keypad 5 - 'wait 1 turn' command
F1 - display this help message
i - show player inventory
l - look around
g - pick up item from Ground
u - use item
w - wield (equip) item
t - throw item from hand
f - fire ranged weapon
r - reload 
d - drop item
o - take Off equipped item
n - uNload ranged weapon
c - close door
s - smash (melee attack inanimate object, i.e. wall)
Esc - Save and exit""")

CHARACTER_BG_DESCRIPTIONS = [_(
    'Many adventurers are lured to the City - in search of treasures, power, glory or something else. You are among the others - jack of all trades, master of nothing.'),
                             _(
                                 'Mighty warriors visit Neth-Nikakh to prove their strength by fighting horrors, created by dark magic. Treasures are also nice bonus. You are such warrior, proficient in melee combat and wearing a set of armor.')
    , _(
        'Mercenaries from distant Northern country called Gantra are well-known as trustworthy soldiers. One of them - with your sturdy crossbow and shooting skills - you headed south, to obtain treasures of mysterious City.'),
                             _(
                                 'A talent to use magic is rare among the people of Vaerthol. You lack one, but unlike others, you desperately crave for magic. One man told you a rumor, that in the sands lies a magic city of Neth-Nikakh, where among the other wonders, ordinary people can become powerful mages. So, you packed your spellbooks (useless for non-mage, of course), scrolls (not-so-useless), and headed South, to finally obtain desired magic gift.')]

CHARACTER_BACKGROUNDS = ['Adventurer', 'Warrior', 'Gantra mercenary', 'Magic seeker']  # they are used as keys
CHARACTER_BACKGROUNDS_TRAN = [_('Adventurer'), _('Warrior'), _('Gantra mercenary'), _('Magic seeker')]  # translations
del CHARACTER_BACKGROUNDS_TRAN  # not used (it's a shitty hack to add them to pot file every time)

CAMP_MENU_DESCRIPTIONS = [_("""\n\tGo to the Desert City. It's about it, after all.\n """),
                          _(
                              """\n\tHorrors of Desert City are exhausting. Opportunity to sleep and eat without being chased by a bunch of hungry Rakshasas is really nice.\n """),
                          _(
                              """\n\tTraders, smugglers and other suspicious persons are always eager to buy treasures from Neth-Nikakh. Treasure Market is most populated, loud and somewhat dangerous place in the camp.\n """),
                          _(
                              """\n\tEquipment merchant Sidorovich from northern country called Gantra is selling various equipment, needed by fellow treasure-hunters. Just don't bring him empty cans, you know.\n """),
                          _(
                              """\n\tTavern 'Galloping Scorpion' is the heart of social life in the camp. Missions, valuable info, rumors and gossips, thousands of them! And plenty of drinkin' also.\n """)]

FIRST_CAMP_ARRIVAL_MESSAGE = _("""\n\tFinally, your long journey came to an end. The last part, traveling with the caravan through the Great Desert, was hard and full of dangers. Now you stand by the entrance of the treasure hunters camp.
\tIt's more like a small town, except lots of armed people wandering around, and enormous marketplace at the center. Adventurers of all sorts stay here between raids to the City.
\tYou can stop here to look around for a while, or head immediately to the Desert City. It can be seen from here, below the towering Lone Mountain, looking more like a mirage.\n """)

BODYPARTS = [_('RIGHT_HAND'), _('LEFT_HAND'), _('RIGHT_RING'), _('LEFT_RING'), _('ARMS'), _('SHOULDERS'),
             _('BODY'), _('HEAD'), _('FACE'), _('LEFT_EAR'), _('RIGHT_EAR'), _('NECK'), _('WAIST'), _('LEGS'),
             _('FEET')]


#  /temporary shit


class GameLoop(DirectorLoop):
    """ GameLoop class """

    active_director = None

    def __init__(self):
        self.last_frame_time = time.time()
        self.game = None  # reference to Game object - to save it if closed
        self.main_game_scene = None  # reference to Main Game Scene
        GameLoop.active_director = self  # assign self to global director
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
        GameLoop.active_director = None
        if len(missing_translations) > 0:
            print('Some strings missing in translation files. Written to missing_translations.txt.')
            f = open(file='missing_translations.txt', mode='w')
            for s in missing_translations:
                f.write(s + '\n\n')
            f.close()
        super().quit()

    def get_initial_scene(self):
        return MainMenuScene()

    def loop_until_terminal_exits(self):
        """ Loop changed, added sleep(), to prevent unnecessary high CPU load,
            added player death check 
        """
        try:
            has_run_one_loop = False
            current_time = time.time()
            while self.run_loop_iteration():
                sleep_time = 1. / self.fps - (current_time - self.last_frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.last_frame_time = current_time
                has_run_one_loop = True
                if self.game:  # delete save if player dead and run death command
                    if self.game.player.state == 'dead':
                        try:
                            os.remove('savegame')
                        except FileNotFoundError:
                            pass
                        commands.command_player_dead(game=self.game)
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
        self.options = CHARACTER_BACKGROUNDS
        self.bg_texts = CHARACTER_BG_DESCRIPTIONS
        self.selected = 0
        views = []
        views.append(RectView(style='double', layout_options=LayoutOptions(left=0, top=0)))
        top_offset = 0
        for option in self.options:
            top_offset += 1
            views.append(ButtonViewFixed(text=_(option),
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
            elif val == terminal.TK_ESCAPE:  # on escape return to main menu
                self.director.pop_scene()
            self.ctx.clear()
            self.description_view.text = self.bg_texts[self.selected]
            self.description_view.needs_layout = True
            return True
        elif val == terminal.TK_ESCAPE:  # on escape return to main menu
            self.director.pop_scene()
            return True

    def option_activated(self):
        """ Method to call when option is activated (ENTER key pressed) - New Game start """
        self._start_new_game()

    def _start_new_game(self):
        """ This method starts a new game and loads starting gear """
        game = game_logic.Game()  # start a new game
        sg_file = open('data/starting_gear.json', 'r')  # load starting gear
        sg_dict = jsonpickle.loads(sg_file.read())
        for item_id in sg_dict[self.options[self.selected]]:
            game.player.add_item(item_id)
        sg_file.close()
        self.director.push_scene(MainGameScene(game))
        self.director.push_scene(CampMenuScene(game))
        self.director.push_scene(SingleButtonMessageScene(message=FIRST_CAMP_ARRIVAL_MESSAGE,
                                                          title=_('Arrival to treasure hunters camp'),
                                                          callback=lambda: (self.director.pop_scene(),
                                                                            terminal.clear())))
        self.director.game = game


# Dialogue and message scenes


class SingleButtonMessageScene(UIScene):
    """ A simple message with single button that closes it """

    def __init__(self, message, title='', button_text='OK.', close_on_esc=True,
                 callback=None, layout_options='intrinsic', *args, **kwargs):
        self.message = message
        self.title = title
        self.close_on_esc = close_on_esc
        if not callback:
            callback = self._default_button_action
        if layout_options == 'intrinsic':
            size = self._calculate_size()
            layout_options = LayoutOptions(width=size.width,
                                           height=size.height,
                                           top=None, bottom=None,
                                           left=None, right=None)
        self.window_view = WindowView(title=title, layout_options=layout_options, subviews=
        [LabelViewFixed(text=message, align_vert='left', align_horz='top',
                        layout_options=LayoutOptions(top=0,
                                                     left=0)),
         ButtonViewFixed(text=button_text, callback=callback,
                         layout_options=LayoutOptions(bottom=0,
                                                      left=0,
                                                      width='intrinsic',
                                                      height='intrinsic',
                                                      right=None,
                                                      top=None))])
        views = [self.window_view]
        super().__init__(views, *args, **kwargs)

    def terminal_read(self, val):
        """ Handles input """
        super().terminal_read(val)
        if val == terminal.TK_ESCAPE and self.close_on_esc:
            self.director.pop_scene()
            return True
        elif val == terminal.TK_RESIZED:
            new_size = self._calculate_size()
            self.window_view.layout_options = LayoutOptions(width=new_size.width, height=new_size.height,
                                                            top=None, bottom=None,
                                                            left=None, right=None)
            self.window_view.set_needs_layout(True)
        return False

    def _calculate_size(self):
        """ Method for autosize """
        t_width = terminal.state(terminal.TK_WIDTH)
        t_height = terminal.state(terminal.TK_HEIGHT)
        aspect_ratio = (t_width / t_height)
        # try increasing height and width while checking message text to fit
        for height in range(4, t_height):
            # make width grow in accord with aspect ratio to get more wide window
            width = max((len(self.title), round(aspect_ratio * height)))
            wrapped_text = []
            # simple wrap() won't do, because text with \n will get fucked up
            for line in self.message.splitlines():
                if line:
                    if len(line) <= width:
                        wrapped_text.append(line)
                    else:
                        wrapped_text.extend(textwrap.wrap(line, width))
            if len(wrapped_text) + 3 <= height:
                # returning width of most long text line - previous algorithm produces some excess width
                return Size(width=len(max(wrapped_text, key=len)) + 2, height=len(wrapped_text) + 4)
        return Size(width=t_width - 2, height=t_height - 2)

    def _default_button_action(self):
        """ Default action when button is pressed - pop this scene """
        self.director.pop_scene()


class MultiButtonMessageScene(UIScene):
    """ A message with multiple buttons """

    def __init__(self, buttons, title='', close_on_esc=True, layout_options='intrinsic', *args, **kwargs):
        """
        :param buttons: a list of tuples (caption, text, callback)
        :param title: string with window caption
        :param close_on_esc: bool, shall window close on ESC button hit?
        :param layout_options: LayoutOptions() object or 'intrinsic' string for auto size
        :param args: other possible UIScene args
        :param kwargs: other possible UIScene args
        """

        self.buttons = buttons
        self.title = title
        self.close_on_esc = close_on_esc
        subviews = []
        button_offset = 0
        max_text_l = 0
        max_caption_l = 0
        self.longest_text = ''
        self.longest_caption = ''
        self.text_view = LabelViewFixed(text='', align_vert='left', align_horz='top',
                                        layout_options=LayoutOptions(top=0, left=0))
        for button in buttons:
            caption, text, callback = button
            button_offset += 1
            if len(text) > max_text_l:
                max_text_l = len(text)
                self.longest_text = text
            if len(caption) > max_caption_l:
                max_caption_l = len(text)
                self.longest_caption = caption
            if not callback:
                callback = self._default_button_action
            b = ButtonViewFixed(text=caption, callback=callback,
                                callback_selected=lambda txt=text: self.text_view.set_text(txt),
                                layout_options=LayoutOptions(bottom=len(buttons) - button_offset,
                                                             left=0,
                                                             width='intrinsic',
                                                             height='intrinsic',
                                                             right=None,
                                                             top=None))
            subviews.append(b)
        subviews = [self.text_view] + subviews
        if layout_options == 'intrinsic':
            size = self._calculate_size()
            layout_options = LayoutOptions(width=size.width,
                                           height=size.height,
                                           top=None, bottom=None,
                                           left=None, right=None)
        self.window_view = WindowView(title=title, layout_options=layout_options, subviews=subviews)
        views = [self.window_view]
        super().__init__(views, *args, **kwargs)

    def terminal_read(self, val):
        """ Handles input """
        super().terminal_read(val)
        if val == terminal.TK_ESCAPE and self.close_on_esc:
            self.director.pop_scene()
            return True
        elif val in (terminal.TK_KP_8, terminal.TK_UP):
            self.view.find_prev_responder()
        elif val in (terminal.TK_KP_2, terminal.TK_DOWN):
            self.view.find_next_responder()
        elif val == terminal.TK_RESIZED:
            new_size = self._calculate_size()
            self.window_view.layout_options = LayoutOptions(width=new_size.width, height=new_size.height,
                                                            top=None, bottom=None,
                                                            left=None, right=None)
            self.window_view.set_needs_layout(True)
        return False

    def _calculate_size(self):
        """ Method for autosize """
        t_width = terminal.state(terminal.TK_WIDTH)
        t_height = terminal.state(terminal.TK_HEIGHT)
        aspect_ratio = (t_width / t_height)
        # try increasing height and width while checking message text to fit
        for height in range(len(self.buttons) + 3, t_height):
            # make width grow in accord with aspect ratio to get more wide window
            width = max((len(self.title), len(self.longest_caption), round(aspect_ratio * height)))
            wrapped_text = []
            # simple wrap() won't do, because text with \n will get fucked up
            for line in self.longest_text.splitlines():
                if line:
                    if len(line) <= width:
                        wrapped_text.append(line)
                    else:
                        wrapped_text.extend(textwrap.wrap(line, width))
            if len(wrapped_text) + len(self.buttons) + 2 <= height:
                # returning width of most long text line - previous algorithm produces some excess width
                return Size(width=len(max(wrapped_text, key=len)) + 2, height=len(wrapped_text) + len(self.buttons) + 3)
        return Size(width=t_width - 2, height=t_height - 2)  # if cannot auto size properly - full window

    def _default_button_action(self):
        """ Default action when button is pressed - pop this scene """
        self.director.pop_scene()


class CampMenuScene(MultiButtonMessageScene):
    """ A Scene with camp menu """

    def __init__(self, game, *args, **kwargs):
        self.game = game
        buttons = [(_('Delve into Desert City'), CAMP_MENU_DESCRIPTIONS[0], self._to_city_start_thread),
                   (_('Get some rest.'), CAMP_MENU_DESCRIPTIONS[1], self._take_rest),
                   (_('Sell treasures.'), CAMP_MENU_DESCRIPTIONS[2], self._to_market),
                   (_('Go to equipment merchant.'), CAMP_MENU_DESCRIPTIONS[3], self._to_equipment_merchant),
                   (_('Visit the tavern (closed for now).'), CAMP_MENU_DESCRIPTIONS[4], self._to_tavern)]
        super().__init__(buttons=buttons, title=_('Treasure hunters camp near Neth-Nikakh'), *args, **kwargs)

    def terminal_read(self, val):
        """ Handles input (intercept ESC button - exit game) """
        if val == terminal.TK_ESCAPE and self.close_on_esc:
            text = _('Do you really want to quit?')
            self.director.push_scene(MultiButtonMessageScene(buttons=[(_('Yes'), text, lambda: self.director.quit()),
                                                                      (_('No'), text, None)],
                                                             title=_('Confirm exit'),
                                                             layout_options='intrinsic'))
            return True
        return super().terminal_read(val)

    def become_active(self):
        """ Clears screen when active """
        self.ctx.clear()

    def _to_city_start_thread(self):
        """ 
        Method that starts thread with location generation and transition 
        Threading is needed to show Loading screen while generating a location    
        """
        t = threading.Thread(target=self._to_desert_city)
        t.start()
        self.director.push_scene(LoadingScene(watch_thread=t))

    def _to_desert_city(self):
        """ Method that starts raid to the Desert City. Now simply moves player to new 'ruins' location. """
        commands.command_enter_loc(game=self.game, new_loc=generation.generate_loc('ruins', None, 200, 200))
        self.game.leave_camp()
        director = self.director
        while director.active_scene is not director.main_game_scene:  # pop to main game scene
            director.pop_scene()
        message_scene = SingleButtonMessageScene(message=_(
            """Outskirts of the Desert City. These particular ruins appear to be unexplored by other adventurers."""),
                                                 title=_('Entering ruins.'),
                                                 layout_options='intrinsic')
        message_scene.clear = True
        director.push_scene(message_scene)

    def _take_rest(self):
        """ Method that replenshes player health for now """
        if self.game.player.hp < self.game.player.maxhp:
            self.game.player.heal(heal=self.game.player.maxhp, healer=self.game.player)
        self.director.push_scene(SingleButtonMessageScene(
            message=_("""Ahhh. Sleeping in the bed, eating fresh hot food. Feels wonderful!"""),
            title=_('Rested.'),
            layout_options='intrinsic'))

    def _to_market(self):
        """ Method that sells treasure items to market and shows a report """
        # treasures report section
        report_text = ''
        treasures = {}
        sold = []
        player = self.game.player
        for item in player.inventory:
            if 'relic' in item.categories:  # if there'll be other types of treasure - add here
                if isinstance(item, game_logic.ItemCharges):
                    count = item.charges
                else:
                    count = 1
                if item.name in treasures:
                    treasures[str(item)][0] += count
                else:
                    treasures[str(item)] = [count, item.properties['value']]
                sold.append(item)
        for item in sold:
            player.discard_item(item=item)  # remove sold items from inventory
        if len(treasures) > 0:
            report_text += _('You sold some treasures:\n\n')
            total = 0
            for tr in treasures.keys():
                report_text += _('{tr_name} x{tr_count} * {tr_value} = {tr_total}\n').format(tr_name=tr,
                                                                                             tr_count=str(
                                                                                                 treasures[tr][0]),
                                                                                             tr_value=str(
                                                                                                 treasures[tr][1]),
                                                                                             tr_total=str(
                                                                                                 treasures[tr][0] *
                                                                                                 treasures[tr][1]))
                total += treasures[tr][0] * treasures[tr][1]
            report_text += _('\nTotal treasures value: {total} coins.\n ').format(total=str(total))
            player.properties['money'] += total  # give player the money
        else:
            report_text += _(
                """All you have to do in the marketplace today is wandering around. You don't have anything to sell right now.\n """)
        self.director.push_scene(SingleButtonMessageScene(message=report_text, title=_('Marketplace.')))

    def _to_equipment_merchant(self):
        self.director.push_scene(MerchantScene(game=self.game, merchant=self.game.equipment_merchant))

    def _to_tavern(self):
        pass


# List menu scenes


class ListSelectionScene(UIScene):
    """ Scene displays a list with selectable options """

    def __init__(self, options, caption='', layout_options=None, alphabet=True, *args, **kwargs):
        self.options = options
        self.alphabet = alphabet  # flag that allows option selection by A..Z keys
        self.selected = 0  # currently selected option index
        self.clear = True
        # button creation
        top_offset = 0
        subviews = []
        self.buttons = []
        letter_index = ord('a')  # start menu item indexing from 'a'
        max_option_length = 0  # longest option string - to determine window width
        for option in self.options:
            if alphabet:
                button_text = chr(letter_index) + ') ' + _(str(option))
            else:
                button_text = _(str(option))
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
        # initiate scrolling
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

    def __init__(self, options, descriptions, caption='', layout_options=None, alphabet=True, views=None,
                 *args, **kwargs):
        self.options = options
        self.descriptions = descriptions
        self.alphabet = alphabet  # flag that allows option selection by A..Z keys
        self.selected = 0  # currently selected option index
        self.clear = True
        # buttons creation
        top_offset = 0
        subviews = []
        self.buttons = []
        letter_index = ord('a')  # start menu item indexing from 'a'
        for option in self.options:
            if isinstance(option, game_logic.Entity):
                b_text = str(option)  # entity name already translated
            else:
                b_text = _(str(option))
            if alphabet:
                button_text = chr(letter_index) + ') ' + b_text
            else:
                button_text = b_text
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
        # scrolling initialization
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


class ItemManipulationSelectionScene(UIScene):
    """ Item manipulation selection - when item is selected it Inventory menu """

    def __init__(self, game, item, layout_options=None, *args, **kwargs):
        # self.clear = True
        self.game = game
        self.item = item  # item for manipulation
        subviews = []
        top_offset = 0
        max_option_length = 0
        if 'usable' in item.properties:  # USE button
            button = ButtonViewFixed(text=_('u) Use'),
                                     callback=self._use,
                                     layout_options=LayoutOptions(
                                         left=1,
                                         top=top_offset,
                                         width='intrinsic',
                                         height=1,
                                         bottom=None,
                                         right=None))
            max_option_length = max(len(button.text), max_option_length)
            subviews.append(button)
            top_offset += 1
        button = ButtonViewFixed(text=_('d) Drop'),  # DROP button
                                 callback=self._drop,
                                 layout_options=LayoutOptions(
                                     left=1,
                                     top=top_offset,
                                     width='intrinsic',
                                     height=1,
                                     bottom=None,
                                     right=None))
        max_option_length = max(len(button.text), max_option_length)
        subviews.append(button)
        top_offset += 1
        button = ButtonViewFixed(text=_('w) Wield'),  # WIELD button
                                 callback=self._wield,
                                 layout_options=LayoutOptions(
                                     left=1,
                                     top=top_offset,
                                     width='intrinsic',
                                     height=1,
                                     bottom=None,
                                     right=None))
        max_option_length = max(len(button.text), max_option_length)
        subviews.append(button)
        top_offset += 1
        if isinstance(item, game_logic.ItemRangedWeapon):  # check if there is ranged weapon
            if len(item.ammo) < item.ammo_max:  # check if it is loaded
                button = ButtonViewFixed(text=_('r) Reload'),  # RELOAD button
                                         callback=self._reload,
                                         layout_options=LayoutOptions(
                                             left=1,
                                             top=top_offset,
                                             width='intrinsic',
                                             height=1,
                                             bottom=None,
                                             right=None))
                max_option_length = max(len(button.text), max_option_length)
                subviews.append(button)
                top_offset += 1
            if len(item.ammo) > 0:
                button = ButtonViewFixed(text=_('n) uNload'),  # UNLOAD button
                                         callback=self._unload,
                                         layout_options=LayoutOptions(
                                             left=1,
                                             top=top_offset,
                                             width='intrinsic',
                                             height=1,
                                             bottom=None,
                                             right=None))
                max_option_length = max(len(button.text), max_option_length)
                subviews.append(button)
                top_offset += 1
        if layout_options == 'intrinsic':  # if layout must derive from options
            layout_options = LayoutOptions.centered(height=top_offset + 2,
                                                    width=max(max_option_length + 2, len(str(item))) + 2)
        self.window_view = WindowView(title=str(item),
                                      style='double',
                                      layout_options=layout_options or LayoutOptions(left=0, top=0),
                                      subviews=subviews)
        views = [self.window_view]
        super().__init__(views, *args, **kwargs)

    def terminal_read(self, val):
        super().terminal_read(val)
        # cycle descriptions with selected options
        if val in (terminal.TK_KP_8, terminal.TK_KP_2, terminal.TK_UP, terminal.TK_DOWN):
            # allow traverse with arrows and numpad
            if val in (terminal.TK_KP_8, terminal.TK_UP):
                self.view.find_prev_responder()
            elif val in (terminal.TK_KP_2, terminal.TK_DOWN):
                self.view.find_next_responder()
            return True
        elif val == terminal.TK_U:  # USE
            self._use()
        elif val == terminal.TK_D:  # DROP
            self._drop()
        elif val == terminal.TK_W:  # WIELD
            self._wield()
        elif val == terminal.TK_R:  # RELOAD
            self._reload()
        elif val == terminal.TK_N:  # uNload
            self._unload()
        elif val == terminal.TK_ESCAPE:
            self.director.pop_scene()
            return True
        return False

    def option_activated(self):
        """ Method to call when option is activated (ENTER key pressed) """
        self.director.pop_scene()

    def _use(self):
        director = self.director
        self.option_activated()
        commands.command_use_item(game=self.game, item=self.item, main_scene=director.main_game_scene)

    def _drop(self):
        self.option_activated()
        self.game.player.perform(actions.act_drop_item, self.game.player, self.item)
        self.game.start_update_thread()

    def _reload(self):
        director = self.director
        self.option_activated()
        commands.command_reload(game=self.game, item=self.item)

    def _unload(self):
        pass

    def _wield(self):
        director = self.director
        self.option_activated()
        slot = None
        if len(self.item.equip_slots) > 1:
            director.push_scene(WieldSlotSelectionScene(game=self.game,
                                                        item=self.item,
                                                        caption=_('Select slot:'),
                                                        layout_options='intrinsic'))
            return  # no need to pop Slot Selection scene
        elif len(self.item.equip_slots) == 1:
            slot = list(self.item.equip_slots)[0]
        if slot:  # if selected - equip item
            self.game.player.perform(actions.act_equip_item, self.game.player, self.item, slot)
            self.option_activated()


class ItemSelectionScene(DescribedListSelectionScene):
    """ Item selection Scene subclass, not intended to use directly (to write less code in item manipulation menus)
     Does nothing to selected item. 
    """

    def __init__(self, items, game, *args, **kwargs):
        descriptions = []
        for item in items:
            text = ''
            text += item.description + '\n'
            text += _('Weight: ') + str(item.weight) + _(' kg.\n')
            if item.properties:
                if 'bashing' in item.properties:
                    text += _('Deals {min_damage}-{max_damage} bashing damage.\n').format(
                        min_damage=str(item.properties['bashing'][0]),
                        max_damage=str(item.properties['bashing'][1]))
                if 'slashing' in item.properties:
                    text += _('Deals {min_damage}-{max_damage} slashing damage.\n').format(
                        min_damage=str(item.properties['slashing'][0]),
                        max_damage=str(item.properties['slashing'][1]))
                if 'piercing' in item.properties:
                    text += _('Deals {min_damage}-{max_damage} piercing damage.\n').format(
                        min_damage=str(item.properties['piercing'][0]),
                        max_damage=str(item.properties['piercing'][1]))
                if 'fire' in item.properties:
                    text += _('Deals {min_damage}-{max_damage} fire damage.\n').format(
                        min_damage=str(item.properties['fire'][0]),
                        max_damage=str(item.properties['fire'][1]))
                if 'cold' in item.properties:
                    text += _('Deals {min_damage}-{max_damage} cold damage.\n').format(
                        min_damage=str(item.properties['cold'][0]),
                        max_damage=str(item.properties['cold'][1]))
                if 'lightning' in item.properties:
                    text += _('Deals {min_damage}-{max_damage} lightning damage.\n').format(
                        min_damage=str(item.properties['lightning'][0]),
                        max_damage=str(item.properties['lightning'][1]))
            if len(item.effects) > 0:
                text += _('Effects: ')
                for effect in item.effects:
                    text += effect.description + '\n'
            if len(item.abilities) > 0:
                text += _('Abilities: ')
                for ability in item.abilities:
                    text += _(ability.name) + '\n'
            descriptions.append(text)
        self.game = game
        weight_text = _('Weight: {current} / {max} kg.').format(current=str(round(self.game.player.carried_weight, 2)),
                                                                max=str(round(
                                                                    self.game.player.properties['max_carry_weight'],
                                                                    2)))
        self.weight_bar = LabelViewFixed(text=weight_text,
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


class DropItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of items to drop one """

    def option_activated(self, *args, **kwargs):
        """ Method to drop item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_drop_item, self.game.player, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class ThrowItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of items to throw one """

    def option_activated(self, *args, **kwargs):
        """ Method to initiate item throwing target selection when option is activated (ENTER key pressed) """
        rn = self.game.player.get_throw_range(self.options[self.selected])
        if rn > 0:
            self.director.main_game_scene.start_targeting(range=rn,
                                                          t_object=self.options[self.selected],
                                                          eligible_types=(game_logic.BattleEntity, 'point'),
                                                          callback=commands.command_throw,
                                                          player=self.game.player,
                                                          item=self.options[self.selected])
        super().option_activated(*args, **kwargs)


class FireItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of ranged weapons to throw one """

    def option_activated(self, *args, **kwargs):
        """ Method to initiate item throwing target selection when option is activated (ENTER key pressed) """
        if len(self.options[self.selected].ammo) > 0:  # check if loaded
            self.director.main_game_scene.start_targeting(range=self.options[self.selected].range,
                                                          t_object=self.options[self.selected],
                                                          eligible_types=(game_logic.BattleEntity, 'point'),
                                                          callback=commands.command_fire,
                                                          player=self.game.player,
                                                          weapon=self.options[self.selected])
        else:
            game_logic.Game.add_message(_("{weapon} isn't loaded!").format(weapon=_(self.options[self.selected].name)),
                                        'PLAYER', [255, 255, 255])
        super().option_activated(*args, **kwargs)


class AmmoItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of ammo items to load one """

    def __init__(self, ranged_weapon, *args, **kwargs):
        self.ranged_weapon = ranged_weapon
        super().__init__(*args, **kwargs)

    def option_activated(self, *args, **kwargs):
        """ Method to load ammo when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_reload, self.game.player, self.ranged_weapon, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class UseItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of items to use one """

    def option_activated(self, *args, **kwargs):
        """ Method to use item when option is activated (ENTER key pressed) """
        commands.command_use_item(self.game, self.options[self.selected], self.director.main_game_scene)
        super().option_activated(*args, **kwargs)


class InventorySelectionScene(ItemSelectionScene):
    """ Scene displays a list of items to perform different actions """

    def option_activated(self, *args, **kwargs):
        """ Method to show item manipulation dialog when option is activated (ENTER key pressed) """
        director = self.director
        super().option_activated(*args, **kwargs)  # first pop this scene
        director.push_scene(ItemManipulationSelectionScene(game=self.game,
                                                           item=self.options[self.selected],
                                                           layout_options='intrinsic'))


class TakeOffItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of equipped items to take off one """

    def option_activated(self, *args, **kwargs):
        """ Method to take off item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_unequip_item, self.game.player, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class PickUpItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of items to pick up one """

    def option_activated(self, *args, **kwargs):
        """ Method to pick up item when option is activated (ENTER key pressed) """
        self.game.player.perform(actions.act_pick_up_item, self.game.player, self.options[self.selected])
        super().option_activated(*args, **kwargs)


class WieldItemSelectionScene(ItemSelectionScene):
    """ Scene displays a list of items to wield one """

    def option_activated(self, *args, **kwargs):
        """ Method to wield item or display slot dialog when option is activated (ENTER key pressed) """
        slot = False
        if len(self.options[self.selected].equip_slots) > 1:
            director = self.director
            super().option_activated(*args, **kwargs)  # first pop this scene
            director.push_scene(WieldSlotSelectionScene(game=self.game,
                                                        item=self.options[self.selected],
                                                        caption=_('Select slot:'),
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

class MerchantScene(UIScene):
    """ Scene that displays buy/sell menu """
    def __init__(self, game, merchant, layout_options=None, *args, **kwargs):
        """
        :param game: Game object 
        :param merchant: Merchant object
        :param args: arguments for UIScene
        :param kwargs: keywords arguments for UIScene
        """
        self.game = game
        self.merchant = merchant
        self.focus = 'player_items'  # scene area focus, cycled by TAB
        self.selling = set()
        self.buying = set()
        # pick only buyable by this merchant
        self.player_items = [i for i in self.game.player.inventory if self.merchant.check_buyable(i)]
        self.merchant_items = [i for i in merchant.inventory]
        self.player_items_view = VerticalScrollingLabelList(strings=self.player_items,
                                                            layout_options=LayoutOptions(left=0, right=0.7))
        self.merchant_items_view = VerticalScrollingLabelList(strings=self.merchant_items,
                                                              layout_options=LayoutOptions(left=0.7, right=0))
        self.middle_window = WindowView(title='', style='double',
                                        layout_options=LayoutOptions(left=0.3, right=0.3))
        subviews = [self.player_items_view, self.merchant_items_view, self.middle_window]
        self.window_view = WindowView(title=str(merchant),
                                      style='double',
                                      layout_options=layout_options or LayoutOptions(left=0, top=0),
                                      subviews=subviews)
        self.active_tab = self.player_items_view
        self.active_tab.color_fg = '#888888'  # make inactive tab darker
        self.active_tab.hl_color_fg = '#008800'
        self.active_tab.recolor()
        self.active_tab = self.merchant_items_view  # set merchant tab to active
        self.merchant_items_view.selected = 0  # select first merchant item
        super().__init__(views=[self.window_view], *args, **kwargs)

    def terminal_read(self, val):
        super().terminal_read(val)
        if val in (terminal.TK_TAB, terminal.TK_KP_8, terminal.TK_KP_2, terminal.TK_UP, terminal.TK_DOWN):
            if val == terminal.TK_TAB:  # change active tab
                if self.active_tab == self.merchant_items_view:
                    self.active_tab.color_fg = '#888888'  # make inactive tab darker
                    self.active_tab.hl_color_fg = '#008800'
                    self.active_tab.recolor()
                    self.active_tab = self.player_items_view
                    self.active_tab.color_fg = '#ffffff'  # and active - brighter
                    self.active_tab.hl_color_fg = '#00ff00'
                    self.active_tab.recolor()
                else:
                    self.active_tab.color_fg = '#888888'  # make inactive tab darker
                    self.active_tab.hl_color_fg = '#008800'
                    self.active_tab.recolor()
                    self.active_tab = self.merchant_items_view
                    self.active_tab.color_fg = '#ffffff'  # and active - brighter
                    self.active_tab.hl_color_fg = '#00ff00'
                    self.active_tab.recolor()
                if self.active_tab.selected is None:  # if tab became active - there has to be cursor
                    self.active_tab.select_next()
            elif val in (terminal.TK_KP_8, terminal.TK_UP):
                self.active_tab.select_prev()
            elif val in (terminal.TK_KP_2, terminal.TK_DOWN):
                self.active_tab.select_next()
        elif val == terminal.TK_SPACE:  # select/unselect item for selling or buyng
            if self.active_tab == self.merchant_items_view:
                if self.merchant_items[self.active_tab.selected] in self.selling:
                    self.merchant_items_view.unhighlight(self.active_tab.selected)
                    self.selling.remove(self.merchant_items[self.active_tab.selected])
                else:
                    self.merchant_items_view.highlight(self.active_tab.selected)
                    self.selling.add(self.merchant_items[self.active_tab.selected])
            elif self.active_tab == self.player_items_view:
                if self.player_items[self.active_tab.selected] in self.buying:
                    self.player_items_view.unhighlight(self.active_tab.selected)
                    self.buying.remove(self.player_items[self.active_tab.selected])
                else:
                    self.player_items_view.highlight(self.active_tab.selected)
                    self.buying.add(self.player_items[self.active_tab.selected])
        elif val == terminal.TK_ESCAPE:
            self.director.pop_scene()
            return True
        elif val == terminal.TK_RESIZED:
            self.player_items_view.scrolling_mode_check()
            self.merchant_items_view.scrolling_mode_check()
        return False


class MainMenuScene(UIScene):
    """ Scene with main menu options """

    def __init__(self, *args, **kwargs):
        views = []
        self.game = save_load.load_game()  # try to load game
        views.append(LabelViewFixed(
            LOGO[1:].rstrip(),
            layout_options=LayoutOptions.row_top(0.5)))
        views.append(LabelViewFixed(
            _("Choose one of the options below:"),
            layout_options=LayoutOptions.centered('intrinsic', 'intrinsic')))
        if self.game:  # is game succesfully loaded - show Continue button
            views.append(ButtonViewFixed(
                text=_("Continue"), callback=self.continue_game,
                layout_options=LayoutOptions.row_bottom(4).with_updates(
                    left=0.2, width=0.2, right=None)))
        else:  # if no savegame - show option greyed-out
            views.append(LabelViewFixed(
                text=_("[color=grey]Continue"),
                layout_options=LayoutOptions.row_bottom(4).with_updates(
                    left=0.2, width=0.2, right=None)))
        views.append(ButtonViewFixed(
            text=_("New Game"), callback=self.new_game,
            layout_options=LayoutOptions.row_bottom(4).with_updates(
                left=0.4, width=0.2, right=None)))
        views.append(ButtonViewFixed(
            text=_("Quit"),
            callback=lambda: self.director.quit(),
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
        elif val == terminal.TK_ESCAPE:  # prompt exit game on esc
            text = _('Do you really want to quit?')
            self.director.push_scene(MultiButtonMessageScene(buttons=[(_('Yes'), text, lambda: self.director.quit()),
                                                                      (_('No'), text, None)],
                                                             title=_('Confirm exit'),
                                                             layout_options='intrinsic'))
        self.ctx.clear()

    def become_active(self):
        self.ctx.clear()

    def new_game(self):
        director = self.director
        director.push_scene(CharacterSelectScene())

    def continue_game(self):
        director = self.director
        director.game = self.game
        director.push_scene(MainGameScene(self.game))
        if self.game.state == 'camp':
            director.push_scene(CampMenuScene(self.game))


class LoadingScene(UIScene):
    """ Loading scene - currently a placeholder """

    def __init__(self, watch_thread=None, *args, **kwargs):
        self.watch_thread = watch_thread
        views = [LabelViewFixed(
            LOADING[1:].rstrip(),
            layout_options=LayoutOptions.row_top(0.5))]
        super().__init__(views, *args, **kwargs)

    def terminal_update(self, is_active=False):
        if self.watch_thread:  # every frame check if specified thread is alive. If not, pop Loading scene
            if not self.watch_thread.is_alive():
                if self.director.active_scene == self:
                    self.director.pop_scene()
        super().terminal_update(is_active=is_active)

    def become_active(self):
        self.ctx.clear()


class MainGameScene(UIScene):
    """ Main game scene """

    def __init__(self, game, *args, **kwargs):
        self.game = game
        self._title = ''
        self.state = 'default'  # game UI state (can be 'looking', 'targeting', etc)
        self.target_info = {}  # dictionary containing targeting information when in 'targeting' state
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
        self.map_view.clear = True
        self.cell_info_view = LookView(game=game, map_view=self.map_view, layout_options=LayoutOptions(
            left=0.62,
            top=8,
            right=1,
            bottom=1))
        self.cell_info_view.is_hidden = True
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
        self._title_label = LabelViewFixed(text='',
                                           layout_options=LayoutOptions.row_top(1).with_updates(width='intrinsic',
                                                                                                left=0.3,
                                                                                                right=None))
        self._title_label.clear = True
        self._buffs_bar = LabelViewFixed(text='',
                                         layout_options=LayoutOptions.row_bottom(1).with_updates(width='intrinsic',
                                                                                                 left=0.1,
                                                                                                 right=None))
        self._buffs_bar.clear = True
        views = [self.map_view,
                 RectView(style='double', layout_options=LayoutOptions(left=0, top=0)),
                 RectView(style='double', layout_options=LayoutOptions().column_left(1).with_updates(
                     left=0.61,
                     right=None)),
                 self._title_label,
                 self._buffs_bar,
                 self.bars_view,
                 self.log_view,
                 self.cell_info_view]
        super().__init__(views, *args, **kwargs)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, text):
        """ Window title setter """
        self._title = str(text)
        self._title_label.text = self._title
        self._title_label.set_needs_layout(True)

    def start_targeting(self, range, t_object, callback, eligible_types, *args, **kwargs):
        """ Method that accepts targeting info and changes Scene state to 'targeting' """
        self.target_info = {'range': range,  # targeting max range
                            't_object': t_object,  # targetable object
                            'callback': callback,  # function to call when target is chosen
                            'eligible_types': eligible_types,  # eligible target types
                            'args': args,
                            'kwargs': kwargs}
        self.state = 'targeting'
        self.title = _('TARGETING: {t_object}').format(t_object=str(t_object))
        self.cell_info_view.is_hidden = False
        self.log_view.is_hidden = True
        self.map_view.cam_offset = [0, 0]

    def stop_targeting(self):
        """ Method that changes Scene state back to 'default' from 'targeting' """
        self.target_info.clear()
        self._set_default_state()

    def check_target(self):
        """ Method that checks if target belongs to one of eligible target types """
        target = False
        tx = self.game.player.position[0] + self.map_view.cam_offset[0]  # target cell coordinates
        ty = self.game.player.position[1] + self.map_view.cam_offset[1]
        for t in self.target_info['eligible_types']:
            entity = self.game.player.location.cells[tx][ty].is_there_a(t)
            if entity:
                return entity
        if 'point' in self.target_info['eligible_types'] and self.game.current_loc.is_in_boundaries(tx, ty):
            return tx, ty

    def become_active(self):
        if not self.director.main_game_scene:
            self.director.main_game_scene = self
        elif self.director.main_game_scene == self:
            pass
        else:
            raise (RuntimeError('More than one main game scene!'))
        self.ctx.clear()
        self.map_view.force_redraw = True  # to draw map right after

    def terminal_update(self, is_active=False):
        """ Update values in bars and tabs before drawing """
        player = self.game.player
        if is_active:
            self.health_bar.text = _('{hp}/{max_hp} HP').format(hp=str(player.hp), max_hp=str(player.maxhp))
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
            self.player_right_hand.text = _('Right: {right}').format(right=str(right))
            left = player.equipment['LEFT_HAND']
            self.player_left_hand.text = _('Left: {left}').format(left=str(left))
            money = player.properties['money']
            self.money.text = _('Money: {money} coins.').format(money=str(money))
            filled_lines = 0
            buffs_line = ''
            if player.carried_weight > player.properties['max_carry_weight'] * 1.5:
                buffs_line += '[color=red]{eff}[color=dark white]══[/color]'.format(eff=_('OVERBURDENED'))
                filled_lines += 1
            elif player.carried_weight > player.properties['max_carry_weight']:
                buffs_line += '[color=yellow]{eff}[color=dark white]══[/color]'.format(eff=_('BURDENED'))
                filled_lines += 1
            for effect in self.game.player.effects:
                if filled_lines < 6:
                    if effect.eff == 'POISONED':
                        buffs_line += '[color=green]{eff}[color=dark white]══[/color]'.format(eff=_(effect.eff))
                        filled_lines += 1
                    elif effect.eff == 'HASTE':
                        buffs_line += '[color=yellow]{eff}[color=dark white]══[/color]'.format(eff=_(effect.eff))
                        filled_lines += 1
                    elif effect.eff == 'SLOWED':
                        buffs_line += '[color=blue]{eff}[color=dark white]══[/color]'.format(eff=_(effect.eff))
                        filled_lines += 1
            if self._buffs_bar.text != buffs_line:
                self._buffs_bar.text = buffs_line
                self._buffs_bar.set_needs_layout(True)
                self._buffs_bar.frame.width = self._buffs_bar.intrinsic_size.width
        super().terminal_update(is_active=is_active)

    def terminal_read(self, val):
        """ This method handles player input in main scene """
        handled = False
        if self.state == 'default':
            handled = self._handle_input_default(val=val)
        elif self.state == 'looking':
            handled = self._handle_input_looking(val=val)
        elif self.state == 'targeting':
            handled = self._handle_input_targeting(val=val)
        elif self.state == 'closing_door':
            handled = self._handle_input_closing_door(val=val)
        elif self.state == 'smashing':
            handled = self._handle_input_smashing(val=val)
        super().terminal_read(val)
        return handled

    def _set_default_state(self):
        """ Method that sets UI state to 'default' """
        self.state = 'default'
        self.title = ''
        self.cell_info_view.is_hidden = True
        self.log_view.is_hidden = False
        self.map_view.cam_offset = [0, 0]

    def _handle_input_default(self, val):
        """ This method handles player input in 'default' state """
        player_input = val
        game = self.game
        player = game.player
        handled = False  # input handled flag
        if game.is_waiting_input:
            if player_input == terminal.TK_ESCAPE:  # game quit on ESC
                text = _('Do you really want to quit?')
                self.director.push_scene(
                    MultiButtonMessageScene(buttons=[(_('Yes'), text, lambda: self.director.quit()),
                                                     (_('No'), text, None)],
                                            title=_('Confirm exit'),
                                            layout_options='intrinsic'))
                handled = True
            # movement commands
            elif player_input in (terminal.TK_KP_4, terminal.TK_LEFT):
                commands.command_default_direction(game=game, dx=-1, dy=0)
                handled = True
            elif player_input in (terminal.TK_KP_6, terminal.TK_RIGHT):
                commands.command_default_direction(game=game, dx=1, dy=0)
                handled = True
            elif player_input in (terminal.TK_KP_8, terminal.TK_UP):
                commands.command_default_direction(game=game, dx=0, dy=-1)
                handled = True
            elif player_input in (terminal.TK_KP_2, terminal.TK_DOWN):
                commands.command_default_direction(game=game, dx=0, dy=1)
                handled = True
            elif player_input == terminal.TK_KP_7:
                commands.command_default_direction(game=game, dx=-1, dy=-1)
                handled = True
            elif player_input == terminal.TK_KP_9:
                commands.command_default_direction(game=game, dx=1, dy=-1)
                handled = True
            elif player_input == terminal.TK_KP_1:
                commands.command_default_direction(game=game, dx=-1, dy=1)
                handled = True
            elif player_input == terminal.TK_KP_3:
                commands.command_default_direction(game=game, dx=1, dy=1)
                handled = True
            elif player_input == terminal.TK_KP_5:  # wait for ticks=player.speed (1 turn)
                player.perform(actions.act_wait, game.player, game.player.speed)
                handled = True
            elif player_input == 53:  # on '`' show debug messages in log
                if game.show_debug_log:
                    game.show_debug_log = False
                else:
                    game.show_debug_log = True
                handled = True
            elif player_input == terminal.TK_G:  # pick up item
                commands.command_pick_up(game=game, dx=0, dy=0)
                handled = True
            elif player_input == terminal.TK_R:  # reload ranged weapon
                commands.command_reload_equipped(game=game)
                handled = True
            elif player_input == terminal.TK_N:  # uNload ranged weapon
                for item in player.equipment.values():  # unload every equipped item
                    if isinstance(item, game_logic.ItemRangedWeapon):
                        player.perform(actions.act_unload, player, item)
                handled = True
            elif player_input == terminal.TK_I:  # show inventory
                self.director.push_scene(InventorySelectionScene(items=player.inventory,
                                                                 game=game,
                                                                 caption=_('Inventory'),
                                                                 layout_options=LayoutOptions(
                                                                     top=0.1, bottom=0.1,
                                                                     left=0.2, right=0.2)))
                handled = True
            elif player_input == terminal.TK_D:  # drop item
                self.director.push_scene(DropItemSelectionScene(items=player.inventory,
                                                                game=game,
                                                                caption=_('Drop item:'),
                                                                layout_options=LayoutOptions(
                                                                    top=0.1, bottom=0.1,
                                                                    left=0.2, right=0.2)))
                handled = True
            elif player_input == terminal.TK_U:  # use item
                self.director.push_scene(UseItemSelectionScene(items=player.inventory,
                                                               game=game,
                                                               caption=_('Use item:'),
                                                               layout_options=LayoutOptions(
                                                                   top=0.1, bottom=0.1,
                                                                   left=0.2, right=0.2)))
                handled = True
            elif player_input == terminal.TK_W:  # wield item
                self.director.push_scene(WieldItemSelectionScene(items=player.inventory,
                                                                 game=game,
                                                                 caption=_('Wield item:'),
                                                                 layout_options=LayoutOptions(
                                                                     top=0.1, bottom=0.1,
                                                                     left=0.2, right=0.2)))
                handled = True
            elif player_input == terminal.TK_O:  # take 'o'ff
                self.director.push_scene(TakeOffItemSelectionScene(items=[sl for sl in
                                                                          list(player.equipment.values()) if sl],
                                                                   game=game,
                                                                   caption=_('Take off item:'),
                                                                   layout_options=LayoutOptions(
                                                                       top=0.1, bottom=0.1,
                                                                       left=0.2, right=0.2)))
                handled = True
            elif player_input == terminal.TK_F1:  # help message windows
                self.director.push_scene(SingleButtonMessageScene(message=HELP_TEXT,
                                                                  title=_('Help'),
                                                                  layout_options='intrinsic'))
                handled = True
            elif player_input == terminal.TK_F11:  # debug command exec
                self.director.push_scene(DebugLineInputScene(game=game))
                handled = True
            elif player_input == terminal.TK_L:  # look
                self.state = 'looking'
                self.title = _('LOOKING:')
                self.cell_info_view.is_hidden = False
                self.log_view.is_hidden = True
                self.map_view.cam_offset = [0, 0]
                handled = True
            elif player_input == terminal.TK_C:  # close door
                self.state = 'closing_door'
                self.title = _('CLOSE WHERE:')
                handled = True
            elif player_input == terminal.TK_S:  # smash
                self.state = 'smashing'
                self.title = _('SMASH WHERE:')
                handled = True
            elif player_input == terminal.TK_T:  # throw
                commands.command_throw_choose(game=self.game, main_scene=self)
                handled = True
            elif player_input == terminal.TK_F:  # fire ranged weapon
                commands.command_fire_choose(game=self.game)
                handled = True
            if handled:
                game.start_update_thread()
            return handled

    def _handle_input_looking(self, val):
        """ This method handles player input in 'default' state """
        player_input = val
        handled = False  # input handled flag
        if player_input == terminal.TK_ESCAPE:  # exit to default state
            self._set_default_state()
            handled = True
        # camera offset change with directional keys
        elif player_input in (terminal.TK_KP_4, terminal.TK_LEFT):
            self.map_view.move_camera(-1, 0)
            handled = True
        elif player_input in (terminal.TK_KP_6, terminal.TK_RIGHT):
            self.map_view.move_camera(1, 0)
            handled = True
        elif player_input in (terminal.TK_KP_8, terminal.TK_UP):
            self.map_view.move_camera(0, -1)
            handled = True
        elif player_input in (terminal.TK_KP_2, terminal.TK_DOWN):
            self.map_view.move_camera(0, 1)
            handled = True
        elif player_input == terminal.TK_KP_7:
            self.map_view.move_camera(-1, -1)
            handled = True
        elif player_input == terminal.TK_KP_9:
            self.map_view.move_camera(1, -1)
            handled = True
        elif player_input == terminal.TK_KP_1:
            self.map_view.move_camera(-1, 1)
            handled = True
        elif player_input == terminal.TK_KP_3:
            self.map_view.move_camera(1, 1)
            handled = True
        if handled:
            self.map_view.force_redraw = True  # to redraw map faster
        return handled

    def _handle_input_closing_door(self, val):
        """ This method handles player input in 'closing_door' state """
        player_input = val
        handled = False  # input handled flag
        if player_input == terminal.TK_ESCAPE:  # exit to default state
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_4, terminal.TK_LEFT):
            commands.command_close_direction(player=self.game.player, dx=-1, dy=0)
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_6, terminal.TK_RIGHT):
            commands.command_close_direction(player=self.game.player, dx=1, dy=0)
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_8, terminal.TK_UP):
            commands.command_close_direction(player=self.game.player, dx=0, dy=-1)
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_2, terminal.TK_DOWN):
            commands.command_close_direction(player=self.game.player, dx=0, dy=1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_7:
            commands.command_close_direction(player=self.game.player, dx=-1, dy=-1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_9:
            commands.command_close_direction(player=self.game.player, dx=1, dy=-1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_1:
            commands.command_close_direction(player=self.game.player, dx=-1, dy=1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_3:
            commands.command_close_direction(player=self.game.player, dx=1, dy=1)
            self._set_default_state()
            handled = True
        if handled:
            self.game.start_update_thread()
            self.map_view.force_redraw = True  # to redraw map faster
        return handled

    def _handle_input_smashing(self, val):
        """ This method handles player input in 'closing_door' state """
        player_input = val
        handled = False  # input handled flag
        if player_input == terminal.TK_ESCAPE:  # exit to default state
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_4, terminal.TK_LEFT):
            commands.command_smash_direction(player=self.game.player, dx=-1, dy=0)
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_6, terminal.TK_RIGHT):
            commands.command_smash_direction(player=self.game.player, dx=1, dy=0)
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_8, terminal.TK_UP):
            commands.command_smash_direction(player=self.game.player, dx=0, dy=-1)
            self._set_default_state()
            handled = True
        elif player_input in (terminal.TK_KP_2, terminal.TK_DOWN):
            commands.command_smash_direction(player=self.game.player, dx=0, dy=1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_7:
            commands.command_smash_direction(player=self.game.player, dx=-1, dy=-1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_9:
            commands.command_smash_direction(player=self.game.player, dx=1, dy=-1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_1:
            commands.command_smash_direction(player=self.game.player, dx=-1, dy=1)
            self._set_default_state()
            handled = True
        elif player_input == terminal.TK_KP_3:
            commands.command_smash_direction(player=self.game.player, dx=1, dy=1)
            self._set_default_state()
            handled = True
        if handled:
            self.game.start_update_thread()
            self.map_view.force_redraw = True  # to redraw map faster
        return handled

    def _handle_input_targeting(self, val):
        """ This method handles player input in 'targeting' state """
        player_input = val
        handled = False  # input handled flag
        if player_input == terminal.TK_ESCAPE:  # exit to default state
            self.stop_targeting()
            handled = True
        elif player_input == terminal.TK_ENTER:  # if player chooses the cell
            target = self.check_target()
            if target:
                self.target_info['callback'](target=target, *self.target_info['args'], **self.target_info['kwargs'])
                self.stop_targeting()
                self.game.start_update_thread()
            handled = True
        # camera offset change with directional keys, check targeting range before camera move
        elif player_input in (terminal.TK_KP_4, terminal.TK_LEFT):
            if hypot(self.map_view.cam_offset[0] - 1, self.map_view.cam_offset[1]) <= self.target_info['range']:
                self.map_view.move_camera(-1, 0)
            handled = True
        elif player_input in (terminal.TK_KP_6, terminal.TK_RIGHT):
            if hypot(self.map_view.cam_offset[0] + 1, self.map_view.cam_offset[1]) <= self.target_info['range']:
                self.map_view.move_camera(1, 0)
            handled = True
        elif player_input in (terminal.TK_KP_8, terminal.TK_UP):
            if hypot(self.map_view.cam_offset[0], self.map_view.cam_offset[1] - 1) <= self.target_info['range']:
                self.map_view.move_camera(0, -1)
            handled = True
        elif player_input in (terminal.TK_KP_2, terminal.TK_DOWN):
            if hypot(self.map_view.cam_offset[0], self.map_view.cam_offset[1] + 1) <= self.target_info['range']:
                self.map_view.move_camera(0, 1)
            handled = True
        elif player_input == terminal.TK_KP_7:
            if hypot(self.map_view.cam_offset[0] - 1, self.map_view.cam_offset[1] - 1) < self.target_info['range']:
                self.map_view.move_camera(-1, -1)
            handled = True
        elif player_input == terminal.TK_KP_9:
            if hypot(self.map_view.cam_offset[0] + 1, self.map_view.cam_offset[1] - 1) < self.target_info['range']:
                self.map_view.move_camera(1, -1)
            handled = True
        elif player_input == terminal.TK_KP_1:
            if hypot(self.map_view.cam_offset[0] - 1, self.map_view.cam_offset[1] + 1) < self.target_info['range']:
                self.map_view.move_camera(-1, 1)
            handled = True
        elif player_input == terminal.TK_KP_3:
            if hypot(self.map_view.cam_offset[0] + 1, self.map_view.cam_offset[1] + 1) < self.target_info['range']:
                self.map_view.move_camera(1, 1)
            handled = True
        if handled:
            self.map_view.force_redraw = True  # to redraw map faster
        return handled


class DebugLineInputScene(UIScene):
    """ Scene that allows debug commands entering and execution """

    def __init__(self, game, *args, **kwargs):
        self.game = game
        views = [SingleLineTextInputView(callback=self._execute, layout_options=LayoutOptions.row_top(5))]
        super().__init__(views, *args, **kwargs)

    def _execute(self, text):
        director = self.director
        director.pop_scene()
        if text == 'testscene':
            director.push_scene(TestingViewsScene())
            return
        commands.command_execute_debug_line(line=text, game=self.game)


class TestingViewsScene(UIScene):
    """ Scene to test Views """
    def __init__(self, *args, **kwargs):
        self.scroll_list = VerticalScrollingLabelList(strings=[i for i in range(50)])
        views = [self.scroll_list]
        super().__init__(views, *args, **kwargs)

    def terminal_read(self, val):
        super().terminal_read(val)
        # cycle descriptions with selected options
        if val in (terminal.TK_TAB, terminal.TK_KP_8, terminal.TK_KP_2, terminal.TK_UP, terminal.TK_DOWN):
            # allow traverse with arrows and numpad
            if val == terminal.TK_TAB:
                self.scroll_list.select_next()
            elif val in (terminal.TK_KP_8, terminal.TK_UP):
                self.scroll_list.select_prev()
            elif val in (terminal.TK_KP_2, terminal.TK_DOWN):
                self.scroll_list.select_next()
            return True
        elif val == terminal.TK_ESCAPE:
            self.director.pop_scene()
            return True
        elif val == terminal.TK_RESIZED:
            self.scroll_list.scrolling_mode_check()
        return False


# Views

class MapView(View):
    """ View with game map """

    def __init__(self, game, *args, **kwargs):
        self.game = game  # game object reference for obtaining map info
        self.cam_offset = [0, 0]  # camera offset (if looking or targeting)
        self.last_game_time = game.time_system.current_time()  # last game time (to know when redraw needed)
        self.tick = 0  # frame count (to know when redraw needed)
        self.force_redraw = False
        super().__init__(*args, **kwargs)

    @property
    def intrinsic_size(self):
        return Size(self.bounds.width, self.bounds.height)

    def move_camera(self, dx, dy):
        """ Method that alters camera offset by given numbers """
        player_x = self.game.player.position[0]
        player_y = self.game.player.position[1]
        rel_x = player_x + self.cam_offset[0]  # game location coordinates in accordance to screen coordinates
        rel_y = player_y + self.cam_offset[1]
        if self.game.current_loc.is_in_boundaries(rel_x + dx, rel_y + dy):
            self.cam_offset[0] += dx
            self.cam_offset[1] += dy

    @staticmethod
    def cell_graphics(x, y, cell, loc, visible):
        """ Method that returns graphic representation of tile. """
        char = ' '
        color = [255, 255, 255]
        bgcolor = [0, 0, 0]
        if visible:  # check if cell is visible
            return cell.get_cell_graphics()
        elif cell.explored:  # check if it was previously explored
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
        if (self.last_game_time != self.game.time_system.current_time() or self.tick > 10) \
                or self.force_redraw:
            if self.force_redraw:
                self.force_redraw = False
            while self.game.player.state == 'performing':  # if player is acting - wait until action finishes
                time.sleep(0.05)
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
                        terminal.printf(self.layout_options.left + x * 2, self.layout_options.top + y,
                                        '[font=map]' + cg[0])

                    else:
                        ctx.bkcolor(terminal.color_from_argb(255, 0, 0, 0))
                        terminal.printf(self.layout_options.left + x * 2, self.layout_options.top + y, '[font=map] ')
            if not self.cam_offset == [0, 0]:
                # if camera is not centered on player - draw there a red 'X'
                ctx.color(terminal.color_from_argb(255, 255, 0, 0))
                ctx.bkcolor(terminal.color_from_argb(255, 0, 0, 0))
                # some magic - center of the map coordinates correction
                sub_x = 0
                magic = self.bounds.width % 4
                # check width divided by 4 and apply correction
                if magic == 1:
                    sub_x = 0
                elif magic == 2:
                    sub_x = 1
                elif magic == 3:
                    sub_x = 1
                terminal.printf(self.layout_options.left + self.bounds.width // 2 - sub_x,
                                self.layout_options.top + self.bounds.height // 2, '[font=map]X')
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
        super().draw(ctx)
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
        log_lines = log_lines[-(self.bounds.height - 2):]  # slice list to log_height elements
        ctx.print(Point(0, 0), '=' * self.bounds.width)
        y = 1
        for line in log_lines:
            y += 1
            ctx.color(terminal.color_from_argb(255, line[1][0], line[1][1], line[1][2]))
            ctx.print(Point(0, y), line[0])  # draw each line


class LookView(View):
    """ View with description of cell player looking at """

    def __init__(self, game, map_view, *args, **kwargs):
        self.game = game  # game object reference for obtaining map info
        self.map_view = map_view  # map_view needed to obtain cam_offset
        self.clear = True  # clear before each draw
        super().__init__(*args, **kwargs)

    @property
    def intrinsic_size(self):
        return Size(self.bounds.width, self.bounds.height)

    def draw(self, ctx):
        super().draw(ctx)
        if (self.game.player.position[0] + self.map_view.cam_offset[0],
            self.game.player.position[1] + self.map_view.cam_offset[1]) in self.game.player.fov_set:  # if in FOV
            entities = self.game.current_loc.cells[self.game.player.position[0] + self.map_view.cam_offset[0]][
                self.game.player.position[1] + self.map_view.cam_offset[1]].entities  # get entities @ selected cell
            creatures = [ent for ent in entities if ent.occupies_tile]
            items = [ent for ent in entities if isinstance(ent, game_logic.Item)]
            other = [ent for ent in entities if (not isinstance(ent, game_logic.Item)) and (not ent.occupies_tile)]
            ctx.print(Point(0, 0), '=' * self.bounds.width)
            cur_y = 1  # a 'cursor' y position
            for creature in creatures:  # show creature info if any
                if creature.color[0] + creature.color[1] + creature.color[2] < 100:  # if creature color is too dark
                    col = (255, 255, 255)  # show name in white
                else:
                    col = creature.color
                ctx.color(terminal.color_from_argb(255, col[0], col[1], col[2]))
                ctx.print(Point(0, cur_y), _('{creature_name} is here.').format(creature_name=str(creature)))
                ctx.color(terminal.color_from_name('white'))
                cur_y += 1
                for ln in textwrap.wrap(creature.description, self.bounds.width):
                    ctx.print(Point(0, cur_y), ln)
                    cur_y += 1
            ctx.print(Point(0, cur_y), _('Items:'))
            cur_y += 1
            for item in items:  # show items if any
                ctx.color(terminal.color_from_argb(255, item.color[0], item.color[1], item.color[2]))
                ctx.print(Point(0, cur_y), _('{item_name} is here.').format(item_name=str(item)))
                ctx.color(terminal.color_from_name('white'))
                cur_y += 1
            ctx.print(Point(0, cur_y), _('Other:'))
            cur_y += 1
            for other in other:  # show other objects
                ctx.color(terminal.color_from_argb(255, other.color[0], other.color[1], other.color[2]))
                ctx.print(Point(0, cur_y), _('{other_name} is here.').format(other_name=str(other)))
                ctx.color(terminal.color_from_name('white'))
                cur_y += 1


class VerticalScrollingLabelList(View):
    """ View with list of labels, scrolling """

    def __init__(self, strings, color_fg='#ffffff', color_bg='#000000', hl_color_fg='#00ff00', hl_color_bg='#000000',
                 *args, **kwargs):
        """
        :param strings: strings to be placed
        :param color_fg: string text color
        :param color_bg: string background color
        :param hl_color_fg: highlighted string color
        :param hl_color_bg: highlighted string background color
        :param args: arguments to pass to View constructor
        :param kwargs: keywords of arguments to pass to View constructor
        """
        self.strings = list(strings)
        self.labels = []
        self.highlighted = set()
        top_offset = 0
        self.color_fg = color_fg
        self.color_bg = color_bg
        self.hl_color_fg = hl_color_fg
        self.hl_color_bg = hl_color_bg
        # labels creation
        for string in self.strings:
            if isinstance(string, game_logic.Entity):
                l_text = str(string)  # entity name already translated
            else:
                l_text = _(str(string))
            label = LabelViewFixed(text=l_text,
                                   layout_options=LayoutOptions(
                                       left=0,
                                       top=top_offset,
                                       width='intrinsic',
                                       height=1,
                                       bottom=None,
                                       right=None))
            label.is_hidden = True
            self.labels.append(label)
            top_offset += 1
        self._selected = None
        # scrolling initialization
        self.scrolling_mode = False
        self.scroll_pos = 0
        super().__init__(subviews=self.labels, clear=True, *args, **kwargs)

    @property
    def intrinsic_size(self):
        return Size(self.bounds.width, self.bounds.height)

    @property
    def selected(self):
        """
        :return: index of currently selected label 
        """
        return self._selected

    @selected.setter
    def selected(self, index):
        """
        :param index: of the label that must be selected, or None
        :return: None
        """
        if index is None:  # if none selected - unselect current
            fg = self.labels[self._selected].color_fg
            bg = self.labels[self._selected].color_bg
            self.labels[self._selected].color_fg = bg
            self.labels[self._selected].color_bg = fg
            self._selected = index
        elif self._selected != index and 0 <= index < len(self.labels):
            # revert colors of unselected label back
            if self._selected is not None:
                fg = self.labels[self._selected].color_fg
                bg = self.labels[self._selected].color_bg
                self.labels[self._selected].color_fg = bg
                self.labels[self._selected].color_bg = fg
            self._selected = index
            # invert colors of the new selected label
            fg = self.labels[self._selected].color_fg
            bg = self.labels[self._selected].color_bg
            self.labels[self._selected].color_fg = bg
            self.labels[self._selected].color_bg = fg
            if self.scrolling_mode:
                self._scroll()

    def highlight(self, index):
        """ Highlight string by index (change color) """
        if index == self.selected:
            self.labels[index].color_fg = self.hl_color_bg
            self.labels[index].color_bg = self.hl_color_fg
        else:
            self.labels[index].color_fg = self.hl_color_fg
            self.labels[index].color_bg = self.hl_color_bg
        self.highlighted.add(index)

    def unhighlight(self, index):
        """ Remove highlighting string by index (change color) """
        if index == self.selected:
            self.labels[index].color_fg = self.color_bg
            self.labels[index].color_bg = self.color_fg
        else:
            self.labels[index].color_fg = self.color_fg
            self.labels[index].color_bg = self.color_bg
        self.highlighted.remove(index)

    def recolor(self):
        """ Method to call when some of the View colors changes """
        i = 0
        for label in self.labels:
            if i in self.highlighted:
                if i == self.selected:
                    label.color_fg = self.hl_color_bg
                    label.color_bg = self.hl_color_fg
                else:
                    label.color_fg = self.hl_color_fg
                    label.color_bg = self.hl_color_bg
            else:
                if i == self.selected:
                    label.color_fg = self.color_bg
                    label.color_bg = self.color_fg
                else:
                    label.color_fg = self.color_fg
                    label.color_bg = self.color_bg
            i += 1

    def select_next(self):
        if self.selected is None:
            self.selected = 0
        elif self.selected < len(self.labels) - 1:
            self.selected += 1
        else:
            self.selected = 0

    def select_prev(self):
        if self.selected is None:
            self.selected = 0
        elif self.selected > 0:
            self.selected -= 1
        else:
            self.selected = len(self.labels) - 1

    def draw(self, ctx):
        """ Cannot determine view bounds in __init__, doing scroll check here """
        super().draw(ctx=ctx)
        self.scrolling_mode_check()
        if not self.scrolling_mode:
            for label in self.labels:
                label.is_hidden = False

    def scrolling_mode_check(self):
        """ Checks for height and enables/disables scrolling """
        list_height = self.bounds.height
        if list_height < len(self.labels):
            self.scrolling_mode = True
            self._scroll()
        else:
            self.scrolling_mode = False

    def _scroll(self):
        """ Method for scrolling the options list """
        list_height = self.bounds.height
        if self.selected is None:
            sel = 0
        else:
            sel = self.selected
        if sel < self.scroll_pos:
            self.scroll_pos = sel
        elif sel > self.scroll_pos + list_height - 1:
            self.scroll_pos = sel - list_height + 1
        label_y = 0
        for i in range(len(self.labels)):
            if self.scroll_pos <= i < (self.scroll_pos + list_height):
                self.labels[i].is_hidden = False
                self.labels[i].layout_options = self.labels[i].layout_options.with_updates(top=label_y)
                label_y += 1
            else:
                self.labels[i].is_hidden = True
            self.labels[i].superview.set_needs_layout()
        self.needs_layout = True

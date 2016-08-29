"""
    This file contains time-system and actions.
"""


class Action:
    """
        Class for action.
    """
    def __init__(self, func, args, kwargs, t_passed=0, t_needed=0, frozen=False):
        self.t_passed = t_passed  # ticks passed since action was registered (incremented externally by ActMgr)
        self.t_needed = t_needed  # ticks needed by action to fire
        self.frozen = frozen  # is action frozen (for stunning/timelock effects)
        self.func = func  # function that is called when action fires
        self.args = args
        self.kwargs = kwargs

    def fire_if_ready(self):
        """ Method that checks for if action is ready to fire, and does it """
        if self.t_passed >= self.t_needed:
            self.func(*self.args, **self.kwargs)
            return True
        return False


class ActionMgr:
    """
        Class for action manager.
    """
    def __init__(self):
        self.actions = []

    def register_action(self, t_needed, func, *args, **kwargs):
        """ Method creates an action and adds it to action list """
        action = Action(t_passed=0, t_needed=t_needed, frozen=False, func=func, args=args, kwargs=kwargs)
        self.actions.append(action)

    def pass_ticks(self, ticks=1):
        """ Method that increments tick count on actions, and makes them fire if ready """
        for action in self.actions:
            action.t_passed += ticks
            if action.fire_if_ready():
                self.actions.remove(action)


class TimeSystem:
    """
        Class for time-system.
    """
    def __init__(self):
        self._current_time = 0  # time starts from zero at initialization
        self.act_mgrs = []  # dict of action managers, registered in time system object

    def register_act_mgr(self, act_mgr):
        """ Method registers an action manager to time system. No duplicate registrations allowed """
        for a_m in self.act_mgrs:
            if a_m == act_mgr:
                return False
        self.act_mgrs.append(act_mgr)
        return True

    def unregister_act_mgr(self, act_mgr):
        """ Method unregisters an action manager to time system. """
        return self.act_mgrs.remove(act_mgr)

    def pass_time(self, ticks=1):
        """ Method passing time in time system. """
        self._current_time += ticks
        for act_mgr in self.act_mgrs:
            act_mgr.pass_ticks(ticks)

    def current_time(self):
        """ Method returning current time. """
        return self._current_time


# ============================= ACTION FUNCTIONS ================================================
def act_print_debug(text):
    """ Simple debug action, that prints a string to console """
    print(text)


def act_move(player, loc, dx, dy):
    """ Entity moving action """
    player_x = player.position[0]
    player_y = player.position[1]
    if not player.move(dx, dy):
        if loc.is_in_boundaries(player_x + dx, player_y + dy):
            door = loc.cells[player_x + dx][player_y + dy].is_there_a(Door)
            if door:
                player.open(dx, dy)
    player.state = 'ready'

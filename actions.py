"""
    This file contains time-system and actions.
"""
import game_logic


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
            self.func(self, False, *self.args, **self.kwargs)  # call an action function in normal mode
            return True
        return False

    def register(self):
        """ Method that runs action function in registration mode - when it is registered. Adjust action time
            according to actor speed, etc.
        """
        self.func(self, True, *self.args, **self.kwargs)  # call an action function in registration mode


class ActionMgr:
    """
        Class for action manager.
    """
    def __init__(self):
        self.actions = []

    def register_action(self, t_needed, func, *args, **kwargs):
        """ Method creates an action and adds it to action list """
        action = Action(t_passed=0, t_needed=t_needed, frozen=False, func=func, args=args, kwargs=kwargs)
        action.register()  # call action's func in register mode
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
def act_print_debug(action, register_call, text):
    """ Simple debug action, that prints a string to console """
    if register_call:  # part executed when function is registered in ActionMgr
        pass
    else:              # part that is executed when action fires
        print(text)


def act_move(action, register_call, actor, dx, dy):
    """ Actor self-moving action (need a different one for unvoluntarily movement, regardless of speed) """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed  # one move takes actor.speed ticks to perform
    else:  # part that is executed when action fires
        actor.move(dx, dy)  # move actor to desired coords
        if isinstance(actor, game_logic.Seer):  # check if entity is a Seer
            actor.compute_fov()  # compute actor's FOV TODO: rework testing visibility
        actor.state = 'ready'  # return actor to ready state


def act_open_door(action, register_call, actor, door):
    """ Actor opening door action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed // 4  # open door is a 1/4 speed action for now
    else:  # part that is executed when action fires
        actor.open(door)  # open the door
        if isinstance(actor, game_logic.Seer):  # check if entity is a Seer
            actor.compute_fov()  # compute actor's FOV TODO: rework testing visibility
        actor.state = 'ready'  # return actor to ready state


def act_close_door(action, register_call, actor, door):
    """ Actor closing door action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed // 4    # close door is a 1/4 speed action for now
    else:  # part that is executed when action fires
        actor.close(door)  # close the door
        if isinstance(actor, game_logic.Seer):  # check if entity is a Seer
            actor.compute_fov()  # compute actor's FOV TODO: rework testing visibility
        actor.state = 'ready'  # return actor to ready state

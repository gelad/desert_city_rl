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
        return action

    def remove_action(self, action):
        """ Method removes an action """
        self.actions.remove(action)

    def pass_ticks(self, ticks=1):
        """ Method that increments tick count on actions, and makes them fire if ready """
        for action in self.actions[:]:
            action.t_passed += ticks
            if action.fire_if_ready():
                self.remove_action(action)


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


def act_wait(action, register_call, actor, ticks):
    """ Actor waiting action (doing nothing) """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = ticks  # set desired wait time
    else:  # part that is executed when action fires
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_move(action, register_call, actor, dx, dy):
    """ Actor self-moving action (need a different one for unvoluntarily movement, regardless of speed) """
    if register_call:  # part executed when function is registered in ActionMgr
        if abs(dx)+abs(dy) == 2:  # if movement is diagonal
            action.t_needed = actor.speed * 1.414 // 3  # diagonal move takes 1.41 times longer
        else:  # if it's normal
            action.t_needed = actor.speed // 3  # actual movement occurs on 1/3 of step
    else:  # part that is executed when action fires
        actor.move(dx, dy)  # move actor to desired coords
        if isinstance(actor, game_logic.Seer):  # check if entity is a Seer
            actor.compute_fov()  # compute actor's FOV
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state
        #  withdrawal to make whole action take EXACTLY one step
        if abs(dx) + abs(dy) == 2:  # if movement is diagonal
            actor.perform(act_withdrawal, actor, actor.speed * 1.414 - actor.speed * 1.414 // 3)
        else:  # if it's normal
            actor.perform(act_withdrawal, actor, actor.speed - actor.speed // 3)


def act_attack_melee(action, register_call, actor, target):
    """ Actor melee attack """
    if register_call:  # part executed when function is registered in ActionMgr
        spd = 0
        weapons = 0  # weapons number equipped
        for item in actor.equipment.values():  # check if any weapons equipped
            if item:
                if 'weapon' in item.categories:  # correct speed if weapon(s)
                    weapons += 1
                    if 'speed_normal' in item.categories:
                        spd += actor.speed
                    elif 'speed_fast' in item.categories:
                        spd += actor.speed * 0.75
                    elif 'speed_slow' in item.categories:
                        spd += actor.speed * 1.75
        if weapons > 1:  # dual-wielding penalty
            spd *= 1.25
        elif weapons == 0:
            spd = actor.speed
        action.t_needed = spd / 2  # attack hit occurs on 1/2 swing duration
    else:  # part that is executed when action fires
        actor.attack_melee(target)  # attack target
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state
        # withdrawal to make whole action take EXACTLY actor.speed
        actor.perform(act_withdrawal, actor, action.t_needed * 2)


def act_reload(action, register_call, actor, weapon, ammo):
    """ Actor reloading ranged weapon """
    if register_call:  # part executed when function is registered in ActionMgr
        if 'crossbow' in weapon.categories:
            spd = actor.speed * 3
        elif 'bow' in weapon.categories:
            spd = actor.speed / 2
        else:  # if unknown type of ranged weapon
            spd = actor.speed
        action.t_needed = spd  # attack hit occurs on 1/2 swing duration
    else:  # part that is executed when action fires
        actor.reload(weapon, ammo)  # attack target
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_withdrawal(action, register_call, actor, ticks):
    """ Actor withdrawal """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = ticks  # set desired withdrawal time
        actor.state = 'withdrawal'
    else:  # part that is executed when action fires
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_open_door(action, register_call, actor, door):
    """ Actor opening door action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed / 4  # open door is a 1/4 speed action for now
    else:  # part that is executed when action fires
        actor.open(door)  # open the door
        if isinstance(actor, game_logic.Seer):  # check if entity is a Seer
            actor.compute_fov()  # compute actor's FOV
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_close_door(action, register_call, actor, door):
    """ Actor closing door action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed / 4    # close door is a 1/4 speed action for now
    else:  # part that is executed when action fires
        actor.close(door)  # close the door
        if isinstance(actor, game_logic.Seer):  # check if entity is a Seer
            actor.compute_fov()  # compute actor's FOV
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_drop_item(action, register_call, actor, item):
    """ Actor drop item action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed / 10    # drop action is 1/10 speed
    else:  # part that is executed when action fires
        actor.drop_item(item)  # drop item
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_pick_up_item(action, register_call, actor, item):
    """ Actor pick up item action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed / 4  # pick up action is 1/4 speed
    else:  # part that is executed when action fires
        actor.add_item(item)  # pick up item
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_use_item(action, register_call, actor, item):
    """ Actor use item action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed / 4  # use action is 1/4 speed (for now)
    else:  # part that is executed when action fires
        actor.use_item(item)  # use item
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_equip_item(action, register_call, actor, item, slot):
    """ Actor equip item action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed  # equip is full turn action (for now)
    else:  # part that is executed when action fires
        actor.equip_item(item, slot)  # equip item
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state


def act_unequip_item(action, register_call, actor, item):
    """ Actor unequip item action """
    if register_call:  # part executed when function is registered in ActionMgr
        action.t_needed = actor.speed / 2  # equip is half turn action (for now)
    else:  # part that is executed when action fires
        actor.unequip_item(item)  # unequip item
        actor.actions.remove(action)  # remove performed action from actor's list
        actor.state = 'ready'  # return actor to ready state

"""
    This file contains game events.
"""
import weakref


class Observer:
    """ Observer mixin, completely copy-pasted from SO :( """
    # TODO: test if weakref.WeakSet is needed
    _observers = set()

    def __init__(self):
        self._observers.update({self})
        self._observables = {}

    def observe(self, event_name, callback):
        self._observables[event_name] = callback

    def close(self):
        self._observers.discard(self)
        self._observables.clear()


class Event:
    """ Event class, used to fire events """
    def __init__(self, name, data, autofire=True):
        self.name = name
        self.data = data
        if autofire:
            self.fire()

    def fire(self):
        for observer in Observer._observers:
            if self.name in observer._observables:
                observer._observables[self.name](self.data)

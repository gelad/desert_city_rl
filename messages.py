""" This module contains all game text strings, that need translation, or other manipulations """
import gettext
import os
import sys
import locale
import configparser


def lang_init():
    """
    Initialize a translation framework (gettext).
    Typical use::
        _ = lang_init()

    :return: A string translation function.
    :rtype: (str) -> str
    """
    _locale = None
    try:
        config = configparser.ConfigParser()
        config.read('dc_rl.ini')
        if 'DesertCity' in config:
            if 'locale' in config['DesertCity']:
                _locale = config['DesertCity']['locale']
    except FileNotFoundError:
        print('INI file not found, sticking to system language')
    if not _locale:
        _locale, _encoding = locale.getdefaultlocale()  # Default system values
    path = sys.argv[0]
    path = os.path.join(os.path.dirname(path), 'lang')
    lang = gettext.translation('dc_rl', path, [_locale])
    return lang.gettext


_ = lang_init()


class _Msg:
    """ A class that contains all game messages """
    def __init__(self):
        pass


MSG = _Msg()


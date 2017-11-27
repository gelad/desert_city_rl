""" This module contains all game text strings, that need translation, or other manipulations """
import gettext
import os
import sys
import locale
import configparser


class MyFallback(gettext.NullTranslations):
    def gettext(self, msg):
        print('Translation not found for: {msg}'.format(msg=msg))
        return msg


class MyTranslations(gettext.GNUTranslations, object):
    def __init__(self, *args, **kwargs):
        super(MyTranslations, self).__init__(*args, **kwargs)
        if self.info()['language'] != 'en_US':  # if it's english - no fallback, default strings are fine
            self.add_fallback(MyFallback())


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
    try:
        lang = gettext.translation(domain='dc_rl', localedir=path, languages=[_locale], class_=MyTranslations)
    except FileNotFoundError:
        print('No {l} locale found, switching to en_US.'.format(l=_locale))
        lang = gettext.translation(domain='dc_rl', localedir=path, languages=['en_US'], class_=MyTranslations)
    return lang.gettext


_ = lang_init()


class _Msg:
    """ A class that contains all game messages """
    def __init__(self):
        pass

    @staticmethod
    def m(msg):
        """ Just simple string search in translations """
        return _(msg)


Msg = _Msg()


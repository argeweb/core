#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2014/9/30
import os
import logging
import inspect
from . import events
from .model import HostInformationModel, WebSettingModel
from google.appengine.api import namespace_manager
from google.appengine.api import memcache

_defaults = {}
_host_information = {}
prefixes = ['admin', 'cron', 'console', 'dashboard', 'taskqueue']


class ConfigurationError(Exception):
    pass


def load_settings(app_settings=None, refresh=False):
    """
    Executed when the project is created and loads the settings from application/settings.py
    """
    global _defaults

    if _defaults and not refresh:
        return
    if app_settings is None:
        try:
            from application import settings as app_settings
            reload(app_settings)
            app_defaults = app_settings.settings
            logging.debug('Static settings loaded from application.settings.py')
        except:
            try:
                from argeweb import base_settings as app_settings
                reload(app_settings)
                app_defaults = app_settings.settings
                logging.debug('Static settings loaded from argeweb.base_settings.py')
            except AttributeError:
                raise ConfigurationError("No dictionary 'settings' found in settings.py")
    else:
        app_defaults = app_settings
    defaults(app_defaults)


def defaults(dict=None):
    """
    Adds a set of default values to the settings registry. These can and will be updated
    by any settings modules in effect, such as the Settings Manager.

    If dict is None, it'll return the current defaults.
    """
    if dict:
        _defaults.update(dict)
    else:
        return _defaults


def settings():
    """
    Returns the entire settings registry
    """
    _settings = {}
    events.fire('before_settings', settings=_settings)
    _settings.update(_defaults)
    events.fire('after_settings', settings=_settings)
    return _settings


def print_setting(key):
    return get_from_datastore(key, '')


def get(key, default=None):
    """
    Returns the setting at key, if available, raises an ConfigurationError if default is none, otherwise
    returns the default
    """
    _settings = settings()
    if key in _settings:
        return _settings[key]
    default = os.environ.get(key, default)
    if default is None:
        raise ConfigurationError('Missing setting %s' % key)
    else:
        _defaults.update({key: default})
        return default


def save_to_datastore(setting_key, setting_value, use_memcache=True, prefix=u''):
    _prefix = prefix
    if _prefix is not u'':
        _prefix += '.'
    memcache_key = 'setting.' + _prefix + setting_key
    item = WebSettingModel.get_or_insert(key=setting_key, default=setting_value)
    item.setting_value = setting_value
    item.put()
    if use_memcache:
        memcache.set(key=memcache_key, value=setting_value, time=120)


def get_from_datastore(setting_key, default=None, auto_save=True, use_memcache=True, prefix=u''):
    if default is None:
        default = u''
    _prefix = prefix
    if _prefix is not u'':
        _prefix += '.'
    memcache_key = 'setting.' + _prefix + setting_key
    if use_memcache:
        data = memcache.get(memcache_key)
        if data is not None:
            return data
    if auto_save:
        item = WebSettingModel.get_or_insert(key=setting_key, default=default)
    else:
        item = WebSettingModel.get_by_key(key=setting_key)
    if use_memcache:
        if item is None:
            memcache.add(key=memcache_key, value=default, time=120)
            return default
        else:
            memcache.add(key=memcache_key, value=item.setting_value, time=120)
    return item.setting_value


def get_host_information(key, memcache_key, host=None, host_item=None, timeout=120):
    if host_item is not None:
        return_string = getattr(host_item, key)
        memcache.set(key=memcache_key, value=return_string, time=timeout)
    else:
        return_string = memcache.get(memcache_key)
        if return_string is None and host_item is None:
            host_item = HostInformationModel.get_by_host(host)
            if host_item is not None:
                return_string = getattr(host_item, key)
                memcache.set(key=memcache_key, value=return_string, time=timeout)
    return return_string, host_item


def get_theme(server_name, namespace):
    namespace_manager.set_namespace('shared')
    host_item = HostInformationModel.get_by_host(server_name)
    namespace_manager.set_namespace(namespace)
    return host_item.theme


def set_theme(server_name, namespace, theme):
    namespace_manager.set_namespace('shared')
    host_item = HostInformationModel.get_by_host(server_name)
    host_item.theme = theme
    host_item.put()
    namespace_manager.set_namespace(namespace)


def get_server_name():
    import os
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
        paths = '_'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[1:-1])
        server_name = os.environ['SERVER_NAME'] + '@' + paths.lower()
    else:
        server_name = os.environ['SERVER_NAME']
    return server_name


def get_host_information_item(server_name=None):
    global _host_information
    if server_name is None:
        server_name = get_server_name()
    host_item = get_memcache_in_shared('host.information.' + server_name)
    sn = []
    if host_item is None:
        for n in 'application_user,backend_ui_material,webdav,scaffold,themes,' \
                 'file,user_file,code,plugin_manager,zz_last_path'.split(','):
            sn.append('plugins.%s' % n)
        host_item = HostInformationModel.get_or_insert(
            host=server_name,
            theme='install',
            plugins=','.join(sn),
            is_lock=True
        )
    namespace_manager.set_namespace(host_item.namespace)
    set_memcache_in_shared('host.information.' + server_name, host_item, host_item.namespace)
    return host_item, host_item.namespace, host_item.theme, server_name


def get_memcache_in_shared(memcache_key, current_namespace=None):
    namespace_manager.set_namespace('shared')
    item = memcache.get(memcache_key)
    if current_namespace is not None:
        namespace_manager.set_namespace(current_namespace)
    return item


def set_memcache_in_shared(memcache_key, memcache_value, current_namespace):
    namespace_manager.set_namespace('shared')
    memcache.set(key=memcache_key, value=memcache_value, time=120)
    namespace_manager.set_namespace(current_namespace)



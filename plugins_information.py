#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import argeweb
import os
from caching import cache
from model import HostInformationModel
from google.appengine.api import namespace_manager
from google.appengine.api import memcache

_plugin_installed_list = []
_plugin_enable_list = {}
_plugins_controller = []
_application_controller = []


def get_installed_list():
    return _plugin_installed_list


def exists(name):
    """
    Checks to see if a particular plugin is enabled
    """
    return name in _plugin_installed_list


def register_controller(type_name, new_controllers):
    if type_name == 'plugins':
        global _plugins_controller
        _plugins_controller = new_controllers
    else:
        global _application_controller
        _application_controller = new_controllers


def register_template(template_dir_name, templating=True, type_name='plugins'):
    """
    將 plugin 的樣版目錄加至樣版列表
    """
    check_name = '%s/%s' % (type_name, template_dir_name)
    if check_name in _plugin_installed_list:
        return
    import template
    _plugin_installed_list.append(check_name)

    if templating:
        path = os.path.normpath(os.path.join(
            os.path.dirname(argeweb.__file__),
            '../%s/%s/templates' % (type_name, template_dir_name)))
        template.add_template_path(path)
        template.add_template_path(path, prefix=template_dir_name)


def get_prohibited_controllers(enable_plugins_list):
    """
    取得沒有被啟用的 plugin 與 application 下的 controller
    """
    a = set(get_all_controller_with_type(target_type='application') + get_all_controller_with_type(target_type='plugins'))
    b = []
    for plugin in enable_plugins_list:
        if plugin.find('.') > 0:
            sp = plugin.split('.')
            for item in get_controller_with_type(sp[1], target_type=sp[0]):
                b.append(item)
        else:
            for item in get_controller_with_type(plugin):
                b.append(item)
    return a - set(b)


def get_helper(plugin_name_or_controller, base_type='application'):
    if plugin_name_or_controller is None:
        return None
    if isinstance(plugin_name_or_controller, basestring) is True:
        controller_type = base_type
        plugin_name = plugin_name_or_controller
    else:
        controller_module_name = str(plugin_name_or_controller.__module__)
        try:
            if controller_module_name.startswith('application') or controller_module_name.startswith('plugins'):
                sn = controller_module_name.split('.')
                controller_type = sn[0]
                plugin_name = sn[1]
            else:
                return None
        except:
            return None
    try:
        module = __import__('%s.%s' % (controller_type, plugin_name), fromlist=['*'])
        return getattr(module, 'plugins_helper')
    except AttributeError:
        logging.debug('%s.%s\'s plugin helper not found' % (controller_type, plugin_name))
        return None
    except ImportError:
        logging.debug('%s.%s\'s plugin helper not found' % (controller_type, plugin_name))
        return None


def get_plugin_name_list_with_type(target_type='plugins', use_cache=True):
    """
        取得所有的 controller
        """
    c = get_all_controller_with_type(target_type, use_cache)
    b = [item.split('.')[1] if item.find('.') > 0 else item for item in c]
    c = list(set(b))
    c.sort(key=b.index)
    return c


def get_all_controller(debug, version):
    """
    取得所有的 controller
    """
    temp_controllers = get_all_controller_with_type('application', use_cache=False) + \
                       get_all_controller_with_type('plugins', use_cache=False)
    controllers = temp_controllers
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
        paths = '_'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[1:-1])
        server_name = os.environ['SERVER_NAME'] + '@' + paths.lower()
        host_item = get_enable_plugins_from_db(server_name)
        controllers = []
        for item in temp_controllers:
            n = item.split('.')[:2]
            n = '.'.join(n)
            if host_item is not None and n in host_item or n.startswith('plugins.'):
                controllers.append(item)
    else:
        last_version = memcache.get(key='all.controller.version')
        if version != last_version or last_version is None:
            memcache.set(key='all.controller.version', value=version, time=86400)
            memcache.set(key='all.controller', value=controllers, time=86400)
        else:
            controllers = memcache.get(key='all.controller')
    return controllers

def get_all_controller_with_type(target_type='plugins', use_cache=True):
    if use_cache is True:
        if target_type == 'plugins' and len(_plugins_controller) > 0:
            return _plugins_controller
        if target_type == 'application' and len(_application_controller) > 0:
            return _application_controller
        target_controller_list = memcache.get('%s.all.controller' % target_type)
        if target_controller_list is not None and len(target_controller_list) > 0:
            return target_controller_list

    target_controller_list = []
    dir_plugins = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', target_type))
    for dirPath in os.listdir(dir_plugins):
        if dirPath.find('.') < 0:
            target_controller_list += get_controller_with_type(dirPath, target_type)
    register_controller(target_type, target_controller_list)
    memcache.set(key='%s.all.controller' % target_type, value=target_controller_list, time=60)
    return target_controller_list

def get_controller_with_type(target_name, target_type='plugins'):
    """
        取得特定目錄下所有的 controller
        """
    directory = os.path.join(target_type, target_name, 'controllers')
    controllers_list = []

    for root_path, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.py') and file_name not in ['__init__.py', 'settings.py']:
                controllers_list.append(target_type + '.' + target_name + '.controllers.' + file_name.replace('.py', ''))
    if len(controllers_list) > 0:
        return controllers_list
    else:
        return [target_type + '.' + target_name + '.controllers.' + target_name]


def get_enable_plugins_from_db(server_name, namespace=None):
    """
        取得 HostInformation 裡的 Plugins ( 取得已啟用的 Plugin )
        """
    if namespace is None:
        namespace = namespace_manager.get_namespace()
    if str(namespace) in _plugin_enable_list:
        return _plugin_enable_list[str(namespace)]
    namespace_manager.set_namespace('shared')
    host_item = HostInformationModel.get_by_host(server_name)
    namespace_manager.set_namespace(namespace)
    enable_plugins = str(host_item.plugins).split(',')
    _plugin_enable_list[str(namespace)] = enable_plugins
    return enable_plugins


def set_enable_plugins_to_db(server_name, namespace, plugins):
    """
    設定 HostInformation 裡的 Plugins ( 設定啟用的 Plugin )
    """
    namespace_manager.set_namespace('shared')
    host_item = HostInformationModel.get_by_host(server_name)
    host_item.plugins = ','.join(plugins)
    host_item.put()
    _plugin_enable_list[str(namespace)] = plugins
    namespace_manager.set_namespace(namespace)
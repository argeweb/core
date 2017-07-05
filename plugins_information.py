#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import argeweb
import os
from caching import cache
from model import HostInformationModel
from settings import update_host_information_in_memcache
from google.appengine.api import namespace_manager
from google.appengine.api import memcache

_plugin_installed_list = []
_plugins_controller = []
_application_controller = []


def get_installed_list():
    return _plugin_installed_list


def exists(name):
    """
    Checks to see if a particular plugin is enabled
    """
    return name in _plugin_installed_list


def register_controller(controller_name, target_list):
    if controller_name in target_list:
        return
    target_list.append(controller_name)


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


def get_prohibited_controllers(server_name, namespace):
    """
    取得沒有被啟用的 plugin
    """
    a = set(get_all_controller_with_type())
    b = []
    for plugin in get_enable_plugins_from_db(server_name, namespace):
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


def get_all_plugin(use_cache=True):
    """
    取得所有的 controller
    """
    c = get_all_controller_with_type(use_cache)
    b = [item.split('.')[1] if item.find('.') > 0 else item for item in c]
    c = list(set(b))
    c.sort(key=b.index)
    return c


def get_all_controller(debug, version):
    """
        取得所有的 controller
        """
    if debug is True:
        return get_all_controller_with_type(False, 'application') + get_all_controller_with_type()
    last_version = memcache.get(key='all.controller.version')
    if last_version is None:
        return get_all_controller_with_type(False, 'application') + get_all_controller_with_type()
    if version != last_version:
        controllers = get_all_controller_with_type(False, 'application') + get_all_controller_with_type()
        memcache.set(key='all.controller.version', value=version, time=86400)
        memcache.set(key='all.controller', value=controllers, time=86400)
    else:
        controllers = memcache.get(key='all.controller')
    return controllers

#
# def get_controller_in_application(application_name, target_type='plugins'):
#     """
#     取得 application 目錄下特定 app 裡的所有 controller
#     """
#     directory = os.path.join('application', application_name, 'controllers')
#     dir_path_list = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'application'))
#     application_controllers = []
#     for dirPath in os.listdir(dir_path_list):
#         if dirPath.find('.') < 0:
#             application_controllers += get_controller_in_application(dirPath)
#
#     for root_path, _, files in os.walk(directory):
#         for file_name in files:
#             if file_name.endswith('.py') and file_name not in ['__init__.py', 'settings.py']:
#                 application_controllers.append('application.' + application_name + '.controllers.' + file_name.replace('.py', ''))
#     register_controller(application_name, _plugins_controller)
#     if len(application_controllers) > 0:
#         return application_controllers
#     else:
#         return ['application.' + application_name + '.controllers.' + application_name]

#
# def get_all_controller_in_application():
#     """
#     取得 Application 目錄下所有的 controller
#     """
#     application_controller = []
#     base_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
#     has_controllers_dir = True
#     directory = os.path.join('application', 'controllers')
#     if os.path.exists(directory) is False:
#         has_controllers_dir = False
#         directory = os.path.join('application')
#     directory = os.path.join(base_directory, directory)
#     if not os.path.exists(directory):
#         return
#     for root_path, _, files in os.walk(directory):
#         for file_name in files:
#             if file_name.endswith('.py') == False or file_name in ['__init__.py', 'settings.py']:
#                 continue
#             controller_name = file_name.split('.')[0]
#             register_controller(controller_name, _application_controller)
#             if has_controllers_dir:
#                 application_controller.append('application.controllers.%s' % controller_name)
#     return application_controller
#
#
# def get_controller_in_plugin(plugin_name):
#     """
#     取得特定 plugin 目錄下所有的 controller
#     """
#     directory = os.path.join('plugins', plugin_name, 'controllers')
#     dir_path_list = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'plugins'))
#     application_controllers = []
#     for dirPath in os.listdir(dir_path_list):
#         if dirPath.find('.') < 0:
#             application_controllers += get_controller_in_plugin(dirPath)
#
#     for root_path, _, files in os.walk(directory):
#         for file_name in files:
#             if file_name.endswith('.py') and file_name not in ['__init__.py', 'settings.py']:
#                 application_controllers.append('plugins.'+plugin_name+'.controllers.'+file_name.replace('.py', ''))
#     register_controller(plugin_name, _plugins_controller)
#     if len(application_controllers) > 0:
#         return application_controllers
#     else:
#         return ['plugins.'+plugin_name+'.controllers.'+plugin_name]
#
#
# def get_all_controller_in_plugins(use_cache=True):
#     """
#     取得 plugins 下所有的 controller
#     """
#     if use_cache is True:
#         plugins_controllers = memcache.get('plugins.all.controller')
#         if plugins_controllers is not None and len(plugins_controllers) > 0:
#             return plugins_controllers
#     plugins_controllers = []
#     dir_plugins = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'plugins'))
#     for dirPath in os.listdir(dir_plugins):
#         if dirPath.find('.') < 0:
#             plugins_controllers += get_controller_in_plugin(dirPath)
#     memcache.set(key='plugins.all.controller', value=plugins_controllers, time=60)
#     return plugins_controllers


def get_all_controller_with_type(use_cache=False, target_type='plugins'):
    if use_cache is True:
        target_controller_list = memcache.get('%s.all.controller' % target_type)
        if target_controller_list is not None and len(target_controller_list) > 0:
            return target_controller_list

    target_controller_list = []
    dir_plugins = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', target_type))
    for dirPath in os.listdir(dir_plugins):
        if dirPath.find('.') < 0:
            target_controller_list += get_controller_with_type(dirPath, target_type)
    memcache.set(key='%s.all.controller' % target_type, value=target_controller_list, time=60)
    return target_controller_list
    
    
def get_controller_with_type(target_name, target_type='plugins'):
    """
    取得特定目錄下所有的 controller
    """
    directory = os.path.join(target_type, target_name, 'controllers')
    dir_path_list = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', target_type))
    controllers_list = []
    # for dirPath in os.listdir(dir_path_list):
    #     if dirPath.find('.') < 0:
    #         controllers_list += get_controller_with_type(dirPath, target_type)

    for root_path, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.py') and file_name not in ['__init__.py', 'settings.py']:
                controllers_list.append(target_type + '.' + target_name + '.controllers.' + file_name.replace('.py', ''))
    if target_type == 'plugins':
        register_controller(target_name, _plugins_controller)
    else:
        register_controller(target_name, _application_controller)
    if len(controllers_list) > 0:
        return controllers_list
    else:
        return [target_type + '.' + target_name + '.controllers.' + target_name]


def get_enable_plugins_from_db(server_name, namespace):
    """
        取得 HostInformation 裡的 Plugins ( 取得已啟用的 Plugin )
        """
    namespace_manager.set_namespace('shared')
    host_item = HostInformationModel.get_by_host(server_name)
    namespace_manager.set_namespace(namespace)
    return str(host_item.plugins).split(',')


def set_enable_plugins_to_db(server_name, namespace, plugins):
    """
        設定 HostInformation 裡的 Plugins ( 設定啟用的 Plugin )
        """
    namespace_manager.set_namespace('shared')
    host_item = HostInformationModel.get_by_host(server_name)
    host_item.plugins = ','.join(plugins)
    host_item.put()
    update_host_information_in_memcache(server_name, host_item)
    namespace_manager.set_namespace(namespace)
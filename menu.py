#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .settings import prefixes
_temporary_menu_storage = []


def route_menu(*args, **kwargs):
    def inner(f):
        if 'uri' not in kwargs:
            f_model_path = f.__module__.split('.')
            ctrl = f.__module__.split('.')[-1]
            if f_model_path[0] == 'application':
                a = 5
            plugin = f_model_path[0] in ['application', 'plugins'] and f_model_path[1] or ''
            prefix = 'prefix' in kwargs and kwargs['prefix'] or ''
            action = 'action' in kwargs and kwargs['action'] or f.__name__

            for possible_prefix in prefixes:
                if action.startswith(possible_prefix):
                    prefix = possible_prefix
                    break
            uri_array = []
            if prefix != '':
                action = action.replace(prefix + '_', '')
                uri_array.append(prefix)
            if plugin is not '':
                uri_array.append(plugin)
            uri_array.append(ctrl)
            uri_array.append(action)
            kwargs['uri'] = ':'.join(uri_array)
            kwargs['plugin'] = plugin
            kwargs['controller'] = str(f.__module__)
            kwargs['action'] = action
        _temporary_menu_storage.append(kwargs)
        return f
    return inner


def pass_menu(menu, list_name, controller):
    action_name = '%s.%s' % (menu['controller'], menu['action'])
    return menu['list_name'] != list_name \
        or menu['controller'] in controller.prohibited_controllers \
        or controller.application_user.has_permission(action_name) is False


def get_route_menu(list_name=u'', controller=None):
    menus = []
    if _temporary_menu_storage is None:
        return []

    for menu in _temporary_menu_storage:
        if pass_menu(menu, list_name, controller):
            continue
        uri = menu['uri']
        try:
            url = controller.uri(uri)
        except (KeyError, ValueError):
            continue
        if 'parameter' in menu:
            url += '?' + menu['parameter']

        if (u'%s' % menu['text']).startswith(u'gt:'):
            text = u'gt'
            group_title = (u'%s' % menu['text']).replace(u'gt:', '')
        else:
            text = menu['text']
            group_title = u''
        insert_item = {
            'level': 1,
            'uri': uri,
            'url': url,
            'text': text,
            'group_title': group_title,
            'icon': menu['icon'] if 'icon' in menu else 'list',
            'target': menu['target'] if 'target' in menu else '',
            'sort': float(menu['sort']) if 'sort' in menu else 1.0,
            'need_hr': menu['need_hr'] if 'need_hr' in menu else False,
            'need_hr_parent': menu['need_hr_parent'] if 'need_hr_parent' in menu else False
        }
        if 'group' in menu:
            sub_item = insert_item.copy()
            sub_item['level'] = 2
            insert_item['text'] = menu['group']
            if list_name == u'backend':
                insert_item['url'] = "#"
            is_find = None
            for j in menus:
                if j['text'] == menu['group'] and j['level'] == 1:
                    is_find = j
            if is_find:
                if 'submenu' in is_find:
                    if sub_item['need_hr_parent']:
                        is_find['need_hr_parent'] = True
                    if is_find['sort'] > sub_item['sort']:
                        is_find['sort'] = sub_item['sort']
                    is_find['submenu'].append(sub_item)
                    is_find['submenu'] = sorted(is_find['submenu'], key=lambda k: k['sort'])
                else:
                    is_find['submenu'] = [sub_item]
            else:
                insert_item['submenu'] = [sub_item]
                menus.append(insert_item)
        else:
            menus.append(insert_item)

    menus = sorted(menus, key=lambda k: k['sort'])
    return menus


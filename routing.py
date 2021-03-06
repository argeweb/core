#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
argeweb' routing utilities
"""

import os
import inspect
import webapp2
import logging
import argeweb
import inflector
from webapp2 import Route
from webapp2_extras import routes


def get_true_name_and_argspec(method):
    """
    Drills through layers of decorators attempting to locate
    the actual argspec for the method.
    """

    argspec = inspect.getargspec(method)
    args = argspec[0]
    if args and args[0] == 'self':
        return method.__name__, argspec
    if hasattr(method, '__func__'):
        method = method.__func__
    if not hasattr(method, 'func_closure') or method.func_closure is None:
        raise Exception('No closure for method.')

    method = method.func_closure[0].cell_contents
    return get_true_name_and_argspec(method)


def add(route, app_router=None):
    """
    Adds a webapp2.Route class to the router
    """
    app_router.add(route)


def auto_route(app_router, version=u''):
    """
    Automatically routes all controllers in main app and plugins
    """
    import controller_helper
    for item in controller_helper.get_all_controller(version):
        try:
            route_controllers(app_router, item)
        except ImportError as e:
            logging.error('Plugin %s does not exist, or contains a bad import: %s' % (item, e))


def redirect(url, to, app_router=None):
    """
    Adds a redirect route with the given url templates.
    """
    add(routes.RedirectRoute(url, redirect_to=to), app_router)


def route_controllers(app_router, controller_path=None):
    """
    Called in app.routes to automatically route all controllers in the app/controllers
    folder
    """
    import controller_helper
    sp = ('%s' % controller_path).split('.')
    type_name = sp[0]
    plugin_name = sp[1]
    controller_name = sp[-1]
    try:
        module = __import__('%s' % controller_path, fromlist=['*'])
        try:
            controller_cls = getattr(module, inflector.camelize(controller_name))
            controller_cls._build_routes(app_router)
            controller_helper.register_template(plugin_name, type_name=type_name)
            controller_helper.register_template(controller_name, type_name=type_name)
        except AttributeError:
            logging.debug('Controller %s not found, skipping' % inflector.camelize(controller_name))
    except ImportError as e:
        logging.error('Thought %s was a controller, but was wrong (or ran into some weird error): %s' % (controller_name, e))
    except AttributeError as e:
        logging.error('Thought %s was a controller, but was wrong (or ran into some weird error): %s' % (controller_name, e))
        raise


def route_name_exists(name, *args, **kwargs):
    """
    Checks if a particlar named route (i.e. 'entries-list') exists.
    """
    route = webapp2.get_app().router.build_routes.get(name)
    return True if route else False


def current_route_name():
    """
    Gets the name (i.e. 'entries-list') from the router.
    """
    name = webapp2.get_app().request.route.name
    return name


def canonical_parts_from_method(controller, method, pass_plugin_name=False):
    """
    Returns the canonical parts (prefix, controller, action, named arguments)
    from a controller's method
    """
    method_name, method_args = get_true_name_and_argspec(method)
    method_class = controller
    method_class_name = inflector.underscore(method_class.__name__)
    prefix = None

    if hasattr(method_class, 'Meta'):
        prefixes = method_class.Meta.prefixes
    else:
        prefixes = method_class.prefixes

    for tprefix in prefixes:
        if method_name.startswith(tprefix + '_'):
            prefix = tprefix
            method_name = method_name.replace(prefix + '_', '')

    plugins_name = str(controller).split('.')[1]
    if pass_plugin_name:
        return {
            'prefix': prefix,
            'controller': method_class_name,
            'action': method_name,
            'args': method_args.args[1:]  # exclude self
        }
    else:
        return {
            'prefix': prefix,
            'controller': method_class_name,
            'plugin': plugins_name,
            'action': method_name,
            'args': method_args.args[1:]  # exclude self
        }


def path_from_canonical_parts(prefix, controller, action, args, plugin=''):
    """
    Returns a route ('/admin/plugin/users/edit/3') from canonical parts
    ('admin', 'users', 'edit', [id])
    """
    args_parts = ['<' + x + '>' for x in args]
    route_parts = [prefix, plugin, controller, action] + args_parts
    route_parts = [x for x in route_parts if x]
    route_path = '/' + '/'.join(route_parts)

    return route_path


def name_from_canonical_parts(prefix, controller, action, args=None, plugin=''):
    """
    Returns the route's name ('admin-users-edit') from the canonical
    parts ('admin','users','edit')
    """
    route_parts = [prefix, plugin, controller, action]
    route_parts = [x for x in route_parts if x]
    route_name = ':'.join(route_parts)

    return route_name


def build_routes_for_controller(controllercls):
    """
    Returns list of routes for a particular controller, to enable
    methods to be routed, add the argeweb.core.controller.auto_route
    decorator, or simply set the 'route' attr of the function to
    True.

    def some_method(self, arg1, arg2, arg3)

    becomes

    /prefix/plugin/controller/some_method/<arg1>/<arg2>/<arg3>
    """
    routes_list = []
    name_counters = {}

    for entry in controllercls._route_list:
        method = entry[0]
        args = entry[1]
        kwargs = entry[2]
        pass_plugin_name = False
        if 'pass_plugin_name' in kwargs:
            pass_plugin_name = kwargs['pass_plugin_name']
            del kwargs['pass_plugin_name']

        parts = canonical_parts_from_method(controllercls, method, pass_plugin_name)
        route_path = path_from_canonical_parts(**parts)
        route_name = name_from_canonical_parts(**parts)


        # not the most elegant way to determine the
        # correct member name, but it works. Alternatively,
        # i could use get_real_name_and_argspect, but
        # cononical_parts_from_method already does that.
        method = parts['action']

        if parts['prefix']:
            method = '%s_%s' % (parts['prefix'], parts['action'])

        name_counters[route_name] = name_counters.get(route_name, 0) + 1
        if name_counters[route_name] > 1:
            route_name = '%s-%d' % (route_name, name_counters[route_name])

        tkwargs = dict(
            template=route_path,
            handler=controllercls,
            name=route_name,
            handler_method=method
        )

        tkwargs.update(kwargs)
        # ingest args[0] if its the only thing set
        if len(args) == 1:
            tkwargs['template'] = args[0]
        if len(args) > 1:
            raise ValueError('Only one positional argument may be passed to route_with')

        routes_list.append(Route(**tkwargs))

    return routes_list


def build_scaffold_routes_for_controller(controllercls, prefix_name=None, plugin_name=None):
    """
    Automatically sets up a restful routing interface for a controller
    that has any of the rest methods (list, view, add, edit, delete)
    either without or with a prefix. Note that these aren't true rest
    routes, some more wizardry has to be done for that.

    The routes generated are:

    controller:list : /plugin_name/controller
    controller:view : /plugin_name/controller/:id
    controller:add  : /plugin_name/controller/add
    controller:edit : /plugin_name/controller/:id/edit
    controller:delete : /plugin_name/controller/:id/delete

    prefixes just add to the beginning of the name and uri, for example:

    admin:controller:edit: /admin/plugin_name/controller/:id/edit
    """
    name = inflector.underscore(controllercls.__name__)
    prefix_string = ''

    if prefix_name:
        prefix_string = prefix_name + '_'

    top_route_list = []
    route_list = []
    record_route_list = []

    # GET /controller -> controller::list
    method_name = prefix_string + 'list'
    if hasattr(controllercls, method_name):
        top_route_list.append(Route('/' + name, controllercls, 'list', handler_method=method_name, methods=['HEAD', 'GET']))

    # GET /controller/:urlsafe -> controller::view
    if hasattr(controllercls, prefix_string + 'view'):
        route_list.append(Route('/:<key>', controllercls, 'view', handler_method=prefix_string + 'view', methods=['HEAD', 'GET']))

    # GET/POST /controller/add -> controller::add
    # POST /controller -> controller::add
    if hasattr(controllercls, prefix_string + 'add'):
        route_list.append(Route('/add', controllercls, 'add', handler_method=prefix_string + 'add', methods=['GET', 'POST']))
        top_route_list.append(Route('/' + name, controllercls, 'add:rest', handler_method=prefix_string + 'add', methods=['POST']))

    # GET/POST /controller/:urlsafe/edit -> controller::edit
    # PUT /controller/:urlsafe -> controller::edit
    if hasattr(controllercls, prefix_string + 'edit'):
        record_route_list.append(Route('/edit', controllercls, 'edit', handler_method=prefix_string + 'edit', methods=['GET', 'POST']))
        route_list.append(Route('/:<key>', controllercls, 'edit:rest', handler_method=prefix_string + 'edit', methods=['PUT', 'POST']))

    # GET /controller/:urlsafe/delete -> controller::delete
    # DELETE /controller/:urlsafe -> controller::d
    if hasattr(controllercls, prefix_string + 'delete'):
        record_route_list.append(Route('/delete', controllercls, 'delete', handler_method=prefix_string + 'delete'))
        route_list.append(Route('/:<key>', controllercls, 'delete:rest', handler_method=prefix_string + 'delete', methods=['DELETE']))

    if hasattr(controllercls, prefix_string + 'sort_up'):
        record_route_list.append(Route('/sort_up', controllercls, 'sort_up', handler_method=prefix_string + 'sort_up'))

    if hasattr(controllercls, prefix_string + 'sort_down'):
        record_route_list.append(Route('/sort_down', controllercls, 'sort_down', handler_method=prefix_string + 'sort_down'))

    if hasattr(controllercls, prefix_string + 'set_boolean_field'):
        record_route_list.append(Route('/set_boolean_field', controllercls, 'set_boolean_field', handler_method=prefix_string + 'set_boolean_field'))

    if hasattr(controllercls, prefix_string + 'plugins_check'):
        record_route_list.append(Route('/plugins_check', controllercls, 'plugins_check', handler_method=prefix_string + 'plugins_check'))

    if plugin_name:
        top_route = routes.NamePrefixRoute(name + ':', top_route_list + [
            routes.PathPrefixRoute('/' + name, route_list + [
                routes.PathPrefixRoute('/:<key>', record_route_list)
            ])
        ])
        top_route_2 = routes.NamePrefixRoute(plugin_name + ':', [
            routes.PathPrefixRoute('/' + plugin_name, [top_route])
        ])
        if prefix_name:
            prefix_route = routes.NamePrefixRoute(prefix_name + ':', [
                routes.PathPrefixRoute('/' + prefix_name, [top_route_2])
            ])
            return prefix_route
        return top_route_2
    else:
        top_route = routes.NamePrefixRoute(name + ':', top_route_list + [
            routes.PathPrefixRoute('/' + name, route_list + [
                routes.PathPrefixRoute('/:<key>', record_route_list)
            ])
        ])
    if prefix_name:
        prefix_route = routes.NamePrefixRoute(prefix_name + ':', [
            routes.PathPrefixRoute('/' + prefix_name, [top_route])
        ])
        return prefix_route
    return top_route

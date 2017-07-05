#!/usr/bin/env python
# -*- coding: utf-8 -*-
import webapp2
import routing
from google.appengine.api import namespace_manager


# Sentinel for the uri methods.
route_sentinel = object()


class Uri(object):
    """
    URI Utility class to help controllers and anything else
    that deals with URIs
    """

    def get_route_name(self,
                       prefix=route_sentinel,
                       controller=route_sentinel,
                       action=route_sentinel):
        """
        Function used to build the route name for a given prefix, controller, and
        action. For example, build_action_route('admin','pages','view', id=2)
        will give you "admin:pages:view". Set prefix to False to exclude the
        current prefix from the route name.
        """
        prefix = prefix if prefix != route_sentinel else self.route.prefix
        controller = controller if controller != route_sentinel else self.route.controller
        action = action if action != route_sentinel else self.route.action
        plugin = ''
        if str(self).find('application.') > 0 or str(self).find('plugins.') > 0:
            plugin = str(self).split('.')[1]
        return routing.name_from_canonical_parts(prefix, controller, action, plugin=plugin)

    def uri(self, route_name=None,
            prefix=route_sentinel,
            controller=route_sentinel,
            action=route_sentinel,
            _pass_all=False,
            *args, **kwargs):
        """
        Generate in-application URIs (or URLs).

        :param route_name: The route name for which to generate a URI for, if not provided then prefix, controller, and action will be used to determine the route name
        :param prefix: The prefix of the desired URI, if omitted then the current prefix is used.
        :param controller: The controller name of the desired URI, if omitted then the current controller is used.
        :param action: The action name of the desired URI, if omitted then the current action is used.
        :param _pass_all: will pass all current URI parameters to the generated URI (useful for pagination, etc.)
        :param _full: generate a full URI, including the hostname.
        :param kwargs: arguments passed at URL or GET parameters.

        Examples::

            uri('foxes:run') # -> /foxes/run
            uri(prefix=False, controller='foxes', action='run')  # -> /foxes/run

            # when currently at /foxes/run
            uri(action='hide') # -> /foxes/hide

        """
        if not route_name:
            route_name = self.get_route_name(prefix, controller, action)

        if _pass_all:
            tkwargs = dict(self.request.route_kwargs)

            targs = tuple(self.request.route_args)
            targs = args + targs

            gargs = dict(self.request.GET)
            tkwargs.update(gargs)
            tkwargs.update(kwargs)
        else:
            tkwargs = kwargs

        tkwargs = {key: value for key, value in tkwargs.items()
                   if value is not None}
        for key, value in tkwargs.items():
            if isinstance(value, unicode):
                tkwargs[key] = value.encode('utf-8')

        return webapp2.uri_for(route_name, *args, **tkwargs)

    def uri_action_link(self, action, item=None, uri=None, *varargs, **kwargs):
        if isinstance(action, basestring):
            if item is None:
                return self.uri(action=action, *varargs, **kwargs)
            else:
                return self.uri(action=action, key=item.key.urlsafe(), *varargs, **kwargs)
        if isinstance(action, dict):
            if 'uri' not in action:
                return ''
            uri = action['uri']
            query_list = []
            if 'query' in action:
                for q in action['query']:
                    n = self.process_query_with_item(q, item)
                    if n is not None:
                        query_list.append(n)
                kwargs['query'] = u'&'.join(query_list)
            else:
                if item is not None:
                    kwargs['source'] = item.key.urlsafe()
            return self.uri(uri, *varargs, **kwargs)

    @staticmethod
    def process_query_with_item(q, item):
        name = q['name']
        value = q['value']
        if value.startswith(':'):
            if value == ':key':
                value = item.key.urlsafe()
        return u'%s=%s' % (name, value)

    def uri_exists(self, route_name=None,
                   prefix=route_sentinel,
                   controller=route_sentinel,
                   action=route_sentinel,
                   *args, **kwargs):
        """
        Check if a route exists.
        """
        if not route_name:
            route_name = self.get_route_name(prefix, controller, action)

        return routing.route_name_exists(route_name), route_name

    def uri_exists_with_permission(self, route_name=None, item=None, *args, **kwargs):
        if 'namespace' in kwargs:
            namespace_manager.set_namespace(kwargs['namespace'])

        returnVal = False
        try:
            if 'item' in kwargs:
                item = kwargs['item']
            if item is None:
                self.uri(route_name, *args, **kwargs)
            else:
                self.uri(route_name, key=self.util.encode_key(item), *args, **kwargs)
            returnVal = True
        except:
            pass
        uri_sn = str(self.uri).split("<")[2].split(' ')[0].lower().split('.')
        if 'controller' in kwargs:
            uri_s = '.'.join(uri_sn[:-2]) + '.' + kwargs['controller']
        else:
            uri_s = '.'.join(uri_sn[:-1])
        if 'action' in kwargs:
            uri_s = uri_s + '.' + kwargs['action']
        if returnVal and self.application_user.has_permission(uri_s):
            return True
        else:
            return False

    def on_uri(self, route_name=None,
               prefix=route_sentinel,
               controller=route_sentinel,
               action=route_sentinel,
               **kwargs):
        """
        Checks to see if we're currently on the specified route.
        """
        if not route_name:
            route_name = self.get_route_name(prefix, controller, action)
        if route_name == routing.current_route_name():
            route_matches = True
        else:
            route_matches = False

        if not kwargs or not route_matches:
            return route_matches

        for name, value in kwargs.items():
            if not self.request.params.get(name, None) == value and not self.request.route_kwargs.get(name, None) == value:
                return False

        return True

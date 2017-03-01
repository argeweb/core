#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import time
import template
import json_util
from protorpc import protojson
from protorpc.message_types import VoidMessage
from events import ViewEvents

_views = {}
_function_list = {}
_datastore_commands = {}


def factory(name):
    """
    Creates a view instance by name
    """
    global _views
    return _views.get(name.lower(), _views.get((name + 'View').lower()))


class ViewFunction(object):
    _controller = None

    def __init__(self, controller):
        self._controller = controller

    @staticmethod
    def register(function_object=None, prefix=u'global'):
        name = prefix + ':' + function_object.__name__
        if name in _function_list:
            return
        _function_list[name] = function_object

    def get_run(self):
        def run(common_name, *args, **kwargs):
            prefix = u'global'
            if kwargs.has_key('prefix'):
                prefix = kwargs['prefix']
            name = prefix + ':' + common_name
            kwargs['controller'] = self._controller
            if name in _function_list:
                r = _function_list[name](*args, **kwargs)
                return r
        return run


class ViewDatastore(object):
    _controller = None

    def __init__(self, controller):
        self._controller = controller

    @staticmethod
    def register(name, common_object=None, prefix=u'global'):
        name = prefix + ':' + name
        if name in _datastore_commands:
            return
        _datastore_commands[name] = common_object

    def get(self, *args, **kwargs):
        query_name = None
        if len(args) > 0:
            query_name = str(args[0])
            args = args[1:]
            if len(args) + len(kwargs) == 0 and query_name:
                args = [query_name]
        if 'query_name' in kwargs:
            query_name = str(kwargs['query_name'])
        prefix = u'global'
        if kwargs.has_key('prefix'):
            prefix = kwargs['prefix']
            del kwargs['prefix']
        query_name = prefix + ':' + query_name
        if query_name and query_name in _datastore_commands:
            rv = _datastore_commands[query_name](*args, **kwargs)
            try:
                return rv.get()
            except:
                return rv

    def query(self, query_name, *args, **kwargs):
        prefix = u'global'
        if kwargs.has_key('prefix'):
            prefix = kwargs['prefix']
        query_name = prefix + ':' + query_name
        if query_name in _datastore_commands:
            query = _datastore_commands[query_name](*args, **kwargs)
            use_pager = False
            if 'use_pager' in kwargs:
                use_pager = kwargs['use_pager']
            if 'size' not in kwargs:
                kwargs['size'] = 10
            if 'page' not in kwargs:
                kwargs['page'] = 1
            if 'near' not in kwargs:
                kwargs['near'] = 10
            if 'data_only' not in kwargs:
                kwargs['data_only'] = not use_pager
            kwargs['size'] = self._controller.params.get_integer('size', kwargs['size'])
            kwargs['page'] = self._controller.params.get_integer('page', kwargs['page'])
            kwargs['near'] = self._controller.params.get_integer('near', kwargs['near'])
            return self.paging(query, kwargs['size'], kwargs['page'], kwargs['near'], kwargs['data_only'])

    def paging(self, query, size=None, page=None, near=None, data_only=None, **kwargs):
        data = query.fetch_async(size, offset=size*(page-1))
        if data_only is True:
            c = data.get_result()
            return c
        near_2 = near // 2
        pager = {
            'prev': 0,
            'next': 0,
            'near_list': [],
            'current': page,
            'data': None
        }
        if page > 1:
            pager['prev'] = page - 1
        if page > near_2:
            start = page - near_2
            end = page + near_2
        else:
            start = 1
            end = near
        has_next = False
        all_pages = end - start + 1
        all_pages = all_pages <= 0 and 1 or all_pages
        q = query.fetch_async(size * all_pages, offset=size*(start-1), keys_only=True)
        q_result_len = len(q.get_result())
        if q_result_len > size:
            has_next = True
        for i in xrange(0, all_pages):
            if q_result_len > i * size:
                pager['near_list'].append(start + i)
            else:
                break
        pager['data'] = data.get_result()
        if has_next:
            pager['next'] = page + 1
        return pager

    def random(self, cls_name, common_name, size=3, *args, **kwargs):
        import random
        return_lst = []
        cls_name = cls_name + ':' + common_name
        if cls_name not in _datastore_commands:
            return return_lst
        query = _datastore_commands[cls_name](*args, **kwargs)
        lst = query.fetch(size * 10)
        if len(lst) >= size:
            return_lst = random.sample(lst, size)
        else:
            return_lst = lst
        return return_lst


class ViewContext(dict):
    def get_dotted(self, name, default=None):
        data = self
        path = name.split('.')
        for chunk in path[:-1]:
            data = data.setdefault(chunk, {})
        return data.setdefault(path[-1], default)

    def set_dotted(self, name, value):
        path = name.split('.')
        container = self.get_dotted('.'.join(path[:-1]), {})
        container[path[-1]] = value

    def set(self, **kwargs):
        self.update(**kwargs)


class View(object):
    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            global _views
            cls = type.__new__(meta, name, bases, dict)
            if name != 'View':
                _views[name.lower()] = cls
            return cls

    def __init__(self, controller, context=None):
        self.controller = controller
        self.auto_render = True

        if not context:
            context = ViewContext()
        if isinstance(context, dict) and not isinstance(context, ViewContext):
            context = ViewContext(**context)
        self.context = context

        self.events = ViewEvents(prefix='view')

    def render(self, *args, **kwargs):
        raise NotImplementedError("Base view can't render anything")


class TemplateView(View):

    def __init__(self, controller, context=None):
        super(TemplateView, self).__init__(controller, context)
        self.template_name = None
        self.template_ext = 'html'
        self.cache = True
        self.theme = controller.theme
        self.setup_template_variables()

    def setup_template_variables(self):
        self.context.get_dotted('this', {}).update({
            'uri': self.controller.uri,
            'uri_exists': self.controller.uri_exists_with_permission,
            'on_uri': self.controller.on_uri,
            'encode_key': self.controller.util.encode_key,
            'decode_key': self.controller.util.decode_key,
        })

        self.context.update({
            'controller_name': self.controller.name,
            'events': self.events,
            'uri': self.controller.uri,
            'uri_exists': self.controller.uri_exists,
            'uri_action_link': self.controller.uri_action_link,
            'uri_exists_with_permission': self.controller.uri_exists_with_permission,
            'user': self.controller.application_user,
            'on_uri': self.controller.on_uri,
            'request': self.controller.request,
            'route': self.controller.route,
            'params': self.controller.params,
            'namespace': self.controller.namespace,
            'print_key': self.controller.util.encode_key,
            'print_setting': self.controller.settings.print_setting,
            'datastore': ViewDatastore(self.controller),
            'function': ViewFunction(self.controller).get_run()
        })
        r = self.controller.route
        self.controller.events.setup_template_variables(controller=self.controller)

    def render(self, *args, **kwargs):
        self.controller.events.before_render(controller=self.controller)
        self.context.update({'theme': self.theme})
        result = template.render_template(self.get_template_names(), self.context, theme=self.theme)
        self.controller.response.content_type = 'text/html'
        self.controller.response.charset = 'utf-8'
        self.controller.response.unicode_body = result
        self.controller.events.after_render(controller=self.controller, result=result)
        return self.controller.response

    def get_template_names(self):
        """
        Generates a list of template names.

        The template engine will try each template in the list until it finds one.

        For non-prefixed actions, the return value is simply: ``[ "[controller]/[action].[ext]" ]``.
        For prefixed actions, another entry is added to the list : ``[ "[controller]/[prefix_][action].[ext]" ]``. This means that actions that are prefixed can fallback to using the non-prefixed template.

        For example, the action ``Posts.json_list`` would try these templates::

            posts/json_list.html
            posts/list.html

        """
        if self.template_name:
            if self.cache:
                return self.template_name
            else:
                # 使用隨機字串可以避開 Jinja2 樣版系統的快取
                random_string = str(random.random())
                return_list = []
                for item in self.template_name:
                    if str(item).startswith('assets:'):
                        return_list.append(item + "?random_string=" + random_string)
                    else:
                        return_list.append(item)
                return return_list
        if self.cache:
            random_string = ''
        else:
            # 使用隨機字串可以避開 Jinja2 樣版系統的快取
            random_string = "?random_string=" + str(random.random())
        templates = []

        template_path = '%s/' % self.controller.name
        action_name = '%s.%s' % (self.controller.route.action, self.template_ext)

        templates.append('%s%s' % (template_path, action_name))

        if self.controller.route.prefix:
            templates.insert(0, '%s%s_%s' % (template_path, self.controller.route.prefix, action_name))

        if self.controller.name == 'home':
            if self.controller.route.prefix:
                templates.insert(0, '%s_%s' % ( self.controller.route.prefix, action_name))
            else:
                templates.insert(0, action_name)
        path = self.controller.request.path
        if path != '' and path != '/' and hasattr(self.controller, 'scaffold') is False:
            if path.startswith('/'):
                path = path[1:]
            if path.endswith(self.template_ext):
                templates.append(path)
            else:
                templates.append('%s.%s' % (path, self.template_ext))
        templates_new = []
        for i in templates:
            lower = i.lower()
            if not i in templates_new:
                templates_new.append(i+random_string)
            if not lower in templates_new:
                templates_new.append(lower+random_string)
        self.controller.events.template_names(controller=self.controller, templates=templates_new)
        return templates_new


class JsonView(View):
    def __init__(self, controller, context=None):
        super(JsonView, self).__init__(controller, context)
        self.variable_name = ('data',)

    def _get_data(self, default=None):
        self.variable_name = self.variable_name if isinstance(self.variable_name, (list, tuple)) else (self.variable_name,)

        if hasattr(self.controller, 'scaffold') and self.controller.scaffold is not None:
            self.variable_name += (self.controller.scaffold.singular, self.controller.scaffold.plural)
        for v in self.variable_name:
            if v in self.context:
                return self.context.get(v)
        return default

    def render(self, *args, **kwargs):
        self.controller.events.before_render(controller=self.controller)
        self.controller.response.charset = 'utf-8'
        self.controller.response.content_type = 'application/json'
        data = self._get_data()
        if 'message' in self.controller.context:
            data['message'] = self.controller.context['message']
        result = unicode(json_util.stringify(data))

        if hasattr(self.controller, 'scaffold') and hasattr(self.controller.scaffold, 'scaffold_type'):
            request_method = str(self.controller.request.route.handler_method)
            result_data = {}
            if request_method.startswith('admin_'):
                scaffold_data = {
                    'response_info': 'success',
                    'request_method': request_method,
                    'method_default_message': self.controller.meta.default_message if hasattr(self, 'default_message') else None,
                    'method_data_key': None,
                    'method_record_edit_url': None
                }
                if data is not None:
                    try:
                        scaffold_data['method_data_key'] = self.controller.util.encode_key(data)
                        scaffold_data['method_record_edit_url'] = self.controller.uri(action='edit',
                                                                                 key=scaffold_data['method_data_key'])
                    except:
                        pass
                    result_data['data'] = data
                result_data['scaffold'] = scaffold_data
            result_data['message'] = self.controller.context['message'] if 'message' in self.controller.context else 'undefined'
            result = unicode(json_util.stringify(result_data))
        self.controller.response.unicode_body = result
        self.controller.events.after_render(controller=self.controller, result=result)
        return self.controller.response


class JsonpView(JsonView):
    def render(self, *args, **kwargs):
        self.controller.events.before_render(controller=self.controller)
        self.controller.response.charset = 'utf-8'
        self.controller.response.content_type = 'application/json'
        self.controller.response.headers.setdefault('Access-Control-Allow-Origin', '*')
        callback = 'callback'
        if 'callback' in self.controller.request.params:
            callback = self.controller.request.get('callback')
        result = unicode(json_util.stringify(self._get_data()))
        self.controller.response.unicode_body = u'%s(%s)' % (callback, result)
        self.controller.logging.debug(result)
        self.controller.events.after_render(controller=self.controller, result=result)
        return self.controller.response


class MessageView(JsonView):
    def render(self, *args, **kwargs):
        self.controller.events.before_render(controller=self.controller)
        self.controller.response.charset = 'utf-8'
        self.controller.response.content_type = 'application/json'
        data = self._get_data(default=VoidMessage())
        result = unicode(protojson.encode_message(data))
        self.controller.response.unicode_body = result
        self.controller.events.after_render(controller=self.controller, result=result)
        return self.controller.response


class RenderView(TemplateView):
    def render(self, *args, **kwargs):
        self.controller.events.before_render(controller=self.controller)
        self.controller.response.charset = 'utf-8'
        result = template.render_template(self.get_template_names(), self.context, theme=self.theme)
        self.controller.response.unicode_body = result
        self.controller.events.after_render(controller=self.controller, result=result)
        return self.controller.response

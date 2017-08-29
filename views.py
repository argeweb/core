#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
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


class DataGetObject(object):
    def __init__(self, data_or_query):
        if hasattr(data_or_query, 'get_async'):
            self._query = data_or_query.get_async()
            self._data = None
        else:
            self._query = None
            self._data = data_or_query

    @property
    def data(self):
        if self._data is None and self._query:
            self._data = self._query.get_result()
        return self._data


    def __getitem__(self, item):
        return item

    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, attr):
        return getattr(self.data, attr)

    # def __iter__(self):
    #     lst = self.data
    #     if isinstance(lst, dict):
    #         return iter(lst)
    #     return []

    def __len__(self):
        if self.data is not None:
            return 1
        return 0


class DataQueryObject(object):
    def __init__(self, query, page, size, near, data_only=False):
        self._data = None
        self._query_paging = None
        self._near_list = []

        near_2 = near // 2
        if page > 1:
            self._prev_page = page - 1
        if page > near_2:
            self._start_page = page - near_2
            self._end_page = page + near_2
        else:
            self._start_page = 1
            self._end_page = near
        self._all_pages = self._end_page - self._start_page + 1
        self._all_pages = self._all_pages <= 0 and 1 or self._all_pages
        self._size = size
        self._current = page
        if hasattr(query, 'fetch_async'):
            self._query = query.fetch_async(size, offset=size*(page-1))
        else:
            self._query = query.fetch_async(size, offset=size * (page - 1))
        self._query_object = query
        self._data_paging = None
        self._pager_not_ready = True
        if data_only is False:
            self.pager()

    def __iter__(self):
        lst = self.data
        if isinstance(lst, list):
            return iter(lst)
        return []

    def __len__(self):
        lst = self.data
        if isinstance(lst, list):
            return len(lst)
        return 0

    @property
    def current(self):
        return self._current

    @property
    def list(self):
        return self.data

    @property
    def data(self):
        if self._data is None:
            self._data = self._query.get_result()
        if self._data is None:
            self._data = []
        return self._data

    def get(self, index=0):
        lst = self.data
        if isinstance(lst, list):
            if len(lst) == index:
                return lst[index]
        return None

    def random(self, size):
        lst = self.data
        return_lst = []
        if isinstance(lst, list):
            if len(lst) >= size:
                return_lst = random.sample(lst, size)
            else:
                return_lst = lst
        return return_lst

    def pager(self):
        self._pager_not_ready = False
        self._query_paging = self._query_object.fetch_async(
            self._size * self._all_pages, offset=self._size * (self._start_page - 1), keys_only=True)

    @property
    def pager_data(self):
        if self._data_paging is None:
            if self._pager_not_ready:
                self.pager()
            self._data_paging = self._query_paging.get_result()
        if self._data_paging is None:
            self._data_paging = []
        return self._data_paging

    @property
    def near_list(self):
        self._near_list = []
        result_len = len(self.pager_data)
        for i in xrange(0, self._all_pages):
            if result_len > i * self._size:
                self._near_list.append(self._start_page + i)
            else:
                break
        return self._near_list

    @property
    def next_page(self):
        result_len = len(self.pager_data)
        if result_len > self._size:
            return self._current + 1
        return None

    @property
    def prev_page(self):
        if self._current > 1:
            return self._current - 1
        return None


class ViewFunction(object):
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
            if 'prefix' in kwargs:
                prefix = kwargs['prefix']
            name = prefix + ':' + common_name
            kwargs['controller'] = self._controller
            if name in _function_list:
                r = _function_list[name](*args, **kwargs)
                return r
        return run


class ViewFunctionProxy:
    def __init__(self, name, controller):
        self.name = name
        self._controller = controller

    def run(self, *args, **kwargs):
        kwargs['controller'] = self._controller
        prefix = u'global'
        if 'prefix' in kwargs:
            prefix = kwargs['prefix']
        name = prefix + ':' + self.name
        if name in _function_list:
            return _function_list[name](*args, **kwargs)


class ViewDatastore(object):
    _controller = None

    def __init__(self, controller):
        self._controller = controller

    @staticmethod
    def register(name, common_object=None, prefix=u'global'):
        if isinstance(prefix, basestring):
            name = prefix + ':' + name
        else:
            name = prefix.__module__ + ':' + name
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
        if 'prefix' in kwargs:
            prefix = kwargs['prefix']
            del kwargs['prefix']
        query_name = prefix + ':' + query_name
        if query_name and query_name in _datastore_commands:
            common_object = _datastore_commands[query_name]
            query = common_object(*args, **kwargs)
            return DataGetObject(query)

    def query(self, query_name, *args, **kwargs):
        prefix = u'global'
        if 'prefix' in kwargs:
            prefix = kwargs['prefix']
            del kwargs['prefix']
        use_pager = False
        if 'use_pager' in kwargs:
            use_pager = kwargs['use_pager']
            del kwargs['use_pager']
        data_only = not use_pager
        if 'data_only' in kwargs:
            data_only = kwargs['data_only']
            del kwargs['data_only']
        query_name = prefix + ':' + query_name
        if query_name in _datastore_commands:
            common_object = _datastore_commands[query_name]
            query = common_object(*args, **kwargs)
            target_module = common_object.im_self
            common_object.im_self._kind_map[target_module.__name__] = target_module

            if 'size' not in kwargs:
                kwargs['size'] = self._controller.params.get_integer('size', 10)
            if 'page' not in kwargs:
                kwargs['page'] = self._controller.params.get_integer('page', 1)
            if 'near' not in kwargs:
                kwargs['near'] = self._controller.params.get_integer('near', 10)
            return DataQueryObject(query=query, page=kwargs['page'], size=kwargs['size'],
                                   near=kwargs['near'], data_only=data_only)

    def search(self, *args, **kwargs):
        for name in ['use_pager', 'data_only', 'prefix']:
            if name in kwargs:
                del kwargs[name]
        return self._controller.components.search(*args, **kwargs)


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
            'uri_permission': self.controller.uri_exists_with_permission,
            'on_uri': self.controller.on_uri,
            'encode_key': self.controller.util.encode_key,
            'decode_key': self.controller.util.decode_key,
        })
        view_datastore = ViewDatastore(self.controller)

        self.context.update({
            'plugin_name': str(self.controller).startswith('<plugins') and str(self.controller).split('.')[1] or '',
            'controller_name': self.controller.name,
            'events': self.events,
            'uri': self.controller.uri,
            'uri_exists': self.controller.uri_exists,
            'uri_action_link': self.controller.uri_action_link,
            'uri_permission': self.controller.uri_exists_with_permission,
            'user': self.controller.application_user,
            'on_uri': self.controller.on_uri,
            'request': self.controller.request,
            'route': self.controller.route,
            'params': self.controller.params,
            'get_session': self.controller.get_session,
            'set_session': self.controller.set_session,
            'namespace': self.controller.namespace,
            'print_key': self.controller.util.encode_key,
            'print_setting': self.controller.settings.print_setting,
            'datastore': view_datastore,
            'query': view_datastore.query,
            'get': view_datastore.get,
            'function': ViewFunction(self.controller).get_run(),
            'has_plugin': self.controller.plugins.exists,
            'plugins': self.controller.plugins.get_installed_list,
        })
        for key in _function_list.keys():
            if key.startswith("global"):
                name = key.split(":")[1]
                self.context.update({name: ViewFunctionProxy(name, self.controller).run})
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

    def set_template_names_from_path(self, path):
        # 依照傳入的檔案路徑取得樣版名稱
        if path.startswith('/') is False and path.endswith('.html') is False:
            path = '/%s.html' % path
        path_ds = 'assets:/themes/%s%s' % (self.theme, path)
        config = self.controller.host_information

        # 樣版系統的快取
        self.cache = config.view_cache
        path_app = '/application/%s/templates%s' % (self.theme, path)
        path_theme = '/themes/%s%s' % (self.theme, path)
        if config.use_real_template_first:
            # 先從 實體檔案 讀取樣版, 再從 Datastore 讀取樣版
            if config.use_application_template_first:
                self.template_name = [path_app, path_theme, path_ds]
            else:
                self.template_name = [path_theme, path_app, path_ds]
        else:
            # 先從 Datastore 讀取樣版, 再從 實體檔案 讀取樣版
            if config.use_application_template_first:
                self.template_name = [path_ds, path_app, path_theme]
            else:
                self.template_name = [path_ds, path_theme, path_app]

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
        if data is None:
            data = {}
        if 'message' in self.controller.context:
            data['message'] = self.controller.context['message']
        result = unicode(json_util.stringify(data))

        if hasattr(self.controller, 'scaffold') and hasattr(self.controller.scaffold, 'scaffold_type'):
            request_method = str(self.controller.request.route.handler_method)
            result_data = {}
            if request_method.startswith('admin_'):
                scaffold_data = {
                    'response_result': 'success',
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
            result_data['message'] = self.controller.context['message'] if 'message' in self.controller.context else ''
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

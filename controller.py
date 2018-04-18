#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, os
import weakref
import webapp2
import logging
import base64

from jinja2 import TemplatesNotFound
from google.appengine.api import namespace_manager
from webapp2 import cached_property
from webapp2_extras import sessions
from argeweb.core import controller_helper
from argeweb.core import inflector, response_handlers, request_parsers, events
from argeweb.core import views
from argeweb.core import routing
from argeweb.core import scaffold, auth
from argeweb.core import settings
from argeweb.core import time_util
from argeweb.core import params
from argeweb.core import mysql
from argeweb.core.uri import Uri
from argeweb.core.bunch import Bunch
from argeweb.core.ndb import encode_key, decode_key
from argeweb.core.menu import get_route_menu
from argeweb.core.json_util import parse as json_parse, stringify as json_stringify
from argeweb.components.csrf import CSRF
from argeweb.components.search import Search
from argeweb.components.pagination import Pagination

_temporary_route_storage = []
_temporary_menu_storage = []


def route(f):
    """
    Marks a method for automatically routing and accessible via HTTP.
    See :mod:`~argeweb.core.routing` for more details on how methods are auto-routed.
    This decorator should always be the outermost decorator.

    For example::

        @route
        def exterminate(self):
            return 'EXTERMINAAATE!'
    """
    global _temporary_route_storage
    _temporary_route_storage.append((f, (), {}))
    return f


def route_with(*args, **kwargs):
    """
    Marks a class method to be routed similar to :func:`route` and passes and additional arguments to the webapp2.Route
    constructor.

    :param template: Sets the URL template for this action


    For example::

        @route_with(template='"posts/archive/<year>")
        def archive_by_year(self, year):
            pass
    """
    def inner(f):
        _temporary_route_storage.append((f, args, kwargs))
        return f
    return inner


def add_authorizations(*args):
    """
    Adds additional authorization chains to a particular action. These are executed after the
    chains set in Controller.Meta.
    """
    def inner(f):
        if hasattr(f, 'authorizations'):
            authorizations = getattr(f, 'authorizations')
            setattr(f, 'authorizations', authorizations + args)
        else:
            setattr(f, 'authorizations', args)
        return f
    return inner


def require_post_method(controller):
    """
    Only support post method
    """
    if controller.request.method != 'POST':
        return controller.abort(404)
    return True


def require_post(f):
    """
    Shortcut decorator to easily add the method_post check to an action
    """
    return add_authorizations(require_post_method)(f)


def require_user(f):
    """
    Shortcut decorator to easily add the method_post check to an action
    """
    return add_authorizations(auth.require_user)(f)


class Controller(webapp2.RequestHandler, Uri):
    """
    Controllers allows grouping of common actions and provides them with
    automatic routing, reusable components, request data parsering, and
    view rendering.
    """

    _controllers = []

    class __metaclass__(type):
        def __new__(meta, name, bases, dict):
            global _temporary_route_storage

            cls = type.__new__(meta, name, bases, dict)
            if name != 'Controller':
                # Add to the controller registry
                if not cls in Controller._controllers:
                    Controller._controllers.append(cls)

                # Make sure the metaclass as a proper inheritence chain
                if not issubclass(cls.Meta, Controller.Meta):
                    cls.Meta = type('Meta', (cls.Meta, Controller.Meta), {})
                else:
                    cls.Meta = type('Meta', (cls.Meta, ), {})

                cls._route_list = _temporary_route_storage
                _temporary_route_storage = []

            return cls

    # The name of this class, lowercase (automatically determined)
    name = 'controller'

    #: View Context, all these variables will be passed to the view.
    context = property(lambda self: self.meta.view.context)

    class Meta(object):
        """
        The Meta class stores configuration information for a Controller. This class is constructed
        into an instance and made available at ``self.meta``. This class is optional, Controllers that
        do not specify it will receive the default configuration. Additionally, you need not inherit from
        this class as Controller's metaclass will ensure it.

        For example::

            def Posts(Controller):
                class Meta:  # no inheritance
                    prefixes = ('admin', )
                    #  all other properties inherited from default.
        """

        #: List of components.
        #: When declaring a controller, this must be a list or tuple of classes.
        #: When the controller is constructed, ``controller.components`` will
        #: be populated with instances of these classes.
        # components = (scaffold.Scaffolding,)
        components = (scaffold.Scaffolding, Pagination, Search, CSRF)

        #: Prefixes are added in from of controller (like admin_list) and will cause routing
        #: to produce a url such as '/admin/plugin/name/list' and a name such as 'admin:plugin:name:list'
        prefixes = settings.prefixes

        #: Authorizations control access to the controller. Each authorization is a callable.
        #: Authorizations are called in order and all must return True for the request to be
        #: processed. If they return False or a tuple like (False, 'message'), the request will
        #: be rejected.
        #: You should **always** have ``auth.require_admin_for_prefix(prefix=('admin',))`` in your
        #: authorization chain.
        authorizations = (auth.require_admin_for_prefix(prefix=('admin',)), auth.check_user)
        #: Which :class:`~argeweb.core.views.View` class to use by default. use :meth:`change_view` to switch views.
        default_view = None
        View = views.TemplateView

        #: Which :class:`RequestParser` class to use by default. See :meth:`Controller.parse_request`.
        Parser = 'Form'

        def __init__(self, controller):
            self._controller = controller
            self.view = None
            self.change_view(self.View)

        def change_view(self, view, persist_context=True):
            """
            Swaps the view, and by default keeps context between the two views.

            :param view: View class or name.
            """
            context = self.view.context if self.view else None
            self.View = view if not isinstance(view, basestring) else views.factory(view)
            self.view = self.View(self._controller, context)

    class Util(object):
        """
        Provides some basic utility functions. This class is constructed into an instance
        and made available at ``controller.util``.
        """

        def __init__(self, controller):
            self._controller = controller

        #: Decodes a urlsafe ``ndb.Key``.
        decode_key = staticmethod(decode_key)

        #: Encode an ``ndb.Key`` (or ``ndb.Model`` instance) into an urlsafe string.
        encode_key = staticmethod(encode_key)

        #: Decodes a json string.
        parse_json = staticmethod(json_parse)

        #: Encodes a json string.
        stringify_json = staticmethod(json_stringify)

        encode_base64 = staticmethod(base64.urlsafe_b64encode)
        decode_base64 = staticmethod(base64.urlsafe_b64decode)

        underscore = staticmethod(inflector.underscore)
        count_minute = staticmethod(time_util.count_minute)

        @classmethod
        def localize_time(cls, datetime=None, strftime='%Y/%m/%d %H:%M:%S'):
            return time_util.localize(datetime).strftime(strftime)

        def get_menu(self, list_name):
            return get_route_menu(list_name, self._controller)

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.name = inflector.underscore(self.__class__.__name__)
        self.settings = settings
        self.host_information, self.namespace, self.theme, self.server_name = self.settings.get_host_information_item()
        self.proper_name = self.__class__.__name__
        self.util = self.Util(weakref.proxy(self))
        self.logging = logging
        self.plugins = controller_helper
        self.params = params.ParamInfo(weakref.proxy(self))
        self.sql = mysql.CloudSQL(weakref.proxy(self))
        self.session_store = sessions.get_store(request=self.request)

        self.route = None
        self.scaffold = None
        self.application_user = None
        self.prohibited_actions = []
        self.prohibited_controllers = []
        namespace_manager.set_namespace(self.namespace)

    def fire(self, event_name, *args, **kwargs):
        kwargs['controller'] = self
        result_list = events.fire(event_name, *args, **kwargs)
        if len(result_list) == 0:
            return None
        if len(result_list) == 1:
            return result_list[0]
        return result_list

    def _build_components(self):
        self.events.before_build_components(controller=self)
        if hasattr(self.Meta, 'components'):
            component_classes = self.Meta.components
            self.components = Bunch()
            for cls in component_classes:
                if hasattr(cls, 'name'):
                    name = cls.name
                else:
                    name = inflector.underscore(cls.__name__)
                self.components[name] = cls(weakref.proxy(self))
        else:
            if hasattr(self.Meta, 'Model'):
                self.components = (scaffold.Scaffolding, )
            else:
                self.components = Bunch()
        self.events.after_build_components(controller=self)

    def _init_route(self):
        action = self.request.route.handler_method
        prefix = None
        for possible_prefix in self.Meta.prefixes:
            if action.startswith(possible_prefix):
                prefix = possible_prefix
                action = action.replace(prefix + '_', '')
                break

        self.route = Bunch(
            prefix=prefix,
            controller=self.name,
            action=action,
            name=self.request.route.name,
            args=self.request.route_args,
            kwargs=self.request.route_kwargs)

    def _init_meta(self):
        self._init_route()

        self.events = events.NamedBroadcastEvents(prefix='controller_')
        self.meta = self.Meta(weakref.proxy(self))
        self._build_components()

    @classmethod
    def _build_routes(cls, router):
        """
        Called in the main app router to get all of this controller's routes.
        Override to add custom/additional routes.
        """

        # Route the rest methods
        # if str(cls).find('plugins.') > 0:
        plugins_name = str(cls).split('.')[1]
        p1 = routing.build_scaffold_routes_for_controller(cls, plugin_name=plugins_name)
        router.add(p1)
        for prefix in cls.Meta.prefixes:
            p2 = routing.build_scaffold_routes_for_controller(cls, prefix, plugin_name=plugins_name)
            router.add(p2)
        # else:
        #     router.add(routing.build_scaffold_routes_for_controller(cls))
        #     for prefix in cls.Meta.prefixes:
        #         router.add(routing.build_scaffold_routes_for_controller(cls, prefix))

        # Auto route the remaining methods
        for route in routing.build_routes_for_controller(cls):
            vars = re.findall(r'\[(\w+)\]', route.template)
            if vars:
                action = route.handler_method
                split = action.split('_')
                prefixed = split[0] in cls.Meta.prefixes
                controller_data = {
                    'prefix': split[0] if prefixed else None,
                    'controller': inflector.underscore(cls.__name__),
                    'action': '_'.join(split[1:]) if prefixed else action,
                }

                for i in vars:
                    value = controller_data.get(i)
                    if not value:
                        continue
                    route.template = route.template.replace('['+i+']', value)
            router.add(route)
        events.fire('controller_build_routes', cls=cls, router=router)

    def _startup(self):
        """
        Called when a new request is received and before authorization and dispatching.
        This is the main point in which to listen for events or change dynamic configuration.
        """
        self.startup()
        if self.theme == u'install' and self.request.path == '/':
            return self.redirect('/admin/setup')

        if hasattr(self.Meta, 'default_view') and self.Meta.default_view is not None:
            if isinstance(self.Meta.default_view, basestring):
                self.meta.change_view(self.Meta.default_view)
        self.prohibited_controllers = self.plugins.get_prohibited_controllers(self.host_information.plugins_list)
        name = '.'.join(str(self).split(' object')[0][1:].split('.')[0:-1])
        user_agent = ''
        if 'User-Agent' in self.request.headers:
            user_agent = self.request.headers['User-Agent']
        if 'HTTP_X_APPENGINE_TASKETA' not in self.request.headers.environ and user_agent.find('CloudPubSub-Google') < 0:
            if name in self.prohibited_controllers and name.startswith('plugins.') and name.find('.controller.'):
                # 組件被停用
                self.logging.debug(u'%s is disable' % self.name)
                return self.abort(404)
            if name in self.prohibited_actions:
                # 權限不足
                self.logging.debug(u'%s in %s' % (self.name, self.prohibited_actions))
                return self.abort(404)

    def startup(self):
        pass

    def _is_authorized(self):
        authorizations = self.meta.authorizations

        #per-handler authorizations
        method = getattr(self, self.request.route.handler_method)
        if hasattr(method, 'authorizations'):
            authorizations = authorizations + method.authorizations

        authorizations = list(authorizations)  # convert to list so listeners can modify

        self.events.before_authorization(controller=self, authorizations=authorizations)

        auth_result = True

        for chain in authorizations:
            auth_result = chain(self)
            if auth_result is not True:
                break

        if isinstance(auth_result, webapp2.Response):
            pass

        elif auth_result is not True:
            message = u'Authorization chain rejected request'
            if isinstance(auth_result, tuple):
                message = auth_result[1]

            self.events.authorization_failed(controller=self, message=message)
            for item in self.settings.get('authorization_redirect'):
                if item['authorization'] == message:
                    return self.redirect("/auth_redirect?to=" + item['redirect'])
            self.abort(403, message)

        self.events.after_authorization(controller=self, result=auth_result)

        return auth_result

    def redirect_uri(self, uri_name, params):
        import urllib
        params_string = u''
        for k, v in params.items():
            params_string += u'&%s=%s'% (k, urllib.quote(v.encode('utf8')))
        try:
            url = u"%s?%s" % (self.uri(uri_name), params_string)
        except:
            url = u"%s?%s" % (uri_name, params_string)
        return self.redirect(url)

    def error_and_abort(self, code, *args, **kwargs):
        self.error(code)
        return self.abort(code, args, kwargs)

    def _clear_redirect(self):
        if self.response.status_int in [300, 301, 302]:
            self.response.status = 200
            del self.response.headers['Location']

    def dispatch(self):
        """
        Calls startup, checks authorization, and then the controller method.

        If a view is set and auto rendering is enabled, then it will try to automatically
        render the view if the action doesn't return anything.

        If the controller method returns anything other than None, auto-rendering is skipped
        and the result is transformed into a response using the :mod:`~argeweb.core.response_handlers`.
        """

        # Setup everything, the session, etc.
        self._init_meta()

        self.context.set_dotted('this.session', self.session)

        self.events.before_startup(controller=self)
        self._startup()
        self.events.after_startup(controller=self)

        # Authorization
        res = self._is_authorized()
        if isinstance(res, webapp2.Response):
            return res

        # Dispatch to the method
        self.events.before_dispatch(controller=self)
        result = super(Controller, self).dispatch()
        self.events.after_dispatch(response=result, controller=self)

        # Return value handlers.
        # Response has highest precendence, the view class has lowest
        if 'application/json' in self.request.headers.get('Accept', []) \
                or self.request.headers.get('Content-Type') == 'application/json':
            self.meta.change_view('json')

        response_handler = response_handlers.factory(type(result))
        if response_handler:
            self.response = response_handler(self, result)

        # View rendering works similar to the string mode above.
        elif self.meta.view.auto_render:
            self._clear_redirect()
            try:
                self.response = self.meta.view.render()
            except TemplatesNotFound as e:
                self.abort(404, str(e))
        else:
            self.abort(500, 'Nothing was able to handle the response %s (%s)' % (result, type(result)))
        self.events.dispatch_complete(controller=self)

        self.session_store.save_sessions(self.response)
        self.events.clear()
        return self.response

    @cached_property
    def session(self):
        """
        Sessions are a simple dictionary of data that's persisted across requests for particular
        browser session.

        Sessions are backed by an encrypted cookie and datastore.
        """
        return self.session_store.get_session(backend='datastore')

    def get_session(self, key):
        if key in self.session:
            return self.session[key]
        return None

    def set_session(self, key, value):
        self.session[key] = value
        return ''

    def parse_request(self, container=None, fallback=None, parser=None):
        """
        Parses request data (like GET, POST, JSON, XML) into a container (like a Form or Message)
        instance using a :class:`~argeweb.core.request_parsers.RequestParser`. By default, it assumes
        you want to process GET/POST data into a Form instance, for that simple case you can use::

            data = self.parse_request()

        provided you've set the Form attribute of the Meta class.
        """
        parser_name = parser if parser else self.meta.Parser
        parser = request_parsers.factory(parser_name)

        if not container:
            container_name = parser.container_name
            if not hasattr(self.meta, container_name):
                raise AttributeError('Meta has no %s class, can not parse request' % container_name)
            container = getattr(self.meta, container_name)

        # 欄位資料介入
        if hasattr(self.meta, 'Model'):
            for property in self.meta.Model._properties:
                if hasattr(fallback, property):
                    field = getattr(self.meta.Model, property)
                    if field is not None and hasattr(field, 'process'):
                        field.process(self, fallback)
        return parser.process(self.request, container, fallback)

    @staticmethod
    def get_file_name(file):
        import os
        dri_path = os.path.join(file)
        l = dri_path.split(os.path.sep)[-1].split('.')[0]
        return l

    def json(self, data, code=200):
        self.meta.change_view('json')
        self.context['data'] = data
        try:
            if 'code' in data:
                self.response.status = data['code']
                return
        except TypeError:
            pass
        self.response.status = code

    def json_success_message(self, message, code=200):
        self.meta.change_view('json')
        self.success_message(message)
        self.response.status = code

    def json_failure_message(self, message, code=200):
        self.meta.change_view('json')
        self.failure_message(message)
        self.response.status = code

    def success_message(self, message):
        self.context['message'] = message
        self.context['data'] = {'result': 'success'}
        self.response.data = {'result': 'success', 'message': message}

    def failure_message(self, message):
        self.context['message'] = message
        self.context['data'] = {'result': 'failure'}
        self.response.data = {'result': 'failure', 'message': message}

    def abort(self, code, detail=None, *args, **kwargs):
        if detail is not None:
            self.failure_message(detail)
        if 'json' in kwargs:
            self.response.data = kwargs['json']
        super(Controller, self).abort(code, *args, **kwargs)

    admin_list = scaffold.list
    admin_view = scaffold.view
    admin_add = scaffold.add
    admin_edit = scaffold.edit
    admin_delete = scaffold.delete
    admin_sort_up = scaffold.sort_up
    admin_sort_down = scaffold.sort_down
    admin_set_boolean_field = scaffold.set_boolean_field
    admin_plugins_check = scaffold.plugins_check
    before_scaffold = scaffold.before_scaffold
    after_scaffold = scaffold.after_scaffold

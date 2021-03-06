"""
argeweb' templating engine.
"""

from google.appengine.api import users, app_identity
from google.appengine.ext import db, ndb
from routing import route_name_exists, current_route_name
from jinja2.exceptions import TemplateNotFound
from json_util import DatastoreEncoder
from settings import settings
import logging
import os
import math
import datetime
import json
import jinja2
import types
import collections
import argeweb
import events
import time
import time_util
import random

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')


class TemplateEngine(object):
    def __init__(self, theme=None, extra_globals=None, extra_paths=None):
        self.theme = theme
        jinja2_env_kwargs = {
            'loader': self._build_loader(extra_paths=extra_paths),
            'auto_reload': False,
            # 'cache_size':  0 if debug else 50,
            'cache_size':  0,
            'variable_start_string': "{{ ",
            'variable_end_string': " }}",
            'extensions': ['jinja2.ext.do']
        }
        events.fire('before_jinja2_environment_creation', engine=self, jinja2_env_kwargs=jinja2_env_kwargs)
        self.environment = jinja2.Environment(**jinja2_env_kwargs)
        events.fire('after_jinja2_environment_creation', engine=self)
        self._update_globals(extra_globals)
        events.fire('template_engine_created', self)

    def _build_loader(self, extra_paths=None):
        # Paths for resolving template file locations
        non_prefix_template_paths = [
            os.path.normpath(os.path.join(os.path.dirname(argeweb.__file__), '../application/templates')),
            os.path.normpath(os.path.join(os.path.dirname(argeweb.__file__), './templates')),
            os.path.normpath(os.path.join(os.path.dirname(argeweb.__file__), '../'))
        ]
        prefix_paths = {
            'app': os.path.join(os.path.dirname(argeweb.__file__), '../application/templates'),
            'framework': os.path.join(os.path.dirname(argeweb.__file__), './templates')
        }

        # Extra (plugin) paths
        if extra_paths:
            for x in extra_paths:
                if not x[1]:  # non prefixed
                    non_prefix_template_paths += x[0]

            prefix_paths.update({
                x[1]: x[0] for x in extra_paths if x[1]
            })

        # Theme Paths
        if self.theme:
            non_prefix_template_paths = [
                os.path.normpath(os.path.join(x, './themes/%s/' % self.theme))
                for x in non_prefix_template_paths
            ] + non_prefix_template_paths

        class ChoiceLoader(jinja2.ChoiceLoader):
            def get_source(self, environment, template):
                is_assets = template.startswith(u'assets:')
                for loader_item in self.loaders:
                    # loader_name = str(loader)
                    # if is_assets and loader_name.find('FunctionLoader') < 0:
                    #     continue
                    # if is_assets is True and loader_name.find('FunctionLoader') > 0:
                    #     continue
                    is_function_loader = str(loader_item).find('FunctionLoader') > 0
                    if is_assets and is_function_loader is False:
                        continue
                    if is_assets is False and is_function_loader:
                        continue
                    try:
                        return loader_item.get_source(environment, template)
                    except TemplateNotFound:
                        pass
                raise TemplateNotFound(template)

        def assets_loader(template):
            if template.startswith(u'assets:') is False:
                return None
            template = template.replace(u'assets:', u'')
            template = template.split('?')[0]
            if template.startswith(u'/') is True:
                template = template[1:]
            try:
                from plugins.code.models.code_model import get_source
                from plugins.file.models.file_model import get_file
                t = get_file(template)
                if t is None:
                    raise TemplateNotFound(template)
                s = get_source(target=t, version=t.last_version)
                if s is None:
                    raise TemplateNotFound(template)
                self.environment.globals.update({
                    'code_version': t.last_version,
                })
                return s.source
            except:
                raise TemplateNotFound(template)

        loader = ChoiceLoader([
            jinja2.FunctionLoader(assets_loader),
            jinja2.FileSystemLoader(non_prefix_template_paths),
            jinja2.PrefixLoader({
                k: jinja2.FileSystemLoader(v)
                for k, v in prefix_paths.iteritems()})
        ])
        return loader

    def render(self, name, context=None):
        template = self.find(name)
        context = context if context else {}

        context.update({'template': {
            'name': template.name,
            'list': name,
            'theme': self.theme
        }})

        events.fire('before_template_render', name=name, context=context, env=self.environment)
        result = template.render(context, context=context)
        events.fire('after_template_render', result=result, name=name, context=context, env=self.environment)
        return result

    def find(self, name):
        return self.environment.get_or_select_template(name)

    def themed(self, name, theme=None):
        """
        Returns a template from a particular theme, or the default.
        """
        if theme:
            # Hilariously this works because our search paths always include the 'base',
            # so by just repeating what we do in determine paths, we can find a themed
            # version
            themed_name = '/themes/%s/%s' % (theme, name)
            try:
                return self.find(themed_name)
            except jinja2.TemplateNotFound:
                logging.debug('Template %s not found for theme %s' % (themed_name, theme))
                pass
        return self.find(name)

    def _update_globals(self, extra_globals=None):
        """
        Sets up all of the appropriate global variales for the templating system
        """
        self.environment.globals.update({
            'print_value': format_value,
            'print_value_with_lang': format_value_with_lang,
            'print_text': pure_text,
            'print_datetime': format_datetime_without_localize,
            'isinstance': isinstance,
            'math': math,
            'int': format_int,
            'float': format_float,
            'round': round,
            'list': list,
            'str': str,
            'len': len,
            'random': random,
            'getattr': getattr,
            'setattr': setattr,
            'unicode': unicode,
            'datetime': datetime,
            'time': time,
            'localize': time_util.localize,
            'framework': {
                'route_name_exists': route_name_exists,
                'current_route_name': current_route_name,
                'is_current_user_admin': users.is_current_user_admin,
                'users': users,
                'settings': settings(),
                'version': argeweb.version,
                'app_version': os.environ['CURRENT_VERSION_ID'],
                'hostname': app_identity.get_default_version_hostname(),
                'themed': self.themed.__get__(self),
            },
            'json': _json_filter,
            'inflector': argeweb.inflector,
            'dir': dir,
            'ndb': ndb,
            'db': db,
        })
        self.environment.filters['json'] = _json_filter
        self.environment.tests['datetime'] = _is_datetime

        if extra_globals:
            self.environment.globals.update(extra_globals)


engines = {}

# This should not normally be used, global variables should not be dynamic,
# they can only be safely set when the app is first spun up before any
# templates are rendered. You should generally hook into a handler's
# before render callback.
global_context = {}

# Extra search paths, use add_template_path function for this.
extra_paths = []


def render_template(name, context=None, theme=None):
    """
    Renders the template given by name with the given context (variables).
    Uses the global context.
    """
    if context is None:
        context = {}
    # TODO preload assets file
    return _get_engine(theme=theme).render(name, context)


def add_template_path(path_or_paths, prefix=None):
    """
    Used to add search paths to the template engine. Can only be called during application
    startup before any templates are rendered
    """
    global extra_paths
    if not isinstance(path_or_paths, list):
        path_or_paths = [path_or_paths]

    extra_paths.append((path_or_paths, prefix))


def _get_engine(theme=None):
    global engines
    global global_context
    global extra_paths

    if not theme in engines:
        engines[theme] = TemplateEngine(theme=theme, extra_globals=global_context, extra_paths=extra_paths)
    return engines[theme]

#
#   Filters
#


def _json_filter(obj, *args, **kwargs):
    """
    A filter to automatically encode a variable as json
    e.g. {{user|json}} renders {'email': 'something@something.com'}
    """
    return json.dumps(obj, *args, cls=DatastoreEncoder, **kwargs)


def _is_datetime(obj):
    return isinstance(obj, datetime.datetime)


#
# Formatters
#
import datetime as cdt


def format_datetime(x, format=None):
    if format is None:
        return time_util.localize(x).strftime('%Y-%m-%d %H:%M:%S')
    return time_util.localize(x).strftime(format)


def format_datetime_without_localize(x, format=None):
    if format is None:
        return x.strftime('%Y-%m-%d %H:%M:%S')
    return x.strftime(format)


def format_date(x, format=None):
    if format is None:
        return x.strftime('%Y-%m-%d')
    return x.strftime(format)


def format_key(x, format=None):
    i = x.get()
    if i is None:
        return '---'
    try:
        if format is not None and hasattr(i, format):
            return format_value(getattr(i, format))
        elif hasattr(i, 'title'):
            return format_value(i.title)
    except:
        pass
    return format_value(i)

formatters = {
    datetime.datetime: format_datetime,
    #datetime.datetime: lambda x: x.strftime('%b %d, %Y at %I:%M%p %Z'),
    datetime.date: format_date,
    ndb.Key: format_key
}


def pure_text(text, length=50, more=u'...'):
    import re
    tag_re = re.compile(r'<[^>]+>')
    s = tag_re.sub(u'', text)
    if len(s) > length:
        return s[:length] + more
    else:
        return s

def format_int(val):
    try:
        return int(val)
    except:
        return 0

def format_float(val):
    try:
        return float(val)
    except:
        return 0.0


def format_value(val, format=None):
    if isinstance(val, types.StringTypes):
        return val

    if isinstance(val, collections.Iterable):
        return u', '.join([format_value(x) for x in val])

    formatter = formatters.get(type(val))

    if formatter:
        try:
            return formatter(val, format)
        except:
            return formatter(val)

    return unicode(val)


def format_value_with_lang(item, field_name, lang=None):
    if field_name is None or lang is None:
        return ''
    lang_field = '%s_lang_%s' % (field_name, lang)
    if hasattr(item, lang_field):
        return format_value(getattr(item, lang_field))
    else:
        return ''

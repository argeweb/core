#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2016/1/28.
import re

from argeweb.core.ndb import decode_key
from datetime import datetime


class ParamInfo(object):
    def __init__(self, controller):
        """ easy way to get param from request

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        self.request = controller.request

    def string_is_empty(self, key=''):
        key = key.strip()
        if key is None or key is '' or key is u'':
            return True
        else:
            return False

    def has(self, key):
        return key in self.request.params

    def get_ndb_record(self, key='', default_value=None):
        """ get from request and try to parse to a int

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        if key is '':
            target = default_value
        else:
            if key in self.request.params:
                target = self.request.get(key)
            else:
                target = key
        try:
            if target is not None:
                return decode_key(target).get()
        except:
            return None

    def get_integer(self, key='', default_value=0):
        """ get from request and try to parse to a int

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                return default_value
            _a = self.request.get(key) if int(self.request.get(key)) is not None else u''
            return default_value if _a == '' else int(_a)
        except:
            return default_value

    def get_float(self, key='', default_value=0.0):
        """ get from request and try to parse to a float

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                return default_value
            _a = self.request.get(key) if float(self.request.get(key)) is not None else u''
            if _a == '' or _a == u'':
                _a = default_value
            return default_value if _a == '' else float(_a)
        except:
            return default_value

    def get_string(self, key='', default_value=u''):
        """ get from request and try to parse to a str(unicode)

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                rv = default_value
            else:
                rv = self.request.get(key)
        except:
            rv = default_value
        if rv is None or rv is '' or rv is u'':
            rv = u''
        return rv

    def get_datetime(self, key='', default_value=None):
        str_format = self.get_string(key+'-format', '%Y-%m-%dT%H:%M:%S')
        str_date = self.get_string(key, u'')
        if str_date is u'':
            if default_value is None:
                return datetime.today()
            return default_value
        else:
            try:
                return datetime.strptime(str_date, str_format)
            except (TypeError, ValueError):
                return datetime.strptime(str_date, '%Y-%m-%d')

    def get_email(self, key='', default_value=None):
        email = self.get_string(key).strip()
        if len(email) > 7:
            if re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email) is not None:
                return email
        return default_value

    def get_header(self, key='', default_value=u''):
        """ get from request and try to parse to a str(unicode)

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        from inflector import titleize
        key = '-'.join(titleize(key).split(' '))
        if key is '':
            return default_value
        try:
            if key not in self.request.headers.keys():
                rv = default_value
            else:
                rv = self.request.headers.get(key)
        except:
            rv = default_value
        if rv is None or rv is '' or rv is u'':
            rv = u''
        return rv

    def get_boolean(self, key='', default_value=False):
        """ get from request and try to parse to a bool

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                return default_value
            else:
                v = self.request.get(key)
                if v.lower() == u'false':
                    return False
                if v.lower() == u'0':
                    return False
                return bool(v)
        except:
            return default_value

    def get_list(self, key='', exactly_equal=True, use_dict=False):
        """ get from request and try to parse to a list
        Args:
            key: the key to get from request
            exactly_equal: item must equal key
            use_dict: if True return key value dict object
        """
        return_list = []
        if key is not '':
            for item in self.request.POST.multi._items:
                if exactly_equal:
                    if item[0] == key:
                        if use_dict:
                            return_list.append({'key': str(item[0]), 'value': str(item[1])})
                        else:
                            return_list.append(item[1])
                else:
                    if item[0].find(key) >= 0:
                        if use_dict:
                            return_list.append({'key': str(item[0]), 'value': str(item[1])})
                        else:
                            return_list.append(item[1])
        return return_list

    def get_json(self, key=''):
        try:
            import simplejson as json
        except ImportError:
            import json

        if key is '':
            return {}
        data = self.request.get(key)
        return json.loads(data)

    def get_search(self):
        """ get from request and try to parse to a list

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        search_str = []
        for i in xrange(10):
            if self.request.get('search[%s][type]' % i) == 'text' and self.request.get('search[%s][value]' % i) != '':
                search_str.append({
                    'value': u'' + self.request.get('search[%s][value]' % i).replace(u'\'', u'\'\''),
                    'field': u'' + self.request.get('search[%s][field]' % i),
                    'type': u'' + self.request.get('search[%s][type]' % i),
                    'operator': u'' + self.request.get('search[%s][operator]' % i),
                })
        return search_str

    def get_mobile_number(self, key='', default_value=u'', taiwan_format=True):
        """ get from request and try to parse to a str(unicode)

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                rv = default_value
            else:
                rv = self.request.get(key)
        except:
            rv = default_value
        if rv is '' or rv is u'':
            return None
        else:
            if len(rv) != 10 or rv.startswith('09') is False:
                return None
        if taiwan_format:
            rv = "+886" + rv[1:]
        return rv

    def get_base64(self, key='', default_value=None):
        """ get from request and try to parse to a str(unicode)

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        import base64
        if key is '':
            return default_value
        try:
            if key not in self.request.params:
                rv = default_value
            else:
                rv = self.request.get(key)
        except:
            rv = default_value
        if rv is None or rv is '' or rv is u'':
            return None
        return base64.urlsafe_b64decode(str(rv))


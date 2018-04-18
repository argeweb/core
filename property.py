#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/29.

from google.appengine.ext import ndb
from google.appengine.ext.ndb import Property, utils
from google.appengine.api.datastore_errors import BadValueError


# TODO 驗証屬性設置
# TODO helper 屬性設置

# ArgeWeb Base Property


class StringProperty(ndb.StringProperty):
    _field_group_index = 0
    _tab_page_index = 0
    _choices_text = {}
    @utils.positional(2 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        if 'choices_text' in kwargs:
            self._choices_text = kwargs.pop('choices_text')
        super(StringProperty, self).__init__(*args, **kwargs)


class BooleanProperty(ndb.BooleanProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(BooleanProperty, self).__init__(*args, **kwargs)


class IntegerProperty(ndb.IntegerProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(IntegerProperty, self).__init__(*args, **kwargs)


class FloatProperty(ndb.FloatProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page

        super(FloatProperty, self).__init__(*args, **kwargs)

    def _db_get_value(self, v, unused_p):
        if not v.has_doublevalue():
            return None
        return v.doublevalue()

class DateTimeProperty(ndb.DateTimeProperty):
    _field_group_index = 0
    _tab_page_index = 0
    _set_default = False

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0,*args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(DateTimeProperty, self).__init__(*args, **kwargs)


class DateProperty(ndb.DateProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0,*args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(DateProperty, self).__init__(*args, **kwargs)


class TimeProperty(ndb.TimeProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(TimeProperty, self).__init__(*args, **kwargs)


class BlobKeyProperty(ndb.BlobKeyProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(BlobKeyProperty, self).__init__(*args, **kwargs)


class TextProperty(ndb.TextProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(TextProperty, self).__init__(*args, **kwargs)


class GeoPtProperty(ndb.GeoPtProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(GeoPtProperty, self).__init__(*args, **kwargs)


class JsonProperty(ndb.JsonProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(JsonProperty, self).__init__(*args, **kwargs)


class KeyProperty(ndb.KeyProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(2 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
        super(KeyProperty, self).__init__(*args, **kwargs)


# ArgeWeb Extended Property

class ApplicationUserProperty(KeyProperty):
    """ 使用者欄位"""
    __property_name__ = 'user'
    _attributes = Property._attributes + ['_is_lock']
    _is_lock = False

    @utils.positional(2 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        from model import ApplicationUserModel
        kwargs['kind'] = ApplicationUserModel
        if 'is_lock' in kwargs:
            self._is_lock = kwargs.pop('is_lock')
        super(ApplicationUserProperty, self).__init__(*args, **kwargs)


class RichTextProperty(TextProperty):
    """ 文字編輯器 專用欄位"""
    __property_name__ = 'richtext'


class CodeJSONProperty(TextProperty):
    """ json 專用欄位"""
    __property_name__ = 'jsontext'


class CodeJSProperty(TextProperty):
    """ JavaScript 專用欄位"""
    __property_name__ = 'javascripttext'


class CodeCSSProperty(TextProperty):
    """ CSS 專用欄位"""
    __property_name__ = 'csstext'


class CategoryProperty(KeyProperty):
    """ 分類 專用欄位
        用於綁定於另一個 ndb.Key
        """
    __property_name__ = 'category'
    _dropdown = True

    @utils.positional(2 + Property._positional)
    def __init__(self, *args, **kwargs):
        if 'dropdown' in kwargs:
            self._dropdown = kwargs.pop('dropdown')

        super(CategoryProperty, self).__init__(*args, **kwargs)

    def _fix_up(self, cls, code_name):
        super(CategoryProperty, self)._fix_up(cls, code_name)
        from argeweb.core.ndb.model import Model
        modelclass = Model._kind_map[self._kind]
        collection_name = '%s_ref_%s_to_%s' % (cls.__name__,
                                               code_name,
                                               modelclass.__name__)

        setattr(modelclass, collection_name, (cls,self))


class LinkProperty(StringProperty):
    __property_name__ = 'link'


class FieldSwitchProperty(BooleanProperty):
    """ 欄位切換 專用欄位
        用來決定特定組別的欄位是否顯示

        """
    _group_index_on_enable = 0
    _group_index_on_disable = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, group_index_on_enable=0, group_index_on_disable=0, target='aside_area', *args, **kwargs):
        self._group_index_on_enable = group_index_on_enable
        self._group_index_on_disable = group_index_on_disable
        super(BooleanProperty, self).__init__(*args, **kwargs)


class SidePanelProperty(StringProperty):
    _uri = None
    _uri_text = None
    _target = None
    _auto_open = None
    __property_name__ = 'backend_link'

    @utils.positional(1 + Property._positional)
    def __init__(self, uri=None, text=None, target='aside_area', auto_open=False, *args, **kwargs):
        self._uri = uri
        self._uri_text = text
        self._target = target
        self._auto_open = auto_open
        super(SidePanelProperty, self).__init__(*args, **kwargs)

    def process(self, controller, fallback):
        target = getattr(fallback, self._name)
        if target is None or target == u'':
            try:
                url = controller.uri(self._uri, target=controller.util.encode_key(fallback))
            except:
                url = controller.uri(self._uri, target='--no-record--')
        else:
            try:
                url = controller.uri(self._uri, target=target)
            except:
                url = controller.uri(self._uri, target='--no-record--')
        setattr(fallback, self._name, url)


class ImageProperty(TextProperty):
    """ 圖片上傳欄位"""
    __property_name__ = 'image'


class ImagesProperty(TextProperty):
    __property_name__ = 'images'


class FileProperty(TextProperty):
    __property_name__ = 'file'


class HtmlProperty(StringProperty):
    """ 顯示用 Html 欄位"""
    __property_name__ = 'html'
    _html = ''

    @utils.positional(2 + Property._positional)
    def __init__(self, html='', *args, **kwargs):
        self._html = html
        super(HtmlProperty, self).__init__(*args, **kwargs)


class RangeProperty(FloatProperty):
    """ 範圍選擇欄位"""
    __property_name__ = 'range'
    _max = None
    _min = None
    _step = None
    _multiple = None

    @utils.positional(1 + Property._positional)
    def __init__(self, min=0, max=100, step='any', multiple=False, unit='', *args, **kwargs):
        self._max = max
        self._min = min
        self._step = step
        self._multiple = multiple
        self._unit = unit
        super(RangeProperty, self).__init__(*args, **kwargs)

    def process_before_put(self, model, field_name):
        try:
            field_value = getattr(model, field_name)
            if isinstance(field_value, int) or isinstance(field_value, basestring):
                field_value = float(field_value)
                setattr(model, field_name, field_value)
        except BadValueError:
            pass


class HiddenProperty(StringProperty):
    __property_name__ = 'hidden'


class SearchingHelperProperty(StringProperty):
    __property_name__ = 'hidden'

    @utils.positional(1 + Property._positional)
    def __init__(self, target=None, target_field_name=None, field_type=None, *args, **kwargs):
        self._target = target
        self._target_field_name = target_field_name
        self._field_type = field_type
        super(SearchingHelperProperty, self).__init__(*args, **kwargs)

    def process_before_put(self, model, field_name):
        target = model._properties[self._target]
        t = None
        target_ndb = None
        if isinstance(target, KeyProperty) or isinstance(target, CategoryProperty):
            t = getattr(model, self._target)
        if t:
            target_ndb = t.get()
        if target_ndb:
            try:
                field_value = getattr(target_ndb, self._target_field_name)
                if isinstance(field_value, int) or isinstance(field_value, float):
                    field_value = str(field_value)
                setattr(model, field_name, field_value)
                from model import DataWatcher
                watcher = DataWatcher.find_by_properties(
                    watcher=model.key, watcher_field=field_name,
                    be_watcher=target_ndb.key, be_watcher_field=self._target_field_name).get()
                if watcher is None:
                    watcher = DataWatcher(
                        watcher=model.key, watcher_field=field_name,
                        be_watcher=target_ndb.key, be_watcher_field=self._target_field_name)
                    watcher.put()
            except BadValueError:
                pass
        else:
            setattr(model, field_name, None)


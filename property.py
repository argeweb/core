#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/29.

from google.appengine.ext import ndb
from google.appengine.ext.ndb import Property, utils


# TODO 驗証屬性設置
# TODO helper 屬性設置

# ArgeWeb Base Property


class StringProperty(ndb.StringProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, field_group=0, tab_page=0, *args, **kwargs):
        self._field_group_index = field_group
        self._tab_page_index = tab_page
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


class DateTimeProperty(ndb.DateTimeProperty):
    _field_group_index = 0
    _tab_page_index = 0

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

class RichTextProperty(TextProperty):
    """ 文字編輯器 專用欄位
        將使用 js 的套件
        """
    __property_name__ = 'richtext'


class CategoryProperty(KeyProperty):
    """ 分類 專用欄位
        用於綁定於另一個 ndb.Key
        """
    __property_name__ = 'category'
    _ajax = None

    @utils.positional(2 + Property._positional)
    def __init__(self, *args, **kwargs):
        if 'ajax' in kwargs:
            self._ajax = kwargs.pop('ajax')

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
    __property_name__ = 'backend_link'

    @utils.positional(1 + Property._positional)
    def __init__(self, uri=None, text=None, target='aside_area', *args, **kwargs):
        self._uri = uri
        self._uri_text = text
        self._target = target
        super(SidePanelProperty, self).__init__(*args, **kwargs)

    def process(self, controller, fallback):
        try:
            url = controller.uri(self._uri, target=controller.util.encode_key(fallback))
        except:
            url = controller.uri(self._uri, target='--no-record--')
        setattr(fallback, self._name, url)


class ImageProperty(StringProperty):
    __property_name__ = 'image'


class ImagesProperty(TextProperty):
    __property_name__ = 'images'


class HiddenProperty(StringProperty):
    __property_name__ = 'hidden'


class SearchingHelperProperty(StringProperty):
    __property_name__ = 'hidden'

    @utils.positional(1 + Property._positional)
    def __init__(self, target=None, target_field_name=None, *args, **kwargs):
        self._target = target
        self._target_field_name = target_field_name
        super(SearchingHelperProperty, self).__init__(*args, **kwargs)


class FileProperty(StringProperty):
    __property_name__ = 'file'

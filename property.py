#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/29.

from google.appengine.ext import ndb
from google.appengine.ext.ndb import Property, utils
from argeweb.core.ndb.model import Model

__all__ = (
    'StringProperty',
    'BooleanProperty',
    'IntegerProperty',
    'FloatProperty',
    'DateTimeProperty',
    'DateProperty',
    'TimeProperty',
    'BlobKeyProperty',
    'TextProperty',
    'GeoPtProperty',
    'LinkProperty',
    'JsonProperty',
    'KeyProperty',
    'RichTextProperty',
    'CategoryProperty',
    'HiddenProperty',
    'ImageProperty',
    'ImagesProperty',
    'FileProperty',
)


class StringProperty(ndb.StringProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(StringProperty, self).__init__(*args, **kwds)


class BooleanProperty(ndb.BooleanProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(BooleanProperty, self).__init__(*args, **kwds)


class IntegerProperty(ndb.IntegerProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(IntegerProperty, self).__init__(*args, **kwds)


class FloatProperty(ndb.FloatProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(FloatProperty, self).__init__(*args, **kwds)


class DateTimeProperty(ndb.DateTimeProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(DateTimeProperty, self).__init__(*args, **kwds)


class DateProperty(ndb.DateProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(DateProperty, self).__init__(*args, **kwds)


class TimeProperty(ndb.TimeProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(TimeProperty, self).__init__(*args, **kwds)


class BlobKeyProperty(ndb.BlobKeyProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(BlobKeyProperty, self).__init__(*args, **kwds)


class TextProperty(ndb.TextProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(TextProperty, self).__init__(*args, **kwds)


class GeoPtProperty(ndb.GeoPtProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(GeoPtProperty, self).__init__(*args, **kwds)


class JsonProperty(ndb.JsonProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(JsonProperty, self).__init__(*args, **kwds)


class KeyProperty(ndb.KeyProperty):
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(2 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'field_group' in kwds:
            self._field_group_index = kwds.pop('field_group')

        if 'tab_page' in kwds:
            self._tab_page_index = kwds.pop('tab_page')

        super(KeyProperty, self).__init__(*args, **kwds)


class RichTextProperty(TextProperty):
    __property_name__ = 'richtext'
    _field_group_index = 0
    _tab_page_index = 0


class CategoryProperty(KeyProperty):
    __property_name__ = 'category'
    _field_group_index = 0
    _tab_page_index = 0
    _ajax = None

    @utils.positional(2 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'ajax' in kwds:
            self._ajax = kwds.pop('ajax')

        super(CategoryProperty, self).__init__(*args, **kwds)

    def _fix_up(self, cls, code_name):
        super(CategoryProperty, self)._fix_up(cls, code_name)
        modelclass = Model._kind_map[self._kind]
        collection_name = '%s_ref_%s_to_%s' % (cls.__name__,
                                               code_name,
                                               modelclass.__name__)

        setattr(modelclass, collection_name, (cls,self))


class LinkProperty(StringProperty):
    __property_name__ = 'link'
    _field_group_index = 0
    _tab_page_index = 0


class BackendLinkProperty(StringProperty):
    _link = None
    _link_text = None
    _link_target = None
    __property_name__ = 'backend_link'
    _field_group_index = 0
    _tab_page_index = 0

    @utils.positional(1 + Property._positional)
    def __init__(self, *args, **kwds):
        if 'url' in kwds and self._link is None:
            self._link = kwds.pop('url')
        if 'text' in kwds and self._link_text is None:
            self._link_text = kwds.pop('text')
        if 'target' in kwds and self._link_target is None:
            self._link_target = kwds.pop('target')
        else:
            self._link_target = 'aside_iframe'
        super(BackendLinkProperty, self).__init__(*args, **kwds)


class ImageProperty(StringProperty):
    __property_name__ = 'image'
    _field_group_index = 0
    _tab_page_index = 0


class ImagesProperty(TextProperty):
    __property_name__ = 'images'
    _field_group_index = 0
    _tab_page_index = 0


class HiddenProperty(StringProperty):
    __property_name__ = 'hidden'
    _field_group_index = 0
    _tab_page_index = 0


class FileProperty(StringProperty):
    __property_name__ = 'file'
    _field_group_index = 0
    _tab_page_index = 0

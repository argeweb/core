#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/29.

from google.appengine.ext.ndb import Property, utils
from google.appengine.ext.ndb import GeoPtProperty, KeyProperty, JsonProperty
from google.appengine.ext.ndb import StringProperty, BooleanProperty, IntegerProperty, FloatProperty
from google.appengine.ext.ndb import DateTimeProperty, DateProperty, TimeProperty, BlobKeyProperty, TextProperty
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


class ReverseReferenceProperty(list):
    pass


class RichTextProperty(TextProperty):
    __property_name__ = 'richtext'


class CategoryProperty(KeyProperty):
    __property_name__ = 'category'
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


class BackendLinkProperty(StringProperty):
    _link = None
    _link_text = None
    _link_target = None
    __property_name__ = 'backend_link'

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


class ImagesProperty(TextProperty):
    __property_name__ = 'images'


class HiddenProperty(StringProperty):
    __property_name__ = 'hidden'


class FileProperty(StringProperty):
    __property_name__ = 'file'
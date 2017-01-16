#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2017/01/16.
from google.appengine.ext import ndb
from argeweb.libs import wtforms
from argeweb.libs.wtforms import Form, validators
from argeweb.libs.wtforms_appengine import ndb as wtfndb
from . import fields


class Convert(object):
    def __init__(self):
        self.converters = {}
        for name in dir(self):
            if not name.startswith('convert_'):
                continue
            add_convertor(name[8:], getattr(self, name))

    def convert_StringProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.StringProperty``."""
        if prop._repeated:
            from google.appengine.ext.ndb import fields as gae_fields
            return gae_fields.StringListPropertyField(**kwargs)
        if prop._required:
            kwargs['validators'].append(validators.InputRequired())
        kwargs['validators'].append(validators.length(max=500))
        return fields.StringField(**kwargs)

    def convert_BooleanProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.BooleanProperty``."""
        return fields.BooleanField(**kwargs)

    def convert_IntegerProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.IntegerProperty``."""
        if prop._repeated:
            from google.appengine.ext.ndb import fields as gae_fields
            return gae_fields.IntegerListPropertyField(**kwargs)
        v = validators.NumberRange(min=-0x8000000000000000, max=0x7fffffffffffffff)
        kwargs['validators'].append(v)
        return fields.IntegerField(**kwargs)

    def convert_FloatProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.FloatProperty``."""
        if prop._code_name == 'sort':
            return None
        return fields.FloatField(**kwargs)

    def convert_DateTimeProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.DateTimeProperty``."""
        if prop._auto_now or prop._auto_now_add:
            return None

        kwargs.setdefault('format', '%Y-%m-%d %H:%M:%S')
        return fields.DateTimeField(**kwargs)

    def convert_TimeProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.TimeProperty``."""
        if prop._auto_now or prop._auto_now_add:
            return None

        kwargs.setdefault('format', '%H:%M:%S')
        return fields.DateTimeField(**kwargs)

    def convert_StructuredProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.StructuredProperty``."""
        return None

    def convert_LocalStructuredProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.LocalStructuredProperty``."""
        return None

    def convert_JsonProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.JsonProperty``."""
        return fields.JsonPropertyField(**kwargs)

    def convert_PickleProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.PickleProperty``."""
        return None

    def convert_GenericProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.GenericProperty``."""
        kwargs['validators'].append(validators.length(max=500))
        return fields.StringField(**kwargs)

    def convert_TextProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.TextProperty``."""
        return fields.TextAreaField(**kwargs)

    def convert_ComputedProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.ComputedProperty``."""
        return None

    def convert__ClassKeyProperty(self, model, prop, kwargs):
            """Returns a form field for a ``ndb.ComputedProperty``."""
            return None

    def convert_UserProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.UserProperty``."""
        if isinstance(prop, ndb.Property) and (prop._auto_current_user or prop._auto_current_user_add):
            return None

        kwargs['validators'].append(wtforms.validators.email())
        kwargs['validators'].append(wtforms.validators.length(max=500))
        return fields.UserField(**kwargs)

    def convert_KeyProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.KeyProperty``."""
        kwargs['kind'] = prop._kind
        kwargs.setdefault('allow_blank', not prop._required)
        if not prop._repeated:
            return fields.KeyPropertyField(**kwargs)
        else:
            del kwargs['allow_blank']
            return fields.MultipleReferenceField(**kwargs)

    def convert_CategoryProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.KeyProperty``."""
        kwargs['kind'] = prop._kind
        kwargs.setdefault('allow_blank', not prop._required)
        if prop._ajax:
            return fields.CategoryAjaxField(**kwargs)
        return fields.CategoryField(**kwargs)

    def convert_SidePanelProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.BlobKeyProperty``."""
        kwargs['uri'] = prop._uri
        kwargs['uri_text'] = prop._uri_text
        kwargs['target'] = prop._target
        return fields.SidePanelField(**kwargs)

    def convert_BlobKeyProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.BlobKeyProperty``."""
        return fields.BlobKeyField(**kwargs)

    def convert_GeoPtProperty(self, model, prop, kwargs):
        return fields.GeoPtPropertyField(**kwargs)

    def convert_RichTextProperty(self, model, prop, kwargs):
        return fields.RichTextField(**kwargs)

    def convert_HiddenProperty(self, model, prop, kwargs):
        return fields.HiddenField(**kwargs)

    def convert_FileProperty(self, model, prop, kwargs):
        return fields.FilePropertyField(**kwargs)

    def convert_LinkProperty(self, model, prop, kwargs):
        return fields.LinkPropertyField(**kwargs)

    def convert_ImageProperty(self, model, prop, kwargs):
        return fields.ImageField(**kwargs)

    def convert_ImagesProperty(self, model, prop, kwargs):
        return fields.ImagesField(**kwargs)

    def convert_DateProperty(self, model, prop, kwargs):
        """Returns a form field for a ``ndb.DateProperty``."""
        if prop._auto_now or prop._auto_now_add:
            return None

        kwargs.setdefault('format', '%Y-%m-%d')
        return fields.DateField(**kwargs)

### Additional Converters
def add_convertor(property_type, converter_func):
    """
    Converts properties from a ``ndb.Model`` class to form fields.

    Default conversions between properties and fields:

    """  # noqa
    setattr(wtfndb.ModelConverter, 'convert_%s' % property_type, converter_func)


def fallback_converter(self, model, prop, kwargs):
    pass

setattr(wtfndb.ModelConverter, 'fallback_converter', fallback_converter)

# argeweb converters
Convert()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2017/01/16.
import operator
import warnings
import decimal
import datetime
import json
import inspect

from google.appengine.ext import db, ndb, blobstore
from google.appengine.api.users import User
from argeweb.libs.wtforms import widgets as wtforms_widgets
from argeweb.libs.wtforms.compat import text_type, string_types
from argeweb.libs.wtforms.widgets import html5 as html5_widgets
from argeweb.libs import wtforms
from argeweb.core.gaeforms import widgets


TextField = wtforms.StringField


class BooleanField(wtforms.BooleanField):
    _field_group_index = 0


class FloatField(wtforms.FloatField):
    _field_group_index = 0


class DateTimeField(wtforms.DateTimeField):
    _field_group_index = 0
    _set_default = False

    def __init__(self, label=None, validators=None, format='%Y-%m-%d %H:%M:%S', **kwargs):
        if 'auto_now_add' in kwargs:
            kwargs.pop('auto_now_add')
            self._set_default = True
        if 'auto_now' in kwargs:
            kwargs.pop('auto_now')
            self._set_default = True

        super(DateTimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                self.data = datetime.datetime.strptime(date_str, self.format)
            except ValueError:
                if date_str is u'' and self._set_default:
                    self.date = datetime.datetime.now().strftime(self.format)
                else:
                    self.data = None
                    raise ValueError(self.gettext('Not a valid datetime value'))


class TextAreaField(wtforms.TextAreaField):
    _field_group_index = 0


class JsonPropertyField(wtforms.StringField):
    """
    This field is the base for most of the more complicated fields, and
    represents an ``<input type="text">``.
    """
    widget = wtforms_widgets.TextArea()

    def process_formdata(self, valuelist):
        if valuelist is not "":
            self.data = json.loads(valuelist[0])
        else:
            self.data = None

    def _value(self):
        return json.dumps(self.data) if self.data is not None else ''


class DateField(wtforms.DateField):
    widget = html5_widgets.DateInput()

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or ''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                self.data = datetime.datetime.strptime(date_str, self.format)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid datetime value'))


class LinkPropertyField(wtforms.StringField):
    widget = html5_widgets.URLInput()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]


class IntegerField(wtforms.IntegerField):
    widget = html5_widgets.NumberInput()


class StringField(wtforms.StringField):
    """
    This field is the base for most of the more complicated fields, and
    represents an ``<input type="text">``.
    """
    widget = wtforms.widgets.TextInput()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        else:
            self.data = ''

    def _value(self):
        return text_type(self.data) if self.data is not None else ''

    def pre_validate(self, form):
      if self.data:
          a = self.data


class KeyPropertyField(wtforms.fields.SelectFieldBase):
    """
    Identical to the non-ndb counterpart, but only supports ndb references.
    """
    _kind = None
    _query = None
    _the_same = None
    widget = wtforms.widgets.TextInput()

    def __init__(self, label=None, validators=None, kind=None,
                 label_attr=None, get_label=None, allow_blank=False,
                 blank_text='', query=None, **kwargs):
        if 'the_same' in kwargs:
            kwargs.pop('the_same')
        super(KeyPropertyField, self).__init__(label, validators, **kwargs)
        if label_attr is not None:
            warnings.warn('label_attr= will be removed in WTForms 1.1, use get_label= instead.', DeprecationWarning)
            self.get_label = operator.attrgetter(label_attr)
        elif get_label is None:
            self.get_label = lambda x: x
        elif isinstance(get_label, string_types):
            self.get_label = operator.attrgetter(get_label)
        else:
            self.get_label = get_label

        self.allow_blank = allow_blank
        self.blank_text = blank_text
        self._set_data(None)
        self._query = query
        self._kind = kind

    @property
    def query(self):
        if self._query is None and self._kind is not None:
            if isinstance(self._kind, basestring):
                kind = ndb.Model._kind_map[self._kind]
            else:
                kind = self._kind
            return kind.query
        return self._query

    def _value(self):
        if self.data:
            return self.data.urlsafe()
        else:
            return '__None'

    def _get_data(self):
        if self._formdata is not None:
            # if self.query:
            #     self.query.filter('__key__ ==', self._formdata)
            #     for obj in self.query.fetch(1000):
            #         if obj.key.urlsafe() == self._formdata:
            #             self._set_data(obj.key)
            #             break
            # else:
            self._set_data(ndb.Key(urlsafe=self._formdata))
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def iter_choices(self):
        if self.allow_blank or not self.query:
            yield ('__None', self.blank_text, self.data is None, None)

        if self.query:
            if inspect.ismethod(self.query):
                query = self.query()
                # self.query = query
            # TODO 如果大於 50筆 ?
            if query:
                for obj in query.fetch(50):
                    key = obj.key.urlsafe()
                    label = self.get_label(obj)
                    yield (key, label, self.data and (self.data == obj.key), getattr(obj, 'category', None))
        elif self.data:
            key = self.data
            item = key.get()
            yield(key, self.get_label(item), True, getattr(item, 'category', None))

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] == '__None':
                self.data = None
            else:
                self._data = None
                self._formdata = valuelist[0]

    def pre_validate(self, form):
        if self.data and self.query:
            try:
                if str(type(self.data.get())).find(str(self._kind)) < 0:
                    raise ValueError(self.gettext('Not a valid choice %s ' % self.data))
            except Exception as e:
                raise ValueError(self.gettext('Not a valid choice %s' % e))
        elif not self.allow_blank:
            raise ValueError(self.gettext('Not a valid choice and not allow blank'))

    # def pre_validate(self, form):
    #     import logging
    #     logging.debug('#!!!!')
    #     s = str(self.data)
    #     if self.data and self.query:
    #         if self.allow_blank:
    #             pass
    #         else:
    #             try:
    #                 g = self.query.filter('__key__ ==', self.data.key).get()
    #             except Exception as e:
    #                 raise ValueError(self.gettext('Not a valid choice'))
    #
    #             if g is None:
    #                 raise ValueError(self.gettext('Not a valid choice'))
    #     else:
    #         if not self.allow_blank:
    #             raise ValueError(self.gettext('Not a valid choice and not allow blank'))
            # for obj in self.query:
            #     if self.data.urlsafe() == obj.key.urlsafe():
            #         break
            # else:
            #     raise ValueError(self.gettext('Not a valid choice'))


class ApplicationUserField(KeyPropertyField):
    """
    A field that alls WTForms to produce a field that can be used
    to edit a db.UserProperty or ndb.UserProperty. Displays as a text field with an
    Email.
    """
    widget = widgets.ApplicationUserWidget()
    __temporary_data = None
    _is_lock = None

    def __init__(self, *args, **kwargs):
        self._is_lock = kwargs.pop('is_lock')
        super(ApplicationUserField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if self.data in ['__None', u'__None', '', u'']:
            self.data = None
        if self.data:
            from ..ndb.util import decode_key
            self.data = decode_key(self.data)
    #
    # def post_validate(self, form, validation_stopped):
    #     if self.__temporary_data:
    #         self.data = self.__temporary_data


class CategoryDropdownField(KeyPropertyField):
    """
    Identical to the non-ndb counterpart, but only supports ndb references.
    """
    widget = widgets.CategoryDropdownWidget()
    _the_same = None

    def __init__(self, *args, **kwargs):
        self._the_same = kwargs.pop('the_same')
        super(CategoryDropdownField, self).__init__(*args, **kwargs)


class SidePanelField(wtforms.StringField):
    """
    Identical to the non-ndb counterpart, but only supports ndb references.
    """
    _uri = None
    _uri_text = None
    _target = None
    _auto_open = None
    widget = widgets.SidePanelWidget()

    def __init__(self, *args, **kwargs):
        self._uri = kwargs.pop('uri')
        self._uri_text = kwargs.pop('uri_text')
        self._target = kwargs.pop('target')
        self._auto_open = kwargs.pop('auto_open')
        super(SidePanelField, self).__init__(*args, **kwargs)


class CategoryField(KeyPropertyField):
    """
    Identical to the non-ndb counterpart, but only supports ndb references.
    """
    widget = widgets.CategorySelectWidget()


class MultipleReferenceField(wtforms.SelectMultipleField):
    """
    Allows WTForms to display a field for a db.List(db.Key),
    db.MultipleReferenceProperty, or ndb.KeyProperty(repeated=True). Shows the options as a list of
    checkboxes. The referenced class must have a __str__ or __unicode__
    method defined.
    """
    widget = widgets.MultipleReferenceCheckboxWidget()
    option_widget = wtforms.widgets.CheckboxInput()

    def __init__(self, kind, choices=None, validate_choices=True, query=None, *args, **kwargs):
        super(MultipleReferenceField, self).__init__(*args, **kwargs)
        if isinstance(kind, basestring):
                kind = ndb.Model._kind_map[kind]
        self.kind = kind

        if query:
            self.query = query
        else:
            self.query = self.kind.query()

        self.validate_choices = validate_choices

    def iter_choices(self):
        for item in self.query:
            value = item.key
            label = str(item)

            selected = self.data is not None and value in self.data

            if not self.kind or issubclass(self.kind, ndb.Model):
                value = value.urlsafe()

            yield (value, label, selected)

    def pre_validate(self, form):
        if self.validate_choices:
            self.choices = [(x, 'key') for x in self.query.fetch(keys_only=True)]
            super(MultipleReferenceField, self).pre_validate(form)

    def process_data(self, value):
        try:
            self.data = list(v for v in value)
        except (ValueError, TypeError):
            self.data = []

    def process_formdata(self, valuelist):
        if valuelist:
            if not self.kind or issubclass(self.kind, ndb.Model):
                self.data = [ndb.Key(urlsafe=x) for x in valuelist]
            else:
                self.data = [db.Key(x) for x in valuelist]
        else:
            self.data = []


class BlobKeyField(wtforms.FileField):
    """
    Manages uploading blobs and cleaning up blob entries if validation fails
    """

    def __init__(self, *args, **kwargs):
        super(BlobKeyField, self).__init__(*args, **kwargs)

        # Wrap the original validate method on the form to get a true post-all-validators callback.
        if '_form' in kwargs:
            form = kwargs['_form']
            original_validate = form.validate

            def validate_wrapper():
                res = original_validate()
                self.post_form_validate(form)
                return res

            form.validate = validate_wrapper

    def post_form_validate(self, form):
        if form.errors:
            self.delete_blob()

    def get_blob_info(self):
        import cgi
        if self.data is None or not isinstance(self.data, cgi.FieldStorage) or not 'blob-key' in self.data.type_options:
            return None

        info = blobstore.parse_blob_info(self.data)
        if not info:
            return None
        return info

    def delete_blob(self):
        info = self.get_blob_info()
        if info:
            blobstore.delete(info.key())


class GeoPtPropertyField(TextField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                lat, lon = valuelist[0].split(',')
                data = '%s,%s' % (decimal.Decimal(lat.strip()), decimal.Decimal(lon.strip()),)
                self.data = ndb.GeoPt(data) # note this change from the original GeoPtPropertyField
            except (decimal.InvalidOperation, ValueError):
                raise ValueError('Not a valid coordinate location')


class FilePropertyField(TextField):
    """
    Identical to the non-ndb counterpart, but only supports ndb references.
    """
    widget = widgets.FileSelectWidget()
    __temporary_data = None
    def _value(self):
        if self.data:
            return self.data
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = valuelist[0]
        else:
            self.data = None

    def pre_validate(self, form):
        if self.data:
            self.__temporary_data = self.data
            self.data = self.data

    def post_validate(self, form, validation_stopped):
        if self.__temporary_data:
            self.data = self.__temporary_data


class ImageField(TextField):
    """
    Identical to the non-ndb counterpart, but only supports ndb references.
    """
    widget = widgets.ImageSelectWidget()
    __temporary_data = None
    def _value(self):
        if self.data:
            return self.data
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = valuelist[0]
        else:
            self.data = None

    def pre_validate(self, form):
        if self.data:
            self.__temporary_data = self.data
            self.data = self.data

    def post_validate(self, form, validation_stopped):
        if self.__temporary_data:
            self.data = self.__temporary_data


class ImagesField(ImageField):
    widget = widgets.ImagesSelectWidget()


class HtmlField(wtforms.Field):
    _html = 'any'
    widget = widgets.HtmlWeight()

    def __init__(self, *args, **kwargs):
        if 'html' in kwargs:
            self._html = kwargs.pop('html')
        super(HtmlField, self).__init__(*args, **kwargs)


class RangeField(wtforms.Field):
    _max = 100
    _min = 0
    _step = 'any'
    _unit = ''
    _multiple = False
    widget = widgets.RangeWeight()

    def __init__(self, *args, **kwargs):
        if 'max' in kwargs:
            self._max = kwargs.pop('max')
        if 'min' in kwargs:
            self._min = kwargs.pop('min')
        if 'step' in kwargs:
            self._step = kwargs.pop('step')
        if 'unit' in kwargs:
            self._unit = kwargs.pop('unit')
        if 'multiple' in kwargs:
            self._multiple = kwargs.pop('multiple')
        super(RangeField, self).__init__(*args, **kwargs)


class RichTextField(wtforms.Field):
    widget = widgets.RichTextWidget()
    __temporary_data = None

    def _value(self):
        if self.data:
            return self.data
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = valuelist[0]
        else:
            self.data = None

    def pre_validate(self, form):
        if self.data:
            self.__temporary_data = self.data
            self.data = self.data

    def post_validate(self, form, validation_stopped):
        if self.__temporary_data:
            self.data = self.__temporary_data


class CodeJSONField(RichTextField):
    widget = widgets.CodeWidget(code_type='json')
    __temporary_data = None


class CodeJSField(RichTextField):
    widget = widgets.CodeWidget(code_type='javascript')
    __temporary_data = None


class CodeCSSField(RichTextField):
    widget = widgets.CodeWidget(code_type='css')
    __temporary_data = None


class CategoryReferenceField(wtforms.Field):
    widget = widgets.RichTextWidget()
    __temporary_data = None
    def __init__(self, kind, choices=None, validate_choices=True, query=None, *args, **kwargs):
        super(CategoryReferenceField, self).__init__(*args, **kwargs)
        if isinstance(kind, basestring):
                kind = ndb.Model._kind_map[kind]
        self.kind = kind

        if query:
            self.query = query
        else:
            self.query = self.kind.query()

        self.validate_choices = validate_choices

    def iter_choices(self):
        for item in self.query:
            value = item.key
            label = str(item)

            selected = self.data is not None and value in self.data

            if not self.kind or issubclass(self.kind, ndb.Model):
                value = value.urlsafe()

            yield (value, label, selected)

    def pre_validate(self, form):
        if self.validate_choices:
            self.choices = [(x, 'key') for x in self.query.fetch(keys_only=True)]
            super(CategoryReferenceField, self).pre_validate(form)

    def process_data(self, value):
        try:
            self.data = list(v for v in value)
        except (ValueError, TypeError):
            self.data = []

    def process_formdata(self, valuelist):
        if valuelist:
            if not self.kind or issubclass(self.kind, ndb.Model):
                self.data = [ndb.Key(urlsafe=x) for x in valuelist]
            else:
                self.data = [db.Key(x) for x in valuelist]
        else:
            self.data = []


class HiddenField(wtforms.fields.HiddenField):
    widget = wtforms.widgets.HiddenInput()
    __temporary_data = None
    def _value(self):
        if self.data:
            return self.data
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = valuelist[0]
        else:
            self.data = None

    def pre_validate(self, form):
        if self.data:
            self.__temporary_data = self.data
            self.data = self.data

    def post_validate(self, form, validation_stopped):
        if self.__temporary_data:
            self.data = self.__temporary_data
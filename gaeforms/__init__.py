#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO CategoryAjaxWidget CategoryLinkWidget
"""
# 由 Model 轉換為表單的過程
# Scaffold 呼叫 argeweb.core.gaeforms.model_form (實際是使用 argeweb.libs.wtforms_appengine.ndb.model_form)
# model_form 呼叫 model_fields
# model_fields 則用 ModelConverter 將 Model 裡的各種 Property 轉成各種 Field
# 再由 Field 所定義的 Widget 去作資料的呈現

  +====================+=======================+===========================+=======================================+
  | Property subclass  | in wtforms_appengine  | in gaeforms               | widget                                |
  +====================+=======================+===========================+=======================================+
  | CategoryProperty   | ----                  | CategoryField        or   | gaeforms.widgets.CategorySelectWidget |
  |                    |                       | CategoryLinkField    or   | gaeforms.widgets.CategoryLinkWidget   |
  |                    |                       | CategoryAjaxField         | gaeforms.widgets.CategoryAjaxWidget   |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | RichTextProperty   | ----                  | RichTextField             | gaeforms.widgets.RichTextWidget       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | ImageProperty      | ----                  | ImageField                | gaeforms.widgets.ImageSelectWidget    |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | ImagesProperty     | ----                  | ImagesField               | gaeforms.widgets.ImagesSelectWidget   |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | FileProperty       | ----                  | FilePropertyField         | gaeforms.widgets.FileSelectWidget     |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | HiddenProperty     | ----                  | HiddenField               | wtforms.widgets.HiddenInput           |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | StringProperty     | TextField             | StringField          or   | wtforms.widgets.TextInput             |
  |                    |                       | StringListPropertyField   | wtforms.widgets.TextArea              |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | BooleanProperty    | BooleanField          |                           | wtforms.widgets.CheckboxInput         |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | IntegerProperty    | IntegerField          | IntegerField              | html5_widgets.NumberInput             |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | FloatProperty      | TextField             |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | DateTimeProperty   | DateTimeField         |                           |                                       |
  |                    |                       |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | DateProperty       | DateField             | DatePropertyFiled         | html5_widgets.DateInput               |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | TimeProperty       | DateTimeField         |                           |                                       |
  |                    |                       |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | TextProperty       | TextAreaField         |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | GeoPtProperty      | TextField             | GeoPtPropertyField        |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | KeyProperty        | KeyPropertyField      | KeyPropertyField     or   |                                       |
  |                    |                       | MultipleReferenceField    |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | BlobKeyProperty    | None                  | BlobKeyField              |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | UserProperty       | None                  | UserField                 |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | StructuredProperty | None                  |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | LocalStructuredPro | None                  |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | JsonProperty       | JsonPropertyField     |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | PickleProperty     | None                  |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | GenericProperty    | None                  |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | ComputedProperty   | none                  |                           |                                       |
  +--------------------+-----------------------+---------------------------+---------------------------------------+
  | _ClassKeyProperty  | none                  |                           |                                       |
  +====================+=======================+===========================+==================+====================+
"""

#import wtforms_json
#wtforms_json.init()

from google.appengine.ext import ndb
from argeweb.libs.wtforms_appengine.ndb import *
import fields
import widgets
import convertor
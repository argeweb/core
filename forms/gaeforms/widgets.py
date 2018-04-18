#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2017/01/16.
from .. import wtforms
from cgi import escape
from argeweb.core.template import pure_text

html_params = wtforms.widgets.html_params
HTMLString = wtforms.widgets.HTMLString
text_type = wtforms.compat.text_type


class MultipleReferenceCheckboxWidget(object):
    """
    Widget for MultipleReferenceField. Displays options as checkboxes"""
    def __init__(self, html_tag='div'):
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', '')
        html = [u'<%s %s>'
            % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            html.append(u'<label class="checkbox" for="%s">%s %s</label>'
                % (subfield.label.field_id, subfield(), subfield.label.text))
        html.append(u'</%s>' % self.html_tag)
        return HTMLString(u''.join(html))


class RichTextWidget(object):
    html_params = staticmethod(html_params)
    '''
    Widget for MultipleReferenceField. Displays options as checkboxes'''
    def __init__(self, html_tag='textarea'):
        super(RichTextWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', '') + ' editor'
        if field.data == 'None' or field.data is None:
            field.data = ''
        html = u'<%s %s>%s</%s>'% (
            self.html_tag, html_params(**kwargs),
            field.data, self.html_tag
        )
        return HTMLString(html)


class CodeWidget(object):
    html_params = staticmethod(html_params)
    '''
    Widget for MultipleReferenceField. Displays options as checkboxes'''
    def __init__(self, html_tag='textarea', code_type='json'):
        super(CodeWidget, self).__init__()
        self.html_tag = html_tag
        self.code_type = code_type

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', '') + ' editor ' + self.code_type
        if field.data == 'None' or field.data is None:
            field.data = ''
        html = u'<%s %s>%s</%s>'% (
            self.html_tag, html_params(**kwargs),
            field.data, self.html_tag
        )
        return HTMLString(html)


class FileSelectWidget(object):
    html_params = staticmethod(html_params)
    '''
    Widget for MultipleReferenceField. Displays options as checkboxes'''
    def __init__(self, html_tag='input'):
        super(FileSelectWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', 'form-control') + ' file'
        if field.data == 'None' or field.data is None:
            field.data = ''
        if field.data:
            field_data = field.data
        else:
            field_data = ''
        ext = field_data.split('.')[-1]
        if len(ext) > 5:
            ext = '---'
        html = u"""
        <div class="file-picker-div input-group">
            <%s type="text" %s value="%s" />
            <div class="input-group-btn">
                <div class="btn btn-outline file-picker-item" data-ext="%s">%s</div>
            </div>
            <a href="#" class="btn brand-bg-color file-picker"><i class="fa fa-file"></i> 選取檔案</a>
        </div>
        """ % (self.html_tag, html_params(**kwargs), field_data, ext, ext)
        return HTMLString(html)


class ImageSelectWidget(object):
    html_params = staticmethod(html_params)
    '''
    Widget for ImageField. Displays image upload button'''
    def __init__(self, html_tag='input'):
        super(ImageSelectWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', 'form-control') + ' image'
        if field.data == 'None' or field.data is None:
            field.data = ''
        if field.data:
            field_data = field.data
        else:
            field_data = ''
        html = u"""
        <div class="file-picker-div input-group">
            <%s type="text" %s value="%s" />
            <div class="input-group-btn">
                <div class="btn btn-outline file-picker-item" style="background-image: url(%s);"></div>
            </div>
            <a href="#" class="btn brand-bg-color file-picker"><i class="fa fa-photo"></i> 選取圖片</a>
        </div>
        """ % (self.html_tag, html_params(**kwargs), field_data, field_data)
        return HTMLString(html)


class ImagesSelectWidget(object):
    html_params = staticmethod(html_params)
    '''
    Widget for MultipleReferenceField. Displays options as checkboxes'''
    def __init__(self, html_tag='textarea'):
        super(ImagesSelectWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', '') + ' images'
        if field.data == 'None' or field.data is None:
            field.data = ''
        list = field.data.split(';')
        html = u'<div class="imgs-selector-div">' \
               u'<%s %s style="display:none" >%s</%s>' \
               u'<a data-target="%s" class="btn-images-open-dropbox">Dropbox</a>'\
               u'<a data-target="%s" class="btn-images-open-google-picker">Google相冊</a>'\
               u'<a data-target="%s" class="btn-images-open-server">伺服器</a>' \
               u'<div class="img_selector_sp"></div>'\
               % (self.html_tag, html_params(**kwargs), field.data, self.html_tag, field.id, field.id, field.id,)
        for item in list:
            if item != u'':
                html += u'<div class="file-picker-item" data-link="%s" style="background-image: url(%s);" />' % (item, item)
        return HTMLString(html + '</div>')


class HtmlWeight(object):
    def __init__(self, html_tag='div'):
        super(HtmlWeight, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        html = u'<%s class="html-helper">%s</%s>' % (self.html_tag, field._html, self.html_tag)
        return HTMLString(html)


class ApplicationUserWidget(object):
    html_params = staticmethod(html_params)

    def __init__(self, html_tag='input'):
        super(ApplicationUserWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', 'form-control') + ' image'
        if field.data == 'None' or field.data is None:
            field.data = ''
        u = None
        user_name = ''
        user_image = ''
        user_key_urlsafe = '__None'
        if field.data:
            field_data = field.data
            u = field_data.get()
        else:
            field_data = '__None'
        if u is not None:
            user_name = u.name
            user_image = u.avatar
            user_key_urlsafe = u.key.urlsafe()
        btn_text = u'選擇使用者'
        is_lock = ''
        if field._is_lock and u is not None:
            btn_text = u'無法變更'
            is_lock = 'lock'

        html = u"""
        <div class="user_picker_div input-group">
            <%s type="text" class="form-control field-type-user-field" value="%s" />
            <input type="hidden" %s value="%s" />
            <div class="input-group-btn">
                <div class="btn btn-outline user-picker-item" style="background-image: url(%s);"></div>
            </div>
            <a href="#" class="btn brand-bg-color user-picker %s"><i class="fa fa-photo"></i> %s</a>
        </div>
        """ % (self.html_tag, user_name, html_params(**kwargs), user_key_urlsafe, user_image, is_lock, btn_text)
        return HTMLString(html)


class RangeWeight(object):
    html_params = staticmethod(html_params)

    def __init__(self, html_tag='input'):
        super(RangeWeight, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs.setdefault('min', field._min)
        kwargs.setdefault('max', field._max)
        kwargs.setdefault('step', field._step)
        multiple = field._multiple and 'multiple' or ''
        if field.data == 'None' or field.data is None:
            field.data = field._min
        if field.data:
            field_data = field.data
        else:
            field_data = field._min
        html = u"""
        <%s type="range" %s %s value="%s" data-unit="%s"/><span>%s%s</span>
        """ % (self.html_tag, html_params(**kwargs), multiple, field_data, field._unit, field_data, field._unit)
        return HTMLString(html)


class CategorySelectWidget(object):
    html_params = staticmethod(html_params)

    def __init__(self, html_tag='input'):
        super(CategorySelectWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', 'form-control') + ' image'
        if field.data == 'None' or field.data is None:
            field.data = ''
        u = None
        user_name = ''
        user_image = ''
        user_key_urlsafe = ''
        if field.data:
            field_data = field.data
            u = field_data.get()
        else:
            field_data = ''
        kind = ''
        if field.query and field.query.kind:
            kind = field.query.kind
        if u is not None:
            user_name = u.name
            user_key_urlsafe = u.key.urlsafe()
        btn_text = u'選擇分類'

        html = u"""
        <div class="user_picker_div input-group">
            <%s type="text" class="form-control field-type-user-field" value="%s" />
            <input type="hidden" %s value="%s" />
            <a href="#" class="btn brand-bg-color category-picker" data-kind="%s"><i class="fa fa-photo"></i> %s</a>
        </div>
        """ % (self.html_tag, user_name, html_params(**kwargs), user_key_urlsafe, kind, btn_text)
        return HTMLString(html)


class CategoryDropdownWidget(object):
    """
    Renders a select field.

    If `multiple` is True, then the `size` property should be specified on
    rendering to make the field useful.

    The field must provide an `iter_choices()` method which the widget will
    call on rendering; this method must yield tuples of
    `(value, label, selected)`.
    """
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select data="down" %s>' % html_params(name=field.name, **kwargs)]
        iter_list = field.iter_choices()
        items = []
        for val, label, selected, category in iter_list:
            str_cat = category and category.urlsafe() or '__None'
            if field._the_same:
                is_root = str_cat == '__None' and True or False
            else:
                is_root = True
            items.append({
                'val': val,
                'label': label,
                'selected': selected,
                'category': str_cat,
                'is_root': is_root,
                'children': [],
            })
        root_list = []
        for item in items:
            if item['is_root']:
                root_list.append(item)
            for item2 in items:
                if item2['category'] == item['val'] and item2['category'] != '__None':
                    item['children'].append(item2)
        for item in root_list:
            html += self.process_child_item(item, 0)

        html.append('</select>')
        return HTMLString(''.join(html))

    def process_child_item(self, item, parent_count):
        html = []
        return_item = self.render_option(
            item['val'],
            item['label'],
            item['selected'],
            count=parent_count
        )
        if return_item:
            html.append(return_item)
        for child_item in item['children']:
            html += self.process_child_item(child_item, parent_count+1)
        return html

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = text_type(value)
        count = 0
        if 'count' in kwargs:
            count = kwargs['count']
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        if value == '__None':
            return HTMLString('<option %s>%s</option>' % (
                html_params(**options),
                escape(pure_text(text_type(label)))
            ))
        else:
            if hasattr(label, 'level') and hasattr(label, 'name'):
                if label.level == 9999 and label.name == u'super_user' and (selected is False or selected is None):
                    return None
            return HTMLString('<option %s>%s%s</option>' % (
                html_params(**options),
                str('----' * count),
                escape(pure_text(text_type(label.title)))))


class SidePanelWidget(object):
    """
    Renders a select field.

    If `multiple` is True, then the `size` property should be specified on
    rendering to make the field useful.

    The field must provide an `iter_choices()` method which the widget will
    call on rendering; this method must yield tuples of
    `(value, label, selected)`.
    """
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('form-control', '')
        if field.data == 'None' or field.data is None:
            field.data = ''
        if field._auto_open is True:
            kwargs['class'] = kwargs['class'] + ' side_panel_open_auto'
        html = ['<a %s href="%s" target="%s">' % (html_params(name=field.name, **kwargs), field.data, field._target)]
        html.append(field._uri_text)

        html.append('</a>')
        return HTMLString(''.join(html))

class Option(object):
    """
    Renders the individual option from a select field.

    This is just a convenience for various custom rendering situations, and an
    option by itself does not constitute an entire field.
    """
    def __call__(self, field, **kwargs):
        return CategorySelectWidget.render_option(field._value(), field.label.text, field.checked, **kwargs)


class HiddenWidget(object):
    html_params = staticmethod(html_params)
    """
    Widget for MultipleReferenceField. Displays options as checkboxes"""
    def __init__(self, html_tag='input'):
        super(HiddenWidget, self).__init__()
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.id)
        kwargs['class'] = kwargs.get('class', '').replace('span6', 'form-control') + ' image'
        if field.data == 'None' or field.data is None:
            field.data = ''
        if field.data:
            field_data = field.data
        else:
            field_data = ''
        html = u"""
        <div class="file-picker-div input-group">
            <%s type="text" %s value="%s" />
            <div class="input-group-btn">
                <div class="btn btn-outline file-picker-item" style="background-image: url(%s);" /></div>
                <a href="#" class="btn brand-bg-color"><i class="fa fa-photo"></i> 選取</a>
            </div>
        </div>
        """ % (self.html_tag, html_params(**kwargs), field_data, field_data)
        return HTMLString(html)
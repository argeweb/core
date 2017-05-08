#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes that extend the basic ndb.Model classes
"""

from google.appengine.ext import ndb
import types
import time
from argeweb.behaviors.searchable import Searchable
from ..property import SearchingHelperProperty, KeyProperty, CategoryProperty

class ModelMeta(ndb.model.MetaModel):
    """
    Augments Models by adding the class methods find_all_by_x
    and find_by_x that are proxies for find_all_by_properties and
    find_by_properties respectively.
    """
    def __init__(cls, name, bases, dct):
        super(ModelMeta, cls).__init__(name, bases, dct)

        # Make sure the Meta class has a proper chain
        if cls.__name__ != 'Model' and not issubclass(cls.Meta, Model.Meta):
            cls.Meta = type('Meta', (cls.Meta, Model.Meta), {})

        # Behaviors
        setattr(cls, 'behaviors', [x(cls) for x in cls.Meta.behaviors])

        # Inject finder methods
        ModelMeta._inject_find_methods(cls, name, bases, dct)

    @staticmethod
    def _inject_find_methods(cls, name, bases, dct):
        # find_by_x and find_all_by_x
        for prop_name, property in cls._properties.items():
            find_all_name = 'find_all_by_' + prop_name

            def bind_all(name):
                def find_all(cls, value):
                    args = {}
                    args[name] = value
                    return cls.find_all_by_properties(**args)
                return types.MethodType(find_all, cls)

            if not find_all_name in dct:
                setattr(cls, find_all_name, bind_all(prop_name))

            find_one_name = 'find_by_' + prop_name

            def bind_one(name):
                def find_one(cls, value):
                    args = {}
                    args[name] = value
                    return cls.find_by_properties(**args)
                return types.MethodType(find_one, cls)

            if not find_one_name in dct:
                setattr(cls, find_one_name, bind_one(prop_name))


class Model(ndb.Model):
    """
    Base class that augments ndb Models by adding easier find methods and callbacks.
    """
    __metaclass__ = ModelMeta

    class Meta(object):
        behaviors = (Searchable, )

    @classmethod
    def find_all_by_properties(cls, **kwargs):
        """
        Generates an ndb.Query with filters generated from the keyword arguments.

        Example::

            User.find_all_by_properties(first_name='Jon',role='Admin')

        is the same as::

            User.query().filter(User.first_name == 'Jon', User.role == 'Admin')

        """
        query = cls.query()
        for name, value in kwargs.items():
            property = cls._properties[name]
            query = query.filter(property == value)
        return query

    @classmethod
    def find_by_properties(cls, **kwargs):
        """
        Similar to find_all_by_properties, but returns either None or a single ndb.Model instance.

        Example::

            User.find_by_properties(first_name='Jon',role='Admin')

        """
        return cls.find_all_by_properties(**kwargs).get()

    def before_put(self):
        """
        Called before an item is saved.

        :arg self: refers to the item that is about to be saved
        :note: ``self.key`` is invalid if the current item has never been saved
        """
        pass

    def after_put(self, key):
        """
        Called after an item has been saved.

        :arg self: refers to the item that has been saved
        :arg key: refers to the key that the item was saved as
        """
        pass

    @classmethod
    def before_delete(cls, key):
        """
        Called before an item is deleted.

        :arg key: is the key of the item that is about to be deleted. It is okay to ``get()`` this key to interogate the properties of the item.
        """
        pass

    @classmethod
    def after_delete(cls, key):
        """
        Called after an item is deleted.

        :arg key: is the key of the item that was deleted. It is not possible to call ``get()`` on this key.
        """
        pass

    @classmethod
    def before_get(cls, key):
        """
        Called before an item is retrieved. Note that this does not occur for queries.

        :arg key: Is the key of the item that is to be retrieved.
        """
        pass

    @classmethod
    def after_get(cls, key, item):
        """
        Called after an item has been retrieved. Note that this does not occur for queries.

        :arg key: Is the key of the item that was retrieved.
        :arg item: Is the item itself.
        """
        pass

    # Impl details

    @classmethod
    def _invoke_behaviors(cls, method, *args, **kwargs):
        for b in cls.behaviors:
            getattr(b, method)(*args, **kwargs)

    def _pre_put_hook(self):
        self._invoke_behaviors('before_put', self)
        return self.before_put()

    def _post_put_hook(self, future):
        res = future.get_result()
        self._invoke_behaviors('after_put', self)
        return self.after_put(res)

    @classmethod
    def _pre_delete_hook(cls, key):
        cls._invoke_behaviors('before_delete', key)
        return cls.before_delete(key)

    @classmethod
    def _post_delete_hook(cls, key, future):
        cls._invoke_behaviors('after_delete', key)
        return cls.after_delete(key)

    @classmethod
    def _pre_get_hook(cls, key):
        cls._invoke_behaviors('before_get', key)
        return cls.before_get(key)

    @classmethod
    def _post_get_hook(cls, key, future):
        res = future.get_result()
        cls._invoke_behaviors('after_get', res)
        return cls.after_get(key, res)

    def __unicode__(self):
        if hasattr(self, 'name'):
            return self.name or super(Model, self).__str__()
        else:
            return super(Model, self).__str__()

    def __str__(self):
        return self.__unicode__()


class BasicModel(Model):
    """
    Adds the common properties created, created_by, modified, and modified_by to :class:`Model`
    """
    from argeweb.core.property import DateProperty, DateTimeProperty, FloatProperty
    created = DateTimeProperty(auto_now_add=True)
    #created_by = ndb.UserProperty(auto_current_user_add=True)
    modified = DateTimeProperty(auto_now=True)
    #modified_by = ndb.UserProperty(auto_current_user=True)
    sort = FloatProperty(default=0.0)

    @staticmethod
    def _get_dict_md5_(content):
        import hashlib
        import random
        try:
            m2 = hashlib.md5()
            m2.update(content)
            random.seed(m2.hexdigest())
        except:
            pass
        return str(int(time.time()*100) + random.randint(1, 799999999999))

    def delete(self):
        self.key.delete()

    def before_put(self):
        """
        Called before an item is saved.

        :arg self: refers to the item that is about to be saved
        :note: ``self.key`` is invalid if the current item has never been saved
        """
        if self.sort is None or self.sort == 0.0:
            self.sort = time.time()
        if hasattr(self, 'name'):
            if self.name == None or self.name == u'':
                self.name = self._get_dict_md5_(str(self.__dict__))
        for i in self._properties:
            item = self._properties[i]
            if isinstance(item, SearchingHelperProperty):
                target = self._properties[item._target]
                t = None
                target_ndb = None
                if isinstance(target, KeyProperty) or isinstance(target, CategoryProperty):
                    t = getattr(self, item._target)
                if t:
                    target_ndb = t.get()
                if target_ndb:
                    field = getattr(target_ndb, item._target_field_name)
                    setattr(self, i, field)
                else:
                    setattr(self, i, None)
        super(BasicModel, self).before_put()

    @classmethod
    def get_prev_one(cls, item):
        return cls.query(cls.sort > item.sort).order(cls.sort).get()

    @classmethod
    def get_next_one(cls, item):
        return cls.query(cls.sort < item.sort).order(-cls.sort).get()

    @classmethod
    def get_prev_one_with_category(cls, item, cat):
        c = ndb.Key(urlsafe=cat)
        if hasattr(cls, 'category'):
            return cls.query(cls.category == c, cls.sort > item.sort).order(cls.sort).get()
        else:
            return None

    @classmethod
    def get_next_one_with_category(cls, item, cat):
        c = ndb.Key(urlsafe=cat)
        if hasattr(cls, 'category'):
            return cls.query(cls.category == c, cls.sort < item.sort).order(-cls.sort).get()
        else:
            return None

    @classmethod
    def all(cls):
        """
        Queries all posts in the system, regardless of user, ordered by date created descending.
        """
        return cls.query().order(-cls.sort)

    @classmethod
    def all_enable(cls, *args, **kwargs):
        if hasattr(cls, 'is_enable') is False:
            return None
        cat = None
        if hasattr(cls, 'category') and 'category' in kwargs:
            category = kwargs['category']
            if isinstance(category, basestring):
                try:
                    cat_kind = eval(cls.category._kind)
                    cat = cat_kind.find_by_name(category)
                except:
                    return None
            else:
                cat = kwargs['category']
        if hasattr(cls, 'category') and 'category_key' in kwargs:
            category_key = kwargs['category_key']
            if isinstance(category_key, basestring):
                cat = ndb.Key(urlsafe=category_key)
            if isinstance(category_key, ndb.Key):
                cat = category_key.get()
        if cat is not None:
            if hasattr(cls, 'category') is False:
                return None
            return cls.query(cls.category == cat.key, cls.is_enable == True).order(-cls.sort)
        return cls.query(cls.is_enable == True).order(-cls.sort)

    @classmethod
    def find_by_name(cls, *args, **kwargs):
        name = None
        if len(args) > 0:
            name = str(args[0])
        if 'name' in kwargs:
            name = str(kwargs['name'])
        if hasattr(cls, 'name') and name is not None:
            return cls.query(cls.name == name).get()
        else:
            return None

    @classmethod
    def find_by_title(cls, title):
        if hasattr(cls, 'title'):
            return cls.query(cls.title == title).get()
        else:
            return None

    @classmethod
    def find_or_create_by_name(cls, name):
        item = cls.find_by_name(name)
        if item is None:
            item = cls()
            item.name = name
            item.put()
        return item

    @classmethod
    def has_record(cls):
        r = cls.query().get()
        if r is not None:
            return True
        else:
            return False

    @classmethod
    def get_default_display_in_form(cls):
        field_name = {
            'created': u'建立時間',
            'modified': u'修改時間',
            'sort': u'排序值',
            'is_enable': u'啟用'
        }
        display_in_form = []
        for name, model_property in cls._properties.items():
            display_in_form.append(name)
            if model_property._verbose_name is not None:
                field_name[name] = model_property._verbose_name
        return field_name, sorted(display_in_form)

    @classmethod
    def get_tab_pages(cls):
        try:
            if hasattr(cls.Meta, 'tab_pages'):
                return cls.Meta.tab_pages
        except AttributeError:
            pass
        return []

    @classmethod
    def get_tab_pages_fields(cls):
        tab_pages_list = {}
        max_tab_pages = 0
        tab_pages = cls.get_tab_pages()
        for name, model_property in cls._properties.items():
            if model_property._tab_page_index is None:
                tab_pages_list["0"].append(name)
            else:
                if str(model_property._tab_page_index) not in tab_pages_list:
                    tab_pages_list[str(model_property._tab_page_index)] = []
                tab_pages_list[str(model_property._tab_page_index)].append(name)
                if int(model_property._tab_page_index) > max_tab_pages:
                    max_tab_pages = int(model_property._tab_page_index)

        try:
            if hasattr(cls.Meta, 'tab_pages'):
                if max_tab_pages < len(tab_pages) - 1:
                    max_tab_pages = len(tab_pages) - 1
                for i in xrange(0, max_tab_pages + 1):
                    if str(i) not in tab_pages_list:
                        tab_pages_list[str(i)] = []
        except AttributeError:
            pass

        tab_pages_list_real = range(0, max_tab_pages+1)
        for item in tab_pages_list:
            tab_pages_list_real[int(item)] = tab_pages_list[item]
        return tab_pages_list_real
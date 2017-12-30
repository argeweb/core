#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes that extend the basic ndb.Model classes
"""
from google.appengine.ext import ndb
from google.appengine.ext.ndb import KindError
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
                    if hasattr(cls, '_fix_up_kind_map'):
                        cls._fix_up_kind_map()
                    args = {}
                    args[name] = value
                    return cls.find_all_by_properties(**args)
                return types.MethodType(find_all, cls)

            if not find_all_name in dct:
                setattr(cls, find_all_name, bind_all(prop_name))

            find_one_name = 'find_by_' + prop_name

            def bind_one(name):
                def find_one(cls, value):
                    if hasattr(cls, '_fix_up_kind_map'):
                        cls._fix_up_kind_map()
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
        cls._fix_up_kind_map()
        query = cls.query()
        for name, value in kwargs.items():
            property = cls._properties[name]
            query = query.filter(property == value)
        return query

    @classmethod
    def find_by_properties(cls, *args, **kwargs):
        """
        Similar to find_all_by_properties, but returns either None or a single ndb.Model instance.

        Example::

            User.find_by_properties(first_name='Jon',role='Admin')

        """
        cls._fix_up_kind_map()
        if len(args) > 0 and 'name' not in kwargs:
            kwargs['name'] = args[0]
        return cls.find_all_by_properties(**kwargs)

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
    def _fix_up_kind_map(cls):
        cls._kind_map[cls.__name__] = cls

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
        cls._kind_map[cls.__name__] = cls
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
    from argeweb.core.property import DateProperty, DateTimeProperty, FloatProperty, HiddenProperty
    name = HiddenProperty(verbose_name=u'識別名稱')
    created = DateTimeProperty(verbose_name=u'建立時間', auto_now_add=True)
    created_time = FloatProperty(verbose_name=u'建立時間sp', default=0.0)
    modified = DateTimeProperty(verbose_name=u'修改時間', auto_now=True)
    modified_time = FloatProperty(verbose_name=u'修改時間sp', default=0.0)
    sort = FloatProperty(verbose_name=u'排序值', default=0.0)

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
        if self.created_time is None or self.created_time == 0.0:
            self.created_time = self.sort
        self.modified_time = time.time()
        if self.name is None or self.name == u'':
            from ..random_util import gen_dict_md5
            self.name = gen_dict_md5(str(self.__dict__))
        for i in self._properties:
            item = self._properties[i]
            if hasattr(item, 'process_before_put'):
                item.process_before_put(self, i)
        self.kind_name = self._get_kind_name()
        super(BasicModel, self).before_put()

    def after_put(self, key):
        pass
        # 資料變更監看功能 (為了維持 key 及其相關的資料，如 分類與其下的產品)
        # if not hasattr(self.Meta, 'stop_data_watcher') and not hasattr(self, '__stop_update__') and self.__module__ not in [
        #     'argeweb.core.model',
        #     'plugins.code.models.code_model',
        #     'plugins.file.models.file_model',
        # ]:
        #     from ..model import DataUpdater
        #     updater = DataUpdater.find_by_properties(updater=self.key).get()
        #     if updater is None:
        #         updater = DataUpdater(updater=self.key)
        #     updater.need_updater = True
        #     updater.cursor = None
        #     updater.put()

    @classmethod
    def _get_kind_name(cls):
        return '%s.%s' % (cls.__module__, str(cls._class_name.im_self).split('<')[0])

    @classmethod
    def _check_kind_name(cls, key, item):
        # TODO 刪除?
        if item and item.kind_name is not None and item.kind_name != cls._get_kind_name():
            try:
                n = item.kind_name.split('.')
                exec 'from %s import %s as TargetConfigModel' % ('.'.join(n[:-1]), n[-1])
            except (ImportError, AttributeError):
                pass
            cls._fix_up_kind_map()

    def get_prev_one(self):
        kind_name = str(self.key).split('\'')[1]
        cls = self._kind_map[kind_name]
        return cls.query(cls.sort > self.sort).order(cls.sort).get()

    def get_next_one(self):
        kind_name = str(self.key).split('\'')[1]
        cls = self._kind_map[kind_name]
        return cls.query(cls.sort < self.sort).order(-cls.sort).get()

    def get_prev_one_with_enable(self):
        kind_name = str(self.key).split('\'')[1]
        cls = self._kind_map[kind_name]
        if hasattr(cls, 'is_enable'):
            return cls.query(cls.is_enable == True, cls.sort > self.sort).order(cls.sort).get()
        return None

    def get_next_one_with_enable(self):
        kind_name = str(self.key).split('\'')[1]
        cls = self._kind_map[kind_name]
        if hasattr(cls, 'is_enable'):
            return cls.query(cls.is_enable == True, cls.sort < self.sort).order(-cls.sort).get()
        return None

    @classmethod
    def get_prev_one_with_category(cls, item, cat):
        cls._fix_up_kind_map()
        c = ndb.Key(urlsafe=cat)
        if hasattr(cls, 'category'):
            return cls.query(cls.category == c, cls.sort > item.sort).order(cls.sort).get()
        else:
            return None

    @classmethod
    def get_next_one_with_category(cls, item, cat):
        cls._fix_up_kind_map()
        c = ndb.Key(urlsafe=cat)
        if hasattr(cls, 'category'):
            return cls.query(cls.category == c, cls.sort < item.sort).order(-cls.sort).get()
        else:
            return None

    @classmethod
    def all(cls, *args, **kwargs):
        """
        Queries all posts in the system, regardless of user, ordered by date created descending.
        """
        cls._fix_up_kind_map()
        return cls.query().order(-cls.sort)

    @classmethod
    def all_enable(cls, *args, **kwargs):
        cls._fix_up_kind_map()
        if hasattr(cls, 'is_enable') is False:
            return None
        cat_key = None
        if hasattr(cls, 'category') and 'category' in kwargs:
            category = kwargs['category']
            if isinstance(category, basestring):
                try:
                    cat_kind = eval(cls.category._kind)
                    cat = cat_kind.get_by_name(category)
                    cat_key = cat.key
                except:
                    return None
            else:
                try:
                    cat_key = category.key
                except:
                    cat_key = category
        if hasattr(cls, 'category') and 'category_key' in kwargs:
            category_key = kwargs['category_key']
            if isinstance(category_key, basestring):
                cat_key = ndb.Key(urlsafe=category_key)
            if isinstance(category_key, ndb.Key):
                cat_key = category_key
        if cat_key is not None:
            if hasattr(cls, 'category') is False:
                return None
            return cls.query(cls.category == cat_key, cls.is_enable == True).order(-cls.sort)
        return cls.query(cls.is_enable == True).order(-cls.sort)

    @classmethod
    def get_by_name(cls, *args, **kwargs):
        find_item = cls.find_by_name(*args, **kwargs)
        if find_item is not None:
            return find_item.get()

    @classmethod
    def find_by_name(cls, *args, **kwargs):
        cls._fix_up_kind_map()
        name = None
        if len(args) > 0:
            name = str(args[0])
        if 'name' in kwargs:
            name = str(kwargs['name'])
        if hasattr(cls, 'name') and name is not None:
            return cls.query(cls.name == name)
        else:
            return None

    @classmethod
    def get_by_name_async(cls, *args, **kwargs):
        cls._fix_up_kind_map()
        name = None
        if len(args) > 0:
            name = str(args[0])
        if 'name' in kwargs:
            name = str(kwargs['name'])
        if hasattr(cls, 'name') and name is not None:
            return cls.query(cls.name == name).get_async()
        else:
            return None

    @classmethod
    def get_or_create_by_name(cls, name, *args, **kwargs):
        cls._fix_up_kind_map()
        item = cls.get_by_name(name)
        if item is None:
            item = cls.create_record(name, *args, **kwargs)
        return item

    @classmethod
    def create_record(cls, name, *args, **kwargs):
        item = cls()
        item.name = name
        for filed_name in kwargs:
            if hasattr(item, filed_name):
                setattr(item, filed_name, kwargs[filed_name])
        item.put()
        return item

    @classmethod
    def has_record(cls):
        cls._fix_up_kind_map()
        r = cls.query().get()
        if r is not None:
            return True
        else:
            return False

    @classmethod
    def get_default_display_in_form(cls):
        cls._fix_up_kind_map()
        field_verbose_names = {
            'is_enable': u'啟用',
            'kind_name': u'類別名稱',
        }
        display_in_form = []
        for name, model_property in cls._properties.items():
            if name not in ['sort', 'kind_name', 'created', 'modified', 'created_time', 'modified_time']:
                display_in_form.append(name)
            if model_property._verbose_name is not None:
                field_verbose_names[name] = model_property._verbose_name
        return field_verbose_names, sorted(display_in_form)

    @classmethod
    def get_tab_pages(cls):
        cls._fix_up_kind_map()
        try:
            if hasattr(cls.Meta, 'tab_pages'):
                return cls.Meta.tab_pages
        except AttributeError:
            pass
        return []

    @classmethod
    def get_tab_pages_fields(cls):
        cls._fix_up_kind_map()
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


class BasicConfigModel(BasicModel):
    @classmethod
    def get_config(cls):
        return cls.get_or_create_by_name(str(cls.__module__).split('.')[1]+'_config')

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2016/10/10
from argeweb.core.ndb import Model, BasicModel, ndb
from argeweb.core import property as Fields
from datetime import datetime, timedelta


class HostInformationModel(BasicModel):
    host = Fields.StringProperty(required=True, verbose_name=u'域名')
    namespace = Fields.StringProperty(required=True, verbose_name=u'命名空間')
    site_name = Fields.StringProperty(verbose_name=u'網站名稱')
    plugins = Fields.TextProperty(verbose_name=u'模組')
    theme = Fields.StringProperty(verbose_name=u'主題樣式')
    space_rental_level = Fields.StringProperty(verbose_name=u'伺服器等級', choices=(
        'F1', 'F2', 'F4'
    ), default='F1')
    space_rental_price = Fields.StringProperty(verbose_name=u'空間費用', default=u'8000')
    space_rental_date = Fields.DateProperty(verbose_name=u'空間租借日', default=datetime.today())
    space_expiration_date = Fields.DateProperty(verbose_name=u'空間到期日', default=datetime.today() + timedelta(days=100))
    is_lock = Fields.BooleanProperty(verbose_name=u'是否鎖定', default=True)
    use_real_template_first = Fields.BooleanProperty(verbose_name=u'優先使用實體樣版', default=True)
    use_application_template_first = Fields.BooleanProperty(verbose_name=u'優先使用應用程式樣版', default=False)
    view_cache = Fields.BooleanProperty(verbose_name=u'緩存虛擬樣版文件', default=True)

    @property
    def plugins_list(self):
        return str(self.plugins).split(',')

    def has_plugin(self, plugin_name):
        return plugin_name in self.plugins_list

    @classmethod
    def get_by_host(cls, host):
        return cls.query(cls.host == host).get()

    @classmethod
    def get_by_host_async(cls, host):
        return cls.query(cls.host == host).get_async()

    @classmethod
    def get_by_namespace(cls, namespace):
        return cls.query(cls.namespace == namespace).get()

    @classmethod
    def get_or_insert(cls, host, theme=None, plugins=None, is_lock=True):
        item = cls.get_by_host(host)
        if item is None:
            import random, string
            item = cls()
            item.host = host
            r = ''.join(random.choice(string.lowercase) for i in range(25))
            item.namespace = u'%s-%s-%s-%s' % (r[0:4], r[5:9], r[10:14], r[15:19])
            item.theme = theme if theme is not None else u''
            item.plugins = plugins if plugins is not None else u''
            item.is_lock = is_lock
            item.put()
        return item

    def before_put(self):
        super(HostInformationModel, self).before_put()
        sn = []
        for n in self.plugins.split(','):
            if n.find('.') < 0:
                sn.append('plugins.%s' % n)
            else:
                sn.append(n)
        self.plugins = ','.join(sn)

    def after_put(self, key):
        from argeweb.core.settings import set_memcache_in_shared
        set_memcache_in_shared('host.information.%s' % self.host, self, self.namespace)

    @classmethod
    def after_get(cls, key, item):
        from argeweb.core.settings import set_memcache_in_shared
        set_memcache_in_shared('host.information.%s' % item.host, item, item.namespace)


class WebSettingModel(BasicModel):
    setting_name = Fields.StringProperty(verbose_name=u'名稱')
    setting_key = Fields.StringProperty(required=True, verbose_name=u'鍵')
    setting_value = Fields.StringProperty(required=True, verbose_name=u'值')

    @classmethod
    def get_by_key(cls, key):
        return cls.query(cls.setting_key == key).get()

    @classmethod
    def get_or_insert(cls, key, default):
        item = cls.query(cls.setting_key == key).get()
        if item is None:
            item = cls()
            item.setting_key = key
            item.setting_value = default
            item.put()
        return item


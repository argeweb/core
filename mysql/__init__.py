#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2018/4/3

try:
    import MySQLdb
except ImportError:
    pass
from google.appengine.api import rdbms
import os


class CloudSQL(object):
    def __init__(self, controller):
        """ easy way to get param from request

        Args:
            key: the key to get from request
            default_value: then value not exits return
        """
        self.__sql_cursor__ = None
        self.__sql_connect__ = None
        self.controller = controller
        config = controller.host_information
        controller.logging.info(config)
        if config.is_dev_server:
            if config.cloud_sql_database_ip is not None:
                self.use(config.cloud_sql_instance_name, config.cloud_sql_database, True,
                         config.cloud_sql_database_ip, "root", config.cloud_sql_database_password)
            else:
                self.use(config.cloud_sql_instance_name, config.cloud_sql_database, True)
        else:
            if config.cloud_sql_database_password is not None:
                self.use(config.cloud_sql_instance_name, config.cloud_sql_database, False,
                         config.cloud_sql_database_ip, "root", config.cloud_sql_database_password)
            else:
                self.use(config.cloud_sql_instance_name, config.cloud_sql_database)

    def use(self, cloud_sql_instance_name, cloud_sql_database, is_dev_appserver=False, sql_ip="173.194.250.158", sql_user="root", sql_password="1234"):
        has_sql = True
        if is_dev_appserver:
            try:
                self.__sql_connect__ = rdbms.connect(instance=cloud_sql_instance_name, db=cloud_sql_database,
                                                     port=3306, host=sql_ip,  user=sql_user, password=sql_password, charset='utf8')
            except:
                try:
                    self.__sql_connect__ = rdbms.connect(instance=cloud_sql_instance_name, db=cloud_sql_database,
                                                         port=3306, host=sql_ip,  user=sql_user, password='', charset='utf8')
                except TypeError:
                    has_sql = False
                    self.controller.logging.debug('cloud sql not working')
        else:
            try:
                self.__sql_connect__ = rdbms.connect(instance=cloud_sql_instance_name, db=cloud_sql_database, user=sql_user, password=sql_password)
            except:
                try:
                    self.__sql_connect__ = rdbms.connect(instance=cloud_sql_instance_name, db=cloud_sql_database, user=sql_user, password="")
                except:
                    has_sql = False
                    self.controller.logging.debug('cloud sql not working')

        if has_sql:
            self.__sql_connect__.autocommit(True)
            #self.__sql_connect__.set_character_set('Unicode')
            self.__sql_cursor__ = self.__sql_connect__.cursor()
            self.cursor = self.__sql_cursor__

    def autocommit(self, value=True):
        self.__sql_connect__.autocommit(value)

    def commit(self):
        self.__sql_connect__.commit()

    def close(self):
        if self.__sql_cursor__ is not None:
            self.__sql_cursor__.close()
            self.__sql_connect__.close()

    def update(self, table_name, new_params=None, where_params=None):
        if not new_params:
            new_params = {}
        str_new_key = []
        str_new_val = []
        str_where = []
        for key, value in new_params.items():
            str_new_key.append(key + ' = %s')
            str_new_val.append(value)
        for key, value in where_params.items():
            str_where.append(key + ' = %s')
            str_new_val.append(value)
        str_sql = 'UPDATE %s SET %s WHERE %s' % (table_name, (",".join(str(x) for x in str_new_key)), (" and ".join(str(x) for x in str_where)))
        self.__sql_cursor__.execute(str_sql, str_new_val)

    def insert(self, table_name, params=None):
        str_key = []
        str_temp_val = []
        str_val = []
        for key, value in params.items():
            str_key.append(key)
            str_temp_val.append('%s')
            str_val.append(value)
        str_sql = 'INSERT INTO %s ( %s ) VALUES ( %s )' % (table_name, (",".join(str(x) for x in str_key)), (",".join(str(x) for x in str_temp_val)))
        self.controller.logging.info(str_sql)
        self.__sql_cursor__.execute(str_sql, str_val)
        try:
            return int(self.__sql_cursor__.lastrowid)
        except:
            return 0

    def insert_many(self, table_name, fields, values):
        field_list = fields.split(",")
        str_temp_val = []
        for i in field_list:
            str_temp_val.append('%s')
        str_sql = 'INSERT INTO %s ( %s ) VALUES ( %s )' % (table_name, fields, (",".join(str(x) for x in str_temp_val)))
        self.controller.logging.info(str_sql)
        self.__sql_cursor__.executemany(str_sql, values)

    def query_by_id(self, table_name, id):
        return self.query_one('select * from ' + table_name + ' where id = %s', id)

    def query(self, query, row_id=0):
        self.__sql_cursor__.execute(query)
        temp_result = self.__sql_cursor__.fetchall()
        result = []
        for item in temp_result:
            item_temp = {}
            row_id += 1
            item_temp["row_id"] = row_id
            c = 0
            for column in self.__sql_cursor__.description:
                item_temp[column[0]] = item[c]
                if column[0].startswith("is_"):
                    item_temp[column[0]] = (item_temp[column[0]] == 1)
                if column[0] == "id":
                    item_temp["recid"] = item_temp[column[0]]
                if item_temp[column[0]] is None or item_temp[column[0]] is "None":
                    item_temp[column[0]] = ""
                c += 1
            result.append(item_temp)
        return result

    def query_all(self, query, params=(), row_id=0):
        if params is ():
            self.__sql_cursor__.execute(query)
        else:
            self.__sql_cursor__.execute(query, params)
        temp_result = self.__sql_cursor__.fetchall()
        result = []
        for item in temp_result:
            item_temp = {}
            row_id += 1
            item_temp["row_id"] = row_id
            c = 0
            for column in self.__sql_cursor__.description:
                item_temp[column[0]] = item[c]
                if column[0].startswith("is_"):
                    item_temp[column[0]] = (item_temp[column[0]] == 1)
                if column[0] == "id":
                    item_temp["recid"] = item_temp[column[0]]
                if item_temp[column[0]] is None or item_temp[column[0]] is "None":
                    item_temp[column[0]] = ""
                c += 1
            result.append(item_temp)
        return result

    def query_one(self, query, params=()):
        if params is ():
            self.__sql_cursor__.execute(query)
        else:
            self.__sql_cursor__.execute(query, params)
        temp_result = self.__sql_cursor__.fetchone()
        if temp_result is not None:
            result = {}
            c = 0
            for column in self.__sql_cursor__.description:
                result[column[0]] = temp_result[c]
                if column[0].startswith("is_"):
                    result[column[0]] = (result[column[0]] == 1)
                if column[0] == "id":
                    result["recid"] = result[column[0]]
                if result[column[0]] is None or result[column[0]] is "None":
                    result[column[0]] = ""
                c += 1
            return result
        else:
            return None

    def query_many(self, query, size, params=(), row_id=0):
        if params is ():
            self.__sql_cursor__.execute(query)
        else:
            self.__sql_cursor__.execute(query, params)
        temp_result = self.__sql_cursor__.fetchmany(size)
        result = []
        for item in temp_result:
            item_temp = {}
            row_id += 1
            item_temp["row_id"] = row_id
            c = 0
            for column in self.__sql_cursor__.description:
                item_temp[column[0]] = item[c]
                if column[0].startswith("is_"):
                    item_temp[column[0]] = (item_temp[column[0]] == 1)
                if column[0] == "id":
                    item_temp["recid"] = item_temp[column[0]]
                if item_temp[column[0]] is None or item_temp[column[0]] is "None":
                    item_temp[column[0]] = ""
                c += 1
            result.append(item_temp)
        return result

    def delete(self, table_name, where_params=None):
        str_new_val = []
        str_where = []
        for key, value in where_params.items():
            str_where.append(key + ' = %s')
            str_new_val.append(value)
        str_sql = 'DELETE FROM %s WHERE %s' % (table_name, (" and ".join(str(x) for x in str_where)))
        self.__sql_cursor__.execute(str_sql, str_new_val)

    def delete_all(self, table_name):
        str_sql = 'DELETE FROM %s' % table_name
        self.__sql_cursor__.execute(str_sql)

    def pager(self, query, params=(), size=10):
        if params is ():
            self.__sql_cursor__.execute(query)
        else:
            self.__sql_cursor__.execute(query, params)
        result = self.__sql_cursor__.fetchone()
        all_record = 0
        try:
            all_record = int(result[0])
        finally:
            return int((all_record + size - 1) / size)

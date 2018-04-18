#!/usr/bin/env python
# -*- coding: utf-8 -*-
config_name = 'banner'
eval ('from plugins.%s.models.config_model import ConfigModel as config_model' % config_name, globals())
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import os
from template import render_template
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')


def generic_handler(code, template=None):
    if not template:
        template = '%s' % code
    template = (
        'base.html',
        'layout.html',
        'errors/%s.html' % template,
        'templates/errors/%s.html' % code,
        'templates/errors/500.html'
    )

    def inner(request, response, exception):
        logging.exception(exception)
        response.set_status(code)
        if request.path.find('/admin') == 0:
            is_backend = True
        else:
            is_backend = False
        if 'application/json' in request.headers.get('Accept', []) or request.headers.get('Content-Type') == 'application/json':
            if hasattr(response, 'data'):
                data = response.data
            else:
                try:
                    error_message = str(exception)
                except UnicodeEncodeError:
                    error_message = str(exception.encode('utf-8'))
                data = {
                    'error': error_message,
                    'code': code
                }
            response.text = unicode(json.dumps(data, encoding='utf-8', ensure_ascii=False))
        else:
            pass
            # from argeweb.core import settings
            # host_information, namespace, theme, server_name = settings.get_host_information_item()
            # response.content_type = 'text/html; charset=UTF-8'
            # response.text = render_template(
            #     name=template,
            #     context={'request': request, 'exception': exception, 'code': code, 'is_backend': is_backend},
            #     theme=theme)

    return inner


handle_400 = generic_handler(400)
handle_401 = generic_handler(401)
handle_403 = generic_handler(403)
handle_404 = generic_handler(404)
handle_500 = generic_handler(500)

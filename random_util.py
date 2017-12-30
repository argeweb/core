#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import hashlib
import random
import time


def gen_random_code(code_length=16, code_type='letters', split_length=4, split_word='-'):
    code_length_max = code_length + 10

    s = ''
    if hasattr(string, code_type):
        s = getattr(string, code_type)
    if s is '':
        if code_type is 'letters+digits':
            s = string.letters + string.digits
    if s is '':
        s = string.letters + string.digits
    r = ''.join(random.choice(s) for i in range(code_length_max))

    if split_length is 0:
        return r[:code_length]

    n = int(code_length / split_length)
    if n * split_length < code_length:
        n += 1
    na = n * split_length - code_length
    ns = []
    for i in xrange(0, n):
        s1 = i * split_length + 1
        s2 = s1 + split_length
        ns.append(r[s1:s2])
    s = split_word.join(ns)
    return s[:len(s)-na]


def gen_dict_md5(dict):
    try:
        m2 = hashlib.md5()
        m2.update(dict)
        random.seed(m2.hexdigest())
    except:
        pass
    return str(int(time.time() * 100) + random.randint(1, 799999999999))

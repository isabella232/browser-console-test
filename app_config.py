#!/usr/bin/env python
# _*_ coding:utf-8 _*_
TESTS_LOAD_WAIT_TIME = 2
try:
    from local_settings import TESTS_LOAD_WAIT_TIME
except ImportError:
    pass

# URL ID EXTRACTION PATTERN
URL_ID_PATTERN = r'(?:/|storyId=)(\d{9})/?'
try:
    from local_settings import URL_ID_PATTERN
except ImportError:
    pass

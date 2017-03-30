#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import os
import logging
import datetime
import re
import time
import csv
import app_config
from fabric.api import task
from distutils.util import strtobool
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

"""
Logging
"""
LOG_FORMAT = '%(levelname)s:%(name)s:%(asctime)s: %(message)s'
LOG_LEVEL = logging.INFO

# GLOBAL SETTINGS
cwd = os.path.dirname(__file__)
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def _prep_bool_arg(arg):
    """
    Util to parse fabric boolean args
    """
    return bool(strtobool(str(arg)))


def _safe_unicode(obj, * args):
    """ return the unicode representation of obj """
    try:
        return unicode(obj, * args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return unicode(ascii_text)


def _safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')


def _choose_web_driver(use):
    """
    Choose the webdriver to use
    """
    driver = None
    if use.lower() == 'phantom':
        logger.info("Phantomjs webdriver selected")
        driver = webdriver.PhantomJS()
        driver.set_window_size(1280, 1024)
    else:
        logger.info("Chrome webdriver selected")
        d = DesiredCapabilities.CHROME.copy()
        d['loggingPrefs'] = {'browser': 'ALL'}
        driver = webdriver.Chrome(desired_capabilities=d)
    return driver


@task(default=True)
def test(*urls, **kwargs):
    """
    Test one or multiple graphics looking for browser warnings and errors
    Using selenium & chrome webdriver
    """
    use = kwargs.get('use', 'Chrome')
    screenshot = kwargs.get('screenshot', True)
    screenshot = _prep_bool_arg(screenshot)
    if urls[0] == '':
        print 'You must specify a url "test:url" or "test:url1,url2"'
        return

    for url in urls:
        test_single(url, use=use, screenshot=screenshot)


@task
def test_single(url, use='Chrome', screenshot=True):
    """
    Test a graphic looking for browser warnings and errors
    Using selenium & chrome webdriver
    """
    screenshot = _prep_bool_arg(screenshot)
    # Timestamp of the test
    ts = re.sub(r'\..*', '', str(datetime.datetime.now()))
    ts = re.sub(r'[\s:-]', '_', ts)
    log_content = []
    url_pattern = re.compile(app_config.URL_ID_PATTERN)
    logger.info('url: %s' % url)
    OUTPUT_PATH = os.path.join(cwd, 'test')
    # Create output files folder if needed
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    driver = _choose_web_driver(use)
    try:
        if re.match(r'^https?://', url):
            m = url_pattern.search(url)
            if m:
                slug = m.group(1)
            else:
                slug = ts
        else:
            logger.error('This does not look like a url %s' % url)
            exit(1)
        driver.get(url)
        time.sleep(app_config.TESTS_LOAD_WAIT_TIME)
        log = driver.get_log('browser')
        if not log:
            logger.info("Test was successful")
        else:
            log_content.append(['id', 'level', 'message'])
            for entry in log:
                clean_message = u'%s' % (
                    _safe_unicode(_safe_str(entry['message'])))
                clean_message = clean_message.replace('\n', '')
                line = [slug, entry['level'], clean_message]
                log_content.append(line)
                if entry['level'] == 'ERROR':
                    logger.error("Reason %s" % clean_message)
                elif entry['level'] == 'WARNING':
                    logger.warning("Reason %s" % clean_message)
                else:
                    logger.info("Found some console.log output %s" % (
                        clean_message))
    finally:
        if screenshot:
            driver.save_screenshot('%s/%s.png' % (OUTPUT_PATH,
                                                  slug))
        driver.quit()
        if log_content:
            with open('%s/%s.log' % (OUTPUT_PATH,
                                     slug), 'w') as writefile:
                writer = csv.writer(writefile, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(log_content)


@task
def bulk_test(csvpath, use='Chrome', screenshot=True):
    """
    Test graphics browser warnings & errors -- use batch for multiple graphics
    Using selenium & chrome webdriver
    """
    screenshot = _prep_bool_arg(screenshot)
    fname = os.path.basename(csvpath)
    # Assume that a filepath is given read contents and clean them
    with open(csvpath, 'r') as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    # Timestamp of the test
    ts = re.sub(r'\..*', '', str(datetime.datetime.now()))
    ts = re.sub(r'[\s:-]', '_', ts)
    log_content = [['url', 'level', 'message']]
    url_pattern = re.compile(app_config.URL_ID_PATTERN)
    OUTPUT_PATH = os.path.join(cwd, 'test/%s' % ts)
    # Create output files folder if needed
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    driver = _choose_web_driver(use)
    try:
        for ix, item in enumerate(content):
            url = item
            if re.match(r'^https?://', item):
                m = url_pattern.search(item)
                if m:
                    slug = m.group(1)
                else:
                    slug = 'line%s' % (ix + 1)
            else:
                logger.error('This does not look like a url %s' % url)
                line = [url, 'ERROR', 'Not wellformed url']
                log_content.append(line)
                continue
            logger.info('url: %s' % url)
            driver.get(url)
            time.sleep(app_config.TESTS_LOAD_WAIT_TIME)
            # Get browser log and parse output
            log = driver.get_log('browser')
            if not log:
                logger.info("%s - Test successful" % (slug))
                line = [url, 'SUCCESS', 'Test successful with no logs']
                log_content.append(line)
            else:
                logger.warning("%s - Test found issues. Check log" % (
                    slug))
                for entry in log:
                    clean_message = u'%s' % (
                        _safe_unicode(_safe_str(entry['message'])))
                    clean_message = clean_message.replace('\n', '')
                    line = [url, entry['level'], clean_message]
                    log_content.append(line)

            # Save screenshot
            if screenshot:
                driver.save_screenshot('%s/%s.png' % (OUTPUT_PATH,
                                                      slug))
    finally:
        driver.quit()
        if log_content:
            with open('%s/test-%s' % (OUTPUT_PATH, fname), 'w') as writefile:
                writer = csv.writer(writefile, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(log_content)

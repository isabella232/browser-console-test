Browser Console Test
====================

* [What Is This?](#what-is-this)
* [Assumptions](#assumptions)
* [What's In Here?](#whats-in-here)
* [Bootstrap the project](#bootstrap-the-project)
* [Running Tests](#running-tests)

What is this?
-------------

`browser-console-test` is a repo that allows you to test webpages searching for
javascript console logging.

Assumptions
-----------

The following things are assumed to be true in this documentation.

* You are running OSX.
* You are using Python 2.7. (Probably the version that came with OSX.)
* You have [virtualenv](https://pypi.python.org/pypi/virtualenv) and [virtualenvwrapper](https://pypi.python.org/pypi/virtualenvwrapper) installed and working.
* You have your Amazon Web Services credentials stored as environment variables locally.

For more details on the technology stack used with this project, see our [development environment blog post](http://blog.apps.npr.org/2013/06/06/how-to-setup-a-developers-environment.html).

What's In Here?
---------------

The project contains the following folders and important files:

* ``fabfile.py`` -- [Fabric](http://docs.fabfile.org/en/latest/) commands for launching the tests
* ``app_config.py`` -- Global project configuration for scripts.
* ``requirements.txt`` -- Python requirements.

Bootstrap the project
---------------------

```
cd browser-console-test
mkvirtualenv browser-console-test
pip install -r requirements.txt
fab -l
```

**Problems installing requirements?** You may need to run the pip command as ``ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future pip install -r requirements.txt`` to work around an issue with OSX.

Running Tests
-------------

#### Installation

At NPR, we recently had to update all of our past graphics to faciltate the site's switch to `https`. We have introduced test capabilities to trim down the review process for this project -- but this functionality can and probably should be a part of our regular deployment.

Our basic test functionality uses [selenium for python](http://selenium-python.readthedocs.io/) and [chrome webdriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) to launch and validate the deployment url for a graphic or multiple graphics. The process makes a screenshot of the Chrome page and writes a log of the warnings, errors and ```console.log()``` statements that we may find.

* Selenium is included in our `requirements.txt`.

* To use [chrome webdriver](https://sites.google.com/a/chromium.org/chromedriver/downloads), download and unzip the corresponding version for your platform and put it somewhere on the `$PATH` so that selenium can find it. (You could include the path to the binary on the webdriver call but let's stick to only one approach.)

As an alternative to `chrome-webdriver`, you can use [phantomjs](http://phantomjs.org/). However, we have found that the browser logging granularity is a bit worse. To install phantomjs:

```
$ brew install phantomjs
```

There are other drivers ([see here](http://selenium-python.readthedocs.io/installation.html#drivers)) that you could use, and it should be quite straightforward to modify the code to do that. Since this is not intended as a cross-browser test, sticking to one browser serves our needs.

#### Test Deployment

Once you have installed the needed binaries and libraries we are ready to start testing.

The main entry point is a fabric task:

```
fab test:url
```

You could do them on more than one url by separating urls with commas

```
fab test:url1,url2
```

If you need/want to run the test on more than a couple of urls we have you covered, you can use the `bulk_test` fabric task

```
fab bulk_test:$CSVPATH
```

`$CSVPATH` is an absolute or relative path to the location of a csv file that will have either one url per line.

As a result the test rig will create a screenshot and a logfile for each url inside `test` folder. If `bulk_test` is used it will create a subfolder with the timestamp and inside it it will create a logfile for all the process and a screenshot for each graphic.

#### Fine-Tuning Tests

All the fabric tasks mentioned above have some behavior that can be customized:

* `use`: Which webdriver to use on the tests, defaults to `Chrome`
* `screenshot`: Whether to make a screenshot or not of the tested page, defaults to `True`

Let's say we have installed phantomjs and want to test using that webdriver, we could run:

```
$ fab test:url,use='phantom'
```

Let's say we do not want a screenshot to be taken for one of our bulk tests:

```
$ fab bulk_test:$CSVPATH,screenshot=False
```


#### Naming result files for the tests

We need to somehow identify each test on bulk tests and also for naming purposes in single tests. For that purpose we use `URL_ID_PATTERN` inside `app_config.py` which will be used as a RegExp pattern to extract an **identifier** from a given url. The default value can be used inside NPR for extracting a unique identifier from our CMS generated urls.

You can override this behavior by changing the `URL_ID_PATTERN` directly on the `app_config.py` or if you do not want to change code for that configuration, you can create `local_settings.py` to override the behavior for a given test run. `local_settings.py` is ignored by git.

If a pattern is not detected on the url for simple tests a formatted timestamp of the execution will be used to name the output files, for bulk tests the line number will be used for screenshot filenames if needed.

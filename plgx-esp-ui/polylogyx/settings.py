# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import datetime as dt
import os
import pika
from os.path import dirname, join, abspath


def get_ini_config(file_path):
    import configparser
    config_dict = {}
    config = configparser.ConfigParser()
    config.read(file_path)
    for section in config.sections():
        for key, value in config[section].items():
            config_dict[key] = value
    return config_dict


class RabbitConfig:
    max_wait_time = 60 * 10
    inactivity_timeout = 30


class Config(object):
    EMAIL_RECIPIENTS = []
    SECRET_KEY = '744463b9d4cf3d8e61e7dc5dc52718dd60cf76fb'

    # Set the following to ensure Celery workers can construct an
    # external URL via `url_for`.
    # SERVER_NAME = "localhost:9000"

    # PREFERRED_URL_SCHEME will not work without SERVER_NAME configured,
    # so we need to use SSLify extension for that.
    # By default it is enabled for all production configs.
    SERVER_PORT = 9000
    PREFERRED_URL_SCHEME = "https"
    ENFORCE_SSL = False
    DEBUG = False
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Flask-Authorize configuration
    AUTHORIZE_MODEL_PARSER = 'table'
    AUTHORIZE_DEFAULT_ACTIONS = ['create', 'delete', 'read', 'update']
    AUTHORIZE_DEFAULT_RESTRICTIONS = []
    AUTHORIZE_DEFAULT_ALLOWANCES = ['create', 'delete', 'read', 'update']
    AUTHORIZE_IGNORE_PROPERTY = '__check_access__'
    AUTHORIZE_ALLOW_ANONYMOUS_ACTIONS = False
    AUTHORIZE_DISABLE_JINJA = False

    DEFAULT_ROLES = {1: 'admin', 2: 'analyst'}

    APP_DIR = abspath(dirname(__file__))  # This directory
    PROJECT_ROOT = abspath(join(APP_DIR, os.pardir))

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_TIMEOUT = 300
    SQLALCHEMY_MAX_OVERFLOW = 20
    
    POSTGRES_USE_SSL = os.getenv("POSTGRES_USE_SSL", 'False').lower() in ('true', '1', 't')
    RABBITMQ_USE_SSL = os.getenv("RABBITMQ_USE_SSL", 'False').lower() in ('true', '1', 't')
    RABBITMQ_MGMT_PORT = 15672
    # When osquery is configured to start with the command-line flag
    # --host_identifier=uuid, set this value to True. This will allow
    # nodes requesting to enroll / re-enroll to reuse the same node_key.
    #
    # When set to False, nodes that request the /enroll endpoint subsequently
    # will have a new node_key generated, and a different corresponding
    # node record in the database. This will result in stale node entries.
    POLYLOGYX_EXPECTS_UNIQUE_HOST_ID = True
    POLYLOGYX_CHECKIN_INTERVAL = dt.timedelta(seconds=300)
    POLYLOGYX_ENROLL_OVERRIDE = 'enroll_secret'
    POLYLOGYX_PACK_DELIMITER = '/'
    POLYLOGYX_MINIMUM_OSQUERY_LOG_LEVEL = 0

    POLYLOGYX_ENROLL_SECRET_TAG_DELIMITER = None
    POLYLOGYX_ENROLL_DEFAULT_TAGS = [
    ]

    POLYLOGYX_CAPTURE_NODE_INFO = [
        ('computer_name', 'name'),
        ('hardware_vendor', 'make'),
        ('hardware_model', 'model'),
        ('hardware_serial', 'serial'),
        ('cpu_brand', 'cpu'),
        ('cpu_physical_cores', 'cpu cores'),
        ('physical_memory', 'memory'),
        ('mac', 'Mac address'),
    ]

    USE_X_FORWARDED_HOST = True
    CELERY_MAX_TASKS_PER_CHILD = 1
    CELERY_IMPORTS = ('polylogyx.tasks')
    CELERY_AMQP_TASK_RESULT_EXPIRES = 60
    CELERY_TASK_RESULT_EXPIRES = 30
    CELERY_ACCEPT_CONTENT = ['djson', 'application/x-djson', 'application/json']
    CELERY_EVENT_SERIALIZER = 'djson'
    CELERY_RESULT_SERIALIZER = 'djson'
    CELERY_TASK_SERIALIZER = 'djson'
    # CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
    CELERY_CREATE_MISSING_QUEUES = True
    CELERY_DEFAULT_QUEUE = "default_ui_queue"

    CELERY_QUEUES = {
        "default_ui_queue": {"exchange": "default_ui_exchange", "binding_key": "default"}
    }

    BROKER_USE_SSL = RABBITMQ_USE_SSL
    BROKER_CONNECTION_MAX_RETRIES = None
    # CELERY_TIMEZONE = 'Asia/Kolkata'
    # You can specify a set of custom logger plugins here.  These plugins will
    # be called for every status or result log that is received, and can
    # do what they wish with them.
    POLYLOGYX_LOG_PLUGINS = [
        # 'polylogyx.plugins.logs.file.LogPlugin',
        # 'polylogyx.plugins.logs.splunk.SplunkPlugin',
        'polylogyx.plugins.logs.rsyslog.RsyslogPlugin'
    ]
    POLYLOGYX_LOG_PLUGINS_OBJ = {
        "rsyslog": 'polylogyx.plugins.logs.rsyslog.RsyslogPlugin'
    }

    # These are the configuration variables for the example logger plugin given
    # above.  Uncomment these to start logging results or status logs to the
    # given file.
    POLYLOGYX_LOG_FILE_PLUGIN_JSON_LOG = '/tmp/osquery.log'  # Default: do not log status/results to json log
    POLYLOGYX_LOG_FILE_PLUGIN_STATUS_LOG = '/tmp/status.log'  # Default: do not log status logs
    POLYLOGYX_LOG_FILE_PLUGIN_RESULT_LOG = '/tmp/result.log'  # Default: do not log results
    POLYLOGYX_LOG_FILE_PLUGIN_APPEND = True  # Default: True

    # You can specify a set of alerting plugins here.  These plugins can be
    # configured in rules to trigger alerts to a particular location.  Each
    # plugin consists of a full path to be imported, combined with some
    # configuration for the plugin.  Note that, since an alerter can be
    # configured multiple times with different names, we provide the
    # configuration per-name.
    POLYLOGYX_ALERTER_PLUGINS = {
        'debug': ('polylogyx.plugins.alerters.debug.DebugAlerter', {
            'level': 'error',
        }),
        'rsyslog': ('polylogyx.plugins.alerters.rsyslog.RsyslogAlerter', {

            # Required
            'service_key': 'foobar',

            # Optional
            'client_url': 'https://polylogyx.domain.com',
            'key_format': 'polylogyx-security-{count}',
        }),
        'email': ('polylogyx.plugins.alerters.emailer.EmailAlerter', {
            # Required
            'recipients': [
                'foo@example.com',
            ],

            # Optional, see polylogyx/plugins/alerters/emailer.py for templates
            'subject_prefix': '[PolyLogyx]',
            'subject_template': 'email/alert.subject.txt',
            'message_template': 'email/alert.body.txt',

        }),

        # 'sentry': ('polylogyx.plugins.alerters.sentry.SentryAlerter', {
        #     'dsn': 'https://<key>:<secret>@app.getsentry.com/<project>',
        # }),

        # 'slack': ('polylogyx.plugins.alerters.slack.SlackAlerter', {
        #     # Required, create webhook here: https://my.slack.com/services/new/incoming-webhook/
        #     'slack_webhook' : 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',

        #     # Optional
        #     'printColumns': False,
        #     'color': '#36a64f',
        # })
    }

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = 'polylogyx@localhost'

    # PolyLogyx fleet manager uses the WatchedFileHandler in logging.handlers module.
    # It is the responsibility of the system to rotate these logs on
    # a periodic basis, as the file will grow indefinitely. See
    # https://docs.python.org/dev/library/logging.handlers.html#watchedfilehandler
    # for more information.
    # Alternatively, you can set filename to '-' to log to stdout.
    POLYLOGYX_LOGGING_DIR = '/var/log/er-ui'
    POLYLOGYX_LOGGING_FILENAME = 'er_ui_log'
    POLYLOGYX_LOGFILE_SIZE = int(os.environ.get("LOGFILE_SIZE", 10485760))
    POLYLOGYX_LOGFILE_BACKUP_COUNT = int(os.environ.get("LOGFILE_BACKUP_COUNT", 10))
    POLYLOGYX_LOGGING_FORMAT = '%(asctime)s--%(levelname).1s--%(thread)d--%(funcName)s--%(message)s'
    POLYLOGYX_LOGGING_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_DURATION = dt.timedelta(days=30)
    REMEMBER_COOKIE_PATH = '/manage'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    # see http://flask-login.readthedocs.io/en/latest/#session-protection
    # only applicable when POLYLOGYX_AUTH_METHOD = 'polylogyx'
    SESSION_PROTECTION = "strong"

    BCRYPT_LOG_ROUNDS = 13

    POLYLOGYX_AUTH_METHOD = 'polylogyx'
    POLYLOGYX_COLUMN_RENDER = {
        'computer_name': '<a href="https://{{ value | urlencode }}/">{{ value }}</a>'
    }
    # POLYLOGYX_AUTH_METHOD = 'google'
    # POLYLOGYX_AUTH_METHOD = 'ldap'

    POLYLOGYX_OAUTH_GOOGLE_ALLOWED_DOMAINS = [
    ]

    POLYLOGYX_OAUTH_GOOGLE_ALLOWED_USERS = [
    ]

    POLYLOGYX_OAUTH_CLIENT_ID = ''
    POLYLOGYX_OAUTH_CLIENT_SECRET = ''

    POLYLOGYX_CUSTOM_CONFIG_LIMIT_PER_PLATFORM = int(os.environ.get("CUSTOM_CONFIGS_LIMIT", '5'))

    POLYLOGYX_NGINX_METRIC_COLLECTION_LOGFILE = "/var/log/nginx/plgx_srv.log"

    # When using POLYLOGYX_AUTH_METHOD = 'ldap', see
    # http://flask-ldap3-login.readthedocs.io/en/latest/configuration.html#core
    # Note: not all configuration options are documented at the link
    # provided above. A complete list of options can be groked by
    # reviewing the the flask-ldap3-login code.

    # LDAP_HOST = None
    # LDAP_PORT = 636
    # LDAP_USE_SSL = True
    # LDAP_BASE_DN = 'dc=example,dc=org'
    # LDAP_USER_DN = 'ou=People'
    # LDAP_GROUP_DN = ''
    # LDAP_USER_OBJECT_FILTER = '(objectClass=inetOrgPerson)'
    # LDAP_USER_LOGIN_ATTR = 'uid'
    # LDAP_USER_RDN_ATTR = 'uid'
    # LDAP_GROUP_SEARCH_SCOPE = 'SEARCH_SCOPE_WHOLE_SUBTREE'
    # LDAP_GROUP_OBJECT_FILTER = '(cn=*)(objectClass=groupOfUniqueNames)'
    # LDAP_GROUP_MEMBERS_ATTR = 'uniquemember'
    # LDAP_GET_GROUP_ATTRIBUTES = ['cn']
    # LDAP_OPT_X_TLS_CACERTFILE = None
    # LDAP_OPT_X_TLS_CERTIFICATE_FILE = None
    # LDAP_OPT_X_TLS_PRIVATE_KEY_FILE = None
    # LDAP_OPT_X_TLS_REQUIRE_CERT = 2  # ssl.CERT_REQUIRED
    # LDAP_OPT_X_TLS_USE_VERSION = 3  # ssl.PROTOCOL_TLSv1
    # LDAP_OPT_X_TLS_VALID_NAMES = []

    # To enable Sentry reporting, configure the following keys
    # https://docs.getsentry.com/hosted/clients/python/integrations/flask/
    # SENTRY_DSN = 'https://<key>:<secret>@app.getsentry.com/<project>'
    # SENTRY_INCLUDE_PATHS = ['polylogyx']
    # SENTRY_USER_ATTRS = ['username', 'first_name', 'last_name', 'email']
    #
    # https://docs.getsentry.com/hosted/clients/python/advanced/#sanitizing-data
    # SENTRY_PROCESSORS = [
    #     'raven.processors.SanitizePasswordsProcessor',
    # ]
    # RAVEN_IGNORE_EXCEPTIONS = []


class ProdConfig(Config):
    ENV = 'prod'
    DEBUG = False
    BASE_URL = join(dirname(dirname(__file__)))
    RESOURCES_URL = join(BASE_URL, 'resources')
    COMMON_FILES_URL = join(BASE_URL, 'common')

    INI_CONFIG = get_ini_config(join(COMMON_FILES_URL, 'config.ini'))

    ESP_SERVER_ADDRESS = os.environ.get("ESP_SERVER_ADDRESS", 'http://plgx-esp:6000')

    ER_ADDRESS = os.environ.get("ER_ADDRESS", 'http://plgx-esp:6000')
    API_KEY = os.environ.get("API_KEY", 'c05910fe-7f77-11e8-adc0-fa7ae01bbebc')

    RABBITMQ_HOST = os.environ.get('RABBITMQ_URL', "rabbit1")
    RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', "5672")
    RABBITMQ_USERNAME = os.environ.get('RABBITMQ_USERNAME', "guest")
    RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', "guest")
    RABBIT_CREDS = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    BROKER_URL = 'pyamqp://{0}:{1}@{2}:{3}'.format(RABBITMQ_USERNAME, RABBITMQ_PASSWORD, RABBITMQ_HOST,RABBITMQ_PORT)
    
    CELERY_RESULT_BACKEND = 'rpc://'

    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "admin")

    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    POLYLOGYX_ENROLL_SECRET = [
        'secret',
    ]

    try:
        SQLALCHEMY_DATABASE_URI = 'postgresql://' + os.environ.get('POSTGRES_USER') + ':' + os.environ.get(
            'POSTGRES_PASSWORD') + '@' + os.environ.get('POSTGRES_ADDRESS') + ':' + os.environ.get(
            'POSTGRES_PORT') + '/' + os.environ.get('POSTGRES_DB_NAME')
        if Config.POSTGRES_USE_SSL:
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI+"?ssl=true&sslmode=prefer"
    except Exception as e:
        print('settings database as local - {}'.format(str(e)))
    try:
        if os.environ['ENROLL_SECRET']:
            POLYLOGYX_ENROLL_SECRET = os.environ['ENROLL_SECRET'].split()
    except Exception as e:
        print('Error in reading enroll secret - {}'.format(str(e)))

    POLYLOGYX_MINIMUM_OSQUERY_LOG_LEVEL = 1


class DevConfig(Config):
    """
    This class specifies a configuration that is suitable for running in
    development.  It should not be used for running in production.
    """
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    POLYLOGYX_LOGGING_DIR = '-'
    POLYLOGYX_LOGGING_FILENAME = '-'

    BASE_URL = join(dirname(dirname(__file__)))
    RESOURCES_URL = join(dirname(BASE_URL), 'resources')
    COMMON_FILES_URL = join(dirname(BASE_URL), 'common')

    INI_CONFIG = get_ini_config(join(COMMON_FILES_URL, 'config.ini'))

    ESP_SERVER_ADDRESS = os.environ.get("ESP_SERVER_ADDRESS", 'http://localhost:6000')

    ESP_ADDRESS = os.environ.get("ESP_ADDRESS", 'http://localhost:6000')
    API_KEY = os.environ.get("API_KEY", 'c05910fe-7f77-11e8-adc0-fa7ae01bbebc')

    RABBITMQ_HOST = os.environ.get('RABBITMQ_URL', "localhost")
    RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', "5672")
    RABBITMQ_USERNAME = os.environ.get('RABBITMQ_USERNAME', "guest")
    RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', "guest")
    RABBIT_CREDS = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    BROKER_URL = 'pyamqp://{0}:{1}@{2}:{3}'.format(RABBITMQ_USERNAME, RABBITMQ_PASSWORD, RABBITMQ_HOST,RABBITMQ_PORT)
    CELERY_RESULT_BACKEND = 'rpc://'

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "admin")

    SQLALCHEMY_DATABASE_URI = 'postgresql://polylogyx:polylogyx@localhost:5432/polylogyx'
    RABBITMQ_URL = 'localhost'

    POLYLOGYX_ENROLL_SECRET = [
        'secret',
    ]


class TestConfig(Config):
    """
    This class specifies a configuration that is used for our tests.
    """
    ENV = 'test'
    TESTING = True
    DEBUG = True

    BASE_URL = join(dirname(dirname(__file__)))
    RESOURCES_URL = join(dirname(BASE_URL), 'resources')
    COMMON_FILES_URL = join(dirname(BASE_URL), 'common')

    INI_CONFIG = get_ini_config(join(COMMON_FILES_URL, 'config.ini'))

    SQLALCHEMY_DATABASE_URI = 'postgresql://polylogyx:polylogyx@localhost:5432/polylogyx_test'

    RABBITMQ_HOST = os.environ.get("RABBITMQ_URL", "localhost")
    RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT", "5672")
    RABBITMQ_USERNAME = os.environ.get("RABBITMQ_USERNAME", "guest")
    RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
    RABBIT_CREDS = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    BROKER_URL = "pyamqp://{0}:{1}@{2}:{3}".format(RABBITMQ_USERNAME, RABBITMQ_PASSWORD, RABBITMQ_HOST, RABBITMQ_PORT)
    CELERY_RESULT_BACKEND = "rpc://"

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "admin")
    
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False

    POLYLOGYX_ENROLL_SECRET = [
        'secret',
    ]
    POLYLOGYX_EXPECTS_UNIQUE_HOST_ID = False

    POLYLOGYX_AUTH_METHOD = None


if os.environ.get('DYNO'):
    # we don't want to even define this class elsewhere,
    # because its definition depends on Heroku-specific environment variables
    class HerokuConfig(ProdConfig):
        """
        Environment variables accessed here are provided by Heroku.
        RABBITMW_URL and DATABASE_URL are defined by addons,
        while others should be created using `heroku config`.
        They are also declared in `app.json`, so they will be created
        when deploying using `Deploy to Heroku` button.
        """
        ENV = 'heroku'
        POLYLOGYX_LOGGING_DIR = ''
        POLYLOGYX_LOGGING_FILENAME = '-'  # handled specially - stdout

        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
        BROKER_URL = 'pyamqp://guest:guest@' + os.environ.get('RABBITMQ_URL')
        CELERY_RESULT_BACKEND = 'rpc://'

        try:
            SECRET_KEY = os.environ['SECRET_KEY']
        except KeyError:
            pass  # leave default random-filled key
        # several values can be specified as a space-separated string
        POLYLOGYX_ENROLL_SECRET = os.environ['ENROLL_SECRET'].split()

        POLYLOGYX_AUTH_METHOD = "google" if os.environ.get('OAUTH_CLIENT_ID') else None
        POLYLOGYX_OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID')
        POLYLOGYX_OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET')
        POLYLOGYX_OAUTH_GOOGLE_ALLOWED_USERS = os.environ.get('OAUTH_ALLOWED_USERS', '').split()

        # mail config
        MAIL_SERVER = os.environ.get('MAIL_SERVER')
        MAIL_PORT = os.environ.get('MAIL_PORT')
        MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
        MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
        MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
        MAIL_USE_SSL = True

        POLYLOGYX_ALERTER_PLUGINS = {
            'debug': ('polylogyx.plugins.alerters.debug.DebugAlerter', {
                'level': 'error',
            }),

            'rsyslog': ('polylogyx.plugins.alerters.rsyslog.RsyslogAlerter', {

                # Required
                'service_key': 'foobar',

                # Optional
                'client_url': 'https://polylogyx.domain.com',
                'key_format': 'polylogyx-security-{count}',
            }),
            'email': ('polylogyx.plugins.alerters.emailer.EmailAlerter', {
                'recipients': [
                    email.strip() for email in
                    os.environ.get('MAIL_RECIPIENTS', '').split(';')
                ],
            }),
        }

# choose proper configuration based on environment -
# this is both for manage.py and for worker.py
if os.environ.get("ENV") == ProdConfig.ENV:
    CurrentConfig = ProdConfig
elif os.environ.get("ENV") == TestConfig.ENV:
    CurrentConfig = TestConfig
elif os.environ.get("DYNO"):
    CurrentConfig = HerokuConfig
else:
    CurrentConfig = DevConfig

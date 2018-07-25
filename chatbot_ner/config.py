import logging.handlers
import os

import dotenv
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config')
MODEL_CONFIG_PATH = os.path.join(BASE_DIR, 'model_config')

LOG_PATH = BASE_DIR + '/logs/'
# SET UP NER LOGGING
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

NER_LOG_FILENAME = LOG_PATH + 'ner_log.log'
# Set up a specific logger with our desired output level
ner_logger = logging.getLogger('NERLogger')
ner_logger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(NER_LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
ner_logger.addHandler(handler)

# SET UP NLP LIB LOGGING
NLP_LIB_LOG_FILENAME = LOG_PATH + 'nlp_log.log'
# Set up a specific logger with our desired output level
nlp_logger = logging.getLogger('NLPLibLogger')
nlp_logger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(NLP_LIB_LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
nlp_logger.addHandler(handler)

if os.path.exists(CONFIG_PATH):
    dotenv.read_dotenv(CONFIG_PATH)
else:
    ner_logger.debug('Warning: no file named "config" found at %s. This is not a problem if your '
                     'datastore(elasticsearch) connection settings are already available in the environment',
                     CONFIG_PATH)

# TODO Consider prefixing everything config with HAPTIK_NER_ because these names are in the environment and so are
# TODO lot of others too which may conflict in name. Example user is already using some another instance of
# TODO Elasticsearch for other purposes
ENGINE = os.environ.get('ENGINE')
if ENGINE:
    ENGINE = ENGINE.lower()
ES_URL = os.environ.get('ES_URL')
ES_HOST = os.environ.get('ES_HOST')
ES_PORT = os.environ.get('ES_PORT')
ES_INDEX_NAME = os.environ.get('ES_INDEX_NAME')
ES_DOC_TYPE = os.environ.get('ES_DOC_TYPE')
ES_AUTH_NAME = os.environ.get('ES_AUTH_NAME')
ES_AUTH_PASSWORD = os.environ.get('ES_AUTH_PASSWORD')
ES_BULK_MSG_SIZE = os.environ.get('ES_BULK_MSG_SIZE', '10000')
ES_SEARCH_SIZE = os.environ.get('ES_SEARCH_SIZE', '10000')

try:
    ES_BULK_MSG_SIZE = int(ES_BULK_MSG_SIZE)
    ES_SEARCH_SIZE = int(ES_SEARCH_SIZE)
except ValueError:
    ES_BULK_MSG_SIZE = 10000
    ES_SEARCH_SIZE = 10000

ES_AWS_SECRET_ACCESS_KEY = os.environ.get('ES_AWS_SECRET_ACCESS_KEY')
ES_AWS_ACCESS_KEY_ID = os.environ.get('ES_AWS_ACCESS_KEY_ID')
ES_AWS_REGION = os.environ.get('ES_AWS_REGION')
ES_AWS_SERVICE = os.environ.get('ES_AWS_SERVICE')
GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')

if not GOOGLE_TRANSLATE_API_KEY:
    ner_logger.warning('Google Translate API key is null or not set')
    GOOGLE_TRANSLATE_API_KEY = ''

CHATBOT_NER_DATASTORE = {
    'engine': ENGINE,
    'elasticsearch': {
        'connection_url': ES_URL,
        'name': ES_INDEX_NAME,
        'host': ES_HOST,
        'port': ES_PORT,
        'user': ES_AUTH_NAME,
        'password': ES_AUTH_PASSWORD,
        'retry_on_timeout': False,
        'max_retries': 1,
        'timeout': 20,
        'request_timeout': 20,
    }
}

if ES_DOC_TYPE:
    CHATBOT_NER_DATASTORE['elasticsearch']['doc_type'] = ES_DOC_TYPE
else:
    CHATBOT_NER_DATASTORE['elasticsearch']['doc_type'] = 'data_dictionary'

if not ES_AWS_SERVICE:
    ES_AWS_SERVICE = 'es'

if ES_AWS_ACCESS_KEY_ID and ES_AWS_SECRET_ACCESS_KEY and ES_AWS_REGION and ES_AWS_SERVICE:
    CHATBOT_NER_DATASTORE['elasticsearch']['http_auth'] = AWS4Auth(ES_AWS_ACCESS_KEY_ID, ES_AWS_SECRET_ACCESS_KEY,
                                                                   ES_AWS_REGION, ES_AWS_SERVICE)
    CHATBOT_NER_DATASTORE['elasticsearch']['use_ssl'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['verify_certs'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['connection_class'] = RequestsHttpConnection
elif ES_AWS_REGION and ES_AWS_SERVICE:
    CHATBOT_NER_DATASTORE['elasticsearch']['use_ssl'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['verify_certs'] = True
    CHATBOT_NER_DATASTORE['elasticsearch']['connection_class'] = RequestsHttpConnection
else:
    ner_logger.warning('Elasticsearch: Some or all AWS settings missing from environment, this will skip AWS auth!')

if os.path.exists(MODEL_CONFIG_PATH):
    dotenv.read_dotenv(MODEL_CONFIG_PATH)
else:
    ner_logger.warning('Warning: no file named "model_config" found at %s. This is not a problem if you '
                       'dont want to run NER with ML models', MODEL_CONFIG_PATH)

CITY_MODEL_TYPE = os.environ.get('CITY_MODEL_TYPE')
CITY_MODEL_PATH = os.environ.get('CITY_MODEL_PATH')
DATE_MODEL_TYPE = os.environ.get('DATE_MODEL_TYPE')
DATE_MODEL_PATH = os.environ.get('DATE_MODEL_PATH')
if not CITY_MODEL_PATH:
    CITY_MODEL_PATH = os.path.join(BASE_DIR, 'data', 'models', 'crf', 'city', 'model_13062017.crf')
if not DATE_MODEL_PATH:
    DATE_MODEL_PATH = os.path.join(BASE_DIR, 'data', 'models', 'crf', 'date', 'model_date.crf')

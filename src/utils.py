import os
import sys
import redis
import logging
import traceback
from pythonjsonlogger import jsonlogger


logging.getLogger('botocore.credentials').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s',
                                     '%Y-%m-%dT%H:%M:%SZ')

# Show in terminal
s_handler = logging.StreamHandler(sys.stdout)
s_handler.setFormatter(formatter)
root_logger.addHandler(s_handler)


def _uncaught(exctype, value, tb):
    logger = logging.getLogger('uncaught')
    message = ''.join(traceback.format_exception(exctype, value, tb))
    logger.critical(message)


sys.excepthook = _uncaught


redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'),
                           password=os.getenv('REDIS_PASSWORD', ''))

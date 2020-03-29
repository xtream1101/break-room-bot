import os
import sys
import boto3
import redis
import os.path
import logging
import datetime
import tempfile
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


def get_ts():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def save_render(board_img, board_name, ext='png'):
    # TODO: Auto get content type using lib
    content_type = {
        'png': 'image/png',
        'gif': 'image/gif',
    }
    file_key = f"{board_name}.{ext}"
    s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
    with tempfile.NamedTemporaryFile() as tmp:
        # TODO: Need to make this dynamic in order to support multiple formats
        board_img.save(tmp.name, format=ext)
        s3.upload_file(tmp.name,
                       os.environ['RENDERED_IMAGES_BUCKET'],
                       file_key,
                       ExtraArgs={'ContentType': content_type[ext]})

    return f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/{file_key}"

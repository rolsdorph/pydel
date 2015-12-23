import hashlib
import datetime
import uuid
import random


def random_device_uid():
    return hashlib.sha256(str(uuid.uuid4()).encode('UTF-8')).hexdigest()


def random_loc_accuracy():
        return random.uniform(1.0, 15.0)


def iso8601_to_datetime(iso8601):
    return datetime.datetime.strptime(iso8601, "%Y-%m-%dT%H:%M:%S.%fZ")

# Dashboard API tests
# TODO: DM-6990 Improve testing in SQuaSH prototype

import os
import sys
import json
import requests

# Username and password set during database creation

TEST_USER = os.environ.get("TEST_USER", None)
TEST_PASSWD = os.environ.get("TEST_PASSWD", None)


if TEST_USER is None or TEST_PASSWD is None:
    print("TEST_USER or TEST_PASSWD are not set.")
    sys.exit(1)

TEST_API_URL = os.environ.get("TEST_API_URL",
                              "http://localhost:8000/")


def test_api_root():
    """Access to the api root
    """
    r = requests.get(TEST_API_URL)
    assert r.status_code == requests.codes.ok


def test_auth():
    """API endpoints are read only, so a GET must work
    without authentication
    """
    r = requests.get(TEST_API_URL)
    api = r.json()

    for endpoint in api:
        r = requests.get(api[endpoint])
        assert r.status_code == 200


def test_post_metric():
    """ Test Metric endpoint inserting one metric
    """

    with open('data/test_post_metric.json') as f:
        data = json.load(f)

    r = requests.get(TEST_API_URL)
    api = r.json()

    r = requests.post(api['metrics'], json=data,
                      auth=(TEST_USER, TEST_PASSWD))

    assert r.status_code == 201

    r.close()


def test_post_metric_list():
    """ Test Metric endpoint inserting a list of metrics
    """

    with open('data/test_post_metric_list.json') as f:
        data = json.load(f)

    r = requests.get(TEST_API_URL)
    api = r.json()

    r = requests.post(api['metrics'], json=data,
                      auth=(TEST_USER, TEST_PASSWD))

    assert r.status_code == 201

    r.close()


def test_post_job():
    """ Test Job endpoint
    """

    with open('data/test_post_job.json') as f:
        data = json.load(f)

    r = requests.get(TEST_API_URL)
    api = r.json()

    r = requests.post(api['jobs'], json=data,
                      auth=(TEST_USER, TEST_PASSWD))

    assert r.status_code == 201

    r.close()

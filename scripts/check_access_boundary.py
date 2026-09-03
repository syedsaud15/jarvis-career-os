"""HTTP deployment smoke test. No real credentials or private payloads are needed."""
import argparse
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def probe(base, path):
    request = Request(base.rstrip('/') + path, headers={'Cache-Control': 'no-cache'})
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, response.headers
    except HTTPError as error:
        return error.code, error.headers


def check(base):
    for attempt in range(30):
        try:
            if probe(base, '/api/health')[0] == 200:
                break
        except (URLError, TimeoutError):
            pass
        if attempt == 29:
            raise RuntimeError('Service did not become healthy')
        time.sleep(2)
    for path, expected in [('/demo', 200), ('/demo/', 200), ('/', 401),
                           ('/index.html', 401), ('/api/profile', 401),
                           ('/api/integrations', 401), ('/api/approvals', 401),
                           ('/api/settings', 401), ('/api/applications', 401),
                           ('/api/activity', 401), ('/api/backup/export.json', 401),
                           ('/demonstration', 401)]:
        actual, headers = probe(base, path)
        assert actual == expected, f'{path}: expected {expected}, got {actual}'
        if expected == 401:
            assert headers.get('WWW-Authenticate', '').startswith('Basic ')
        print(f'PASS {path}: {actual}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('base_url')
    check(parser.parse_args().base_url)

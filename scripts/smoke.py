#!/usr/bin/env python3
"""Verify the running SINQ system over HTTP, leaving one linked demo inquiry."""
import json
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

API = 'http://localhost:8000/sinq/api/'
CLIENT = 'http://localhost:8080/'


def fetch(url, data=None, content_type=None):
    headers = {'Content-Type': content_type} if content_type else {}
    with urlopen(Request(url, data=data, headers=headers), timeout=60) as response:
        return response.read()


def read(route):
    return json.loads(fetch(API + route))


def create(route, data):
    return json.loads(fetch(API + route, json.dumps(data).encode(), 'application/json'))[0]


if __name__ == '__main__':
    assert b'SINQ' in fetch(CLIENT), 'Mobile client is unavailable'
    assert json.loads(fetch('http://localhost:8000/healthz/'))['status'] == 'ok'
    question = create('questions/create/', {'question': {'text': 'Why do leaves turn toward light? ' + uuid4().hex[:8]}})
    explanation = create('causeandeffects/create/', {'causeandeffect': {
        'question_id': question['pk'], 'cause_text': 'Sunlight comes from one direction.', 'effect_text': 'Leaves lean toward the light.'}})
    investigation = create('investigations/create/', {'investigation': {
        'question_id': question['pk'], 'causeandeffect_id': explanation['pk'],
        'steps': [{'number': 1, 'text': 'Turn the plant.'}, {'number': 2, 'text': 'Observe its direction.'}]}})
    image = (Path(__file__).resolve().parent.parent / 'sinq-ios/www/img/sinq_logo.png').read_bytes()
    boundary = 'sinq-' + uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="question_image"; filename="sinq.png"\r\n'
            'Content-Type: image/png\r\n\r\n').encode() + image + f'\r\n--{boundary}--\r\n'.encode()
    upload = json.loads(fetch(API + f"questions/{question['pk']}/images/create/", body,
                              f'multipart/form-data; boundary={boundary}'))[0]
    assert fetch('http://localhost:8000/media/' + upload['fields']['image']) == image
    assert read(f"questions/?investigation_id={investigation['pk']}")[0]['pk'] == question['pk']
    assert read(f"causeandeffects/?question_id={question['pk']}")[0]['pk'] == explanation['pk']
    steps = read(f"investigations/{investigation['pk']}/steps/")
    assert [step['fields']['number'] for step in steps] == [1, 2]
    assert read('questions/') == json.loads(fetch('http://localhost:8000/api/questions/'))
    print(json.dumps({'status': 'passed', 'question': question['pk'], 'explanation': explanation['pk'],
                      'investigation': investigation['pk'], 'photo': upload['fields']['image']}, indent=2))

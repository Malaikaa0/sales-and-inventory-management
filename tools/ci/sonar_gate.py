"""
Set up a SonarQube server, analyse the code and fail if the quality gate fails.

Run from the repository root, with coverage.xml present. The token is generated
here, kept in this process's memory and handed to the scanner container through
an environment variable. It is never printed or written to a file.

Environment:
  SONAR_URL             server as seen from this script (default http://localhost:9000)
  SCANNER_HOST_URL      server as seen from the scanner container (default SONAR_URL)
  SCANNER_NETWORK       docker network for the scanner (default host)
  SONAR_ADMIN_PASSWORD  admin password of an existing server. When unset the server
                        is assumed new: the default password is replaced by a random one.
  PROJECT_KEY           default sales-and-inventory-management
"""
import base64
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

URL = os.environ.get('SONAR_URL', 'http://localhost:9000').rstrip('/')
SCANNER_URL = os.environ.get('SCANNER_HOST_URL', URL)
NETWORK = os.environ.get('SCANNER_NETWORK', 'host')
PROJECT = os.environ.get('PROJECT_KEY', 'sales-and-inventory-management')
SCANNER_IMAGE = 'sonarsource/sonar-scanner-cli:latest'
GATE = 'SQE-gate'
# Overall code conditions: metric, operator that means failure, threshold
CONDITIONS = [
    ('bugs', 'GT', '0'),
    ('vulnerabilities', 'GT', '0'),
    ('coverage', 'LT', '90'),
    ('duplicated_lines_density', 'GT', '3'),
]
OUT = 'reports/ci-sonar'

password = os.environ.get('SONAR_ADMIN_PASSWORD')


def call(path, data=None, auth=None):
    """GET, or POST when data is given. Returns parsed JSON or None."""
    request = urllib.request.Request(f'{URL}/{path}')
    user, secret = auth or ('admin', password)
    request.add_header('Authorization', 'Basic ' + base64.b64encode(f'{user}:{secret}'.encode()).decode())
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    try:
        with urllib.request.urlopen(request, body, timeout=30) as response:
            text = response.read().decode()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'SonarQube {path.split("?")[0]} failed: {error.code} {error.read().decode()[:300]}')
    return json.loads(text) if text else None


def wait_until_up(limit=600):
    deadline = time.time() + limit
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f'{URL}/api/system/status', timeout=10) as response:
                if json.load(response).get('status') == 'UP':
                    print('SonarQube is up')
                    return
        except (OSError, ValueError):
            pass
        time.sleep(5)
    raise SystemExit(f'SonarQube was not up after {limit} seconds')


def set_up_server():
    global password
    if not password:
        password = secrets.token_urlsafe(24) + 'aA1!'
        call('api/users/change_password',
             {'login': 'admin', 'previousPassword': 'admin', 'password': password}, auth=('admin', 'admin'))
        print('admin password replaced')
    found = call(f'api/projects/search?projects={PROJECT}')['components']
    if not found:
        call('api/projects/create', {'project': PROJECT, 'name': PROJECT})
    if GATE not in [g['name'] for g in call('api/qualitygates/list')['qualitygates']]:
        call('api/qualitygates/create', {'name': GATE})
    for condition in call(f'api/qualitygates/show?name={GATE}').get('conditions', []):
        call('api/qualitygates/delete_condition', {'id': condition['id']})
    for metric, operator, error in CONDITIONS:
        call('api/qualitygates/create_condition',
             {'gateName': GATE, 'metric': metric, 'op': operator, 'error': error})
    call('api/qualitygates/select', {'gateName': GATE, 'projectKey': PROJECT})
    print(f'project {PROJECT} uses gate {GATE} with {len(CONDITIONS)} conditions')


def scan(directory, token, *extra):
    # Blame data is not needed by overall code conditions.
    command = [
        'docker', 'run', '--rm', '--network', NETWORK,
        '-e', 'SONAR_TOKEN', '-e', 'SONAR_HOST_URL',
        '-v', f'{directory}:/usr/src:ro', SCANNER_IMAGE,
        f'-Dsonar.projectKey={PROJECT}', '-Dsonar.scm.disabled=true',
        '-Dsonar.working.directory=/tmp/scannerwork', *extra,
    ]
    env = dict(os.environ, SONAR_TOKEN=token, SONAR_HOST_URL=SCANNER_URL, MSYS_NO_PATHCONV='1')
    return subprocess.run(command, env=env).returncode


def wait_for_processing(limit=600):
    deadline = time.time() + limit
    while time.time() < deadline:
        state = call(f'api/ce/component?component={PROJECT}')
        if not state.get('queue') and state.get('current', {}).get('status') in ('SUCCESS', 'FAILED', 'CANCELED'):
            if state['current']['status'] != 'SUCCESS':
                raise SystemExit('SonarQube could not process the analysis')
            return
        time.sleep(3)
    raise SystemExit('timed out waiting for SonarQube to process the analysis')


def main():
    if not os.path.exists('coverage.xml'):
        raise SystemExit('coverage.xml is missing: run the tests with coverage first')
    wait_until_up()
    set_up_server()
    name = f'ci-{secrets.token_hex(4)}'
    token = call('api/user_tokens/generate', {'name': name})['token']
    if os.environ.get('GITHUB_ACTIONS'):
        print(f'::add-mask::{token}')
    try:
        print('analysing the code')
        code = scan(os.getcwd(), token, '-Dsonar.qualitygate.wait=true')
        wait_for_processing()
        gate = call(f'api/qualitygates/project_status?projectKey={PROJECT}')['projectStatus']
        issues = call(f'api/issues/search?components={PROJECT}&resolved=false&types=BUG,VULNERABILITY&ps=500')
        os.makedirs(OUT, exist_ok=True)
        with open(f'{OUT}/quality-gate.json', 'w', encoding='utf-8') as handle:
            json.dump(gate, handle, indent=2)
        for issue in issues['issues']:
            issue.pop('author', None)
        with open(f'{OUT}/bugs-and-vulnerabilities.json', 'w', encoding='utf-8') as handle:
            json.dump(issues['issues'], handle, indent=2)
        print(f'quality gate: {gate["status"]}')
        for condition in gate['conditions']:
            print(f'  {condition["metricKey"]}: {condition.get("actualValue", "no value")} {condition["status"]}')
        for issue in issues['issues']:
            print(f'  {issue["type"]}: {issue["component"].split(":", 1)[1]}:{issue.get("line")} {issue["message"]}')
        if code != 0 or gate['status'] != 'OK':
            sys.exit(1)
    finally:
        call('api/user_tokens/revoke', {'name': name})
        print('token revoked')


if __name__ == '__main__':
    main()

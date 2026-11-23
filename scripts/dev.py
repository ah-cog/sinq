#!/usr/bin/env python3
"""Reproducible local orchestration for the SINQ server and mobile client."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / '.local'
SERVER = ROOT / 'sinq-server'
MOBILE = ROOT / 'sinq-ios'
PYTHON = SERVER / '.venv/bin/python'
ENDPOINTS = {'server': 'http://localhost:18000/sinq/api/questions/', 'mobile': 'http://localhost:18080/'}


def run(args, cwd=ROOT):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def ready(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def setup():
    run(['git', 'submodule', 'update', '--init', '--recursive'])
    python = os.environ.get('SINQ_PYTHON') or shutil.which('python3.14') or shutil.which('python3.13')
    if not python:
        raise SystemExit('Install Python 3.13 or newer, or set SINQ_PYTHON.')
    if not PYTHON.exists():
        run([python, '-m', 'venv', SERVER / '.venv'])
    run([PYTHON, '-m', 'pip', 'install', '-r', 'requirements.txt'], SERVER)
    run([PYTHON, 'manage.py', 'migrate'], SERVER)
    run([PYTHON, 'manage.py', 'seed_demo'], SERVER)
    run(['npm', 'ci'], MOBILE)


def start():
    STATE.mkdir(exist_ok=True)
    if not PYTHON.exists() or not (MOBILE / 'node_modules').exists():
        raise SystemExit('Run python3 scripts/dev.py setup first.')
    commands = {
        'server': ([str(PYTHON), 'manage.py', 'runserver', '127.0.0.1:18000', '--noreload'], SERVER),
        'mobile': (['node', str(MOBILE / 'scripts/serve.mjs')], MOBILE),
    }
    for name, (command, cwd) in commands.items():
        if ready(ENDPOINTS[name]):
            print(f'{name}: already responding at {ENDPOINTS[name]}')
            continue
        with (STATE / f'{name}.log').open('ab') as log:
            process = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
        (STATE / f'{name}.pid').write_text(str(process.pid))
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if all(ready(url) for url in ENDPOINTS.values()):
            status()
            return
        time.sleep(1)
    raise SystemExit(f'Startup timed out. See {STATE}/*.log')


def stop():
    for name in ENDPOINTS:
        file = STATE / f'{name}.pid'
        if not file.exists():
            continue
        pid = int(file.read_text())
        # Check command identity before using a stored PID, which may have been reused.
        result = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True)
        expected = f'{PYTHON} manage.py runserver' if name == 'server' else f'node {MOBILE / "scripts/serve.mjs"}'
        if expected in result.stdout:
            try:
                os.killpg(pid, signal.SIGTERM)
                print(f'{name}: stopped')
            except ProcessLookupError:
                pass
        file.unlink(missing_ok=True)


def status():
    for name, url in ENDPOINTS.items():
        print(f'{name}: {"running" if ready(url) else "unavailable"} — {url}')


def test():
    run([PYTHON, 'manage.py', 'check'], SERVER)
    run([PYTHON, 'manage.py', 'makemigrations', '--check', '--dry-run'], SERVER)
    run([PYTHON, 'manage.py', 'test'], SERVER)
    run(['npm', 'test'], MOBILE)


def mobile(platform):
    if not (MOBILE / 'node_modules/.bin/cordova').exists():
        run(['npm', 'ci'], MOBILE)
    env = os.environ.copy()
    sdk = Path('/opt/homebrew/share/android-commandlinetools')
    if platform == 'android' and sdk.exists():
        env.setdefault('ANDROID_HOME', str(sdk))
        env.setdefault('JAVA_HOME', '/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home')
        env['PATH'] = os.pathsep.join([str(sdk / 'emulator'), str(sdk / 'platform-tools'), str(sdk / 'cmdline-tools/latest/bin'), env['PATH']])
        if not shutil.which('gradle', path=env['PATH']):
            cached = sorted((Path.home() / '.gradle/wrapper/dists').glob('gradle-*/*/gradle-*/bin/gradle'))
            if cached:
                env['PATH'] = str(cached[-1].parent) + os.pathsep + env['PATH']
    if not (MOBILE / 'platforms' / platform).exists():
        subprocess.run(['npx', 'cordova', 'platform', 'add', platform], cwd=MOBILE, env=env, check=True)
    command = ['npx', 'cordova', 'run', platform, '--emulator']
    target = env.get(f'SINQ_{platform.upper()}_TARGET')
    if platform == 'android' and not target and (Path.home() / '.android/avd/SINQ_API_33.ini').exists():
        target = 'SINQ_API_33'
    if platform == 'android' and target:
        adb = shutil.which('adb', path=env['PATH'])
        if adb:
            devices = subprocess.run([adb, 'devices'], capture_output=True, text=True, env=env, check=True)
            for line in devices.stdout.splitlines()[1:]:
                fields = line.split()
                if len(fields) != 2 or fields[1] != 'device' or not fields[0].startswith('emulator-'):
                    continue
                serial = fields[0]
                name = subprocess.run([adb, '-s', serial, 'emu', 'avd', 'name'], capture_output=True, text=True, env=env, check=True)
                if target == serial or target in name.stdout.splitlines():
                    target = serial
                    subprocess.run([adb, '-s', serial, 'reverse', 'tcp:18000', 'tcp:18000'], env=env, check=True)
                    break
    if target:
        command.extend(['--target', target])
    subprocess.run(command, cwd=MOBILE, env=env, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'start', 'stop', 'status', 'test', 'ios', 'android'])
    args = parser.parse_args()
    if args.command in ['ios', 'android']:
        mobile(args.command)
    else:
        globals()[args.command]()

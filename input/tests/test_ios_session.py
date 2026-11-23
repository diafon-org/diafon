#!/usr/bin/env python3
"""The iOS keyboard's keystroke logic, on the Mac. Run: python3 tests/test_ios_session.py

1. Session (input_methods/ios/Shared) against a simulated editor
   (input_methods/ios/check/SessionCheck.swift): every stream trace of the
   typing in both tail modes, random keys in every output, and the cases
   (backspace, a moved cursor, a cleared field, emoji and emoticons).
2. The keyboard and the app typecheck against UIKit (Mac Catalyst), so a
   change to the shared core that breaks them shows without a simulator.
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLE = os.path.join(ROOT, 'input_methods', 'apple')
IOS = os.path.join(ROOT, 'input_methods', 'ios')
CORE = [os.path.join(APPLE, 'Core', f) for f in ('Diafon.swift', 'Prefs.swift', 'Emoji.swift', 'Layouts.swift')]


def swift_files(*dirs):
    return [os.path.join(IOS, d, f) for d in dirs for f in sorted(os.listdir(os.path.join(IOS, d))) if f.endswith('.swift')]


def test_ios_session():
    if not shutil.which('xcrun'):
        print('  SKIP: no Swift compiler')
        return
    subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'gen_apple.py')], check=True, capture_output=True)
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, 'check')
        files = CORE + [os.path.join(IOS, 'Shared', 'Session.swift'), os.path.join(IOS, 'check', 'SessionCheck.swift')]
        res = subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-parse-as-library', *files, '-o', exe], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
        env = dict(os.environ, DIAFON_RESOURCES=os.path.join(APPLE, 'Resources'), DIAFON_EMOJI=os.path.join(ROOT, 'data', 'emoji.json'))
        res = subprocess.run([exe, os.path.join(ROOT, 'spec', 'diafon-v1.json')], capture_output=True, text=True, env=env)
    print(res.stdout.strip())
    assert res.returncode == 0, res.stdout + res.stderr


def test_ios_typecheck():
    if not shutil.which('xcrun'):
        return
    sdk = subprocess.run(['xcrun', '--show-sdk-path'], capture_output=True, text=True).stdout.strip()
    ios = os.path.join(sdk, 'System', 'iOSSupport')
    if not os.path.isdir(os.path.join(ios, 'System', 'Library', 'Frameworks', 'UIKit.framework')):
        print('  SKIP: no Mac Catalyst UIKit in the SDK')
        return
    flags = ['-typecheck', '-swift-version', '5', '-parse-as-library', '-target', 'arm64-apple-ios17.0-macabi', '-sdk', sdk,
             '-Fsystem', os.path.join(ios, 'System', 'Library', 'Frameworks'), '-I', os.path.join(ios, 'usr', 'lib', 'swift')]
    for target in ('Keyboard', 'App'):
        res = subprocess.run(['xcrun', 'swiftc', *flags, *CORE, *swift_files('Shared', target)], capture_output=True, text=True)
        assert res.returncode == 0, f'{target}:\n{res.stderr}'
    print('the keyboard and the app typecheck against UIKit')


if __name__ == '__main__':
    test_ios_session()
    test_ios_typecheck()

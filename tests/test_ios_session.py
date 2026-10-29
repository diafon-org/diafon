#!/usr/bin/env python3
"""The iOS keyboard's keystroke logic, on a Mac. Run: python3 tests/test_ios_session.py

Compiles the shared Swift core (input_methods/apple/Core) with the keyboard's
Session (input_methods/ios/Shared) and SessionCheck, then runs the check over
docs/spec.json: every stream trace key by key in both tail modes (marked text,
replaced text), a seeded fuzz of keys and backspaces in every output, and the
flush, take and cursor-move cases. Then typechecks the keyboard and the app
against UIKit and SwiftUI through the macOS SDK's Mac Catalyst frameworks.
No Xcode or simulator: the Command Line Tools are enough.
"""
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'input_methods', 'apple', 'Core')
IOS = os.path.join(ROOT, 'input_methods', 'ios')
CORE_FILES = ('SpecData.swift', 'Engine.swift', 'Stages.swift', 'Reading.swift', 'Lexicon.swift', 'Prefs.swift', 'Emoji.swift')


def build():
    out = tempfile.mkdtemp(prefix='diafon-ios-session-')
    exe = os.path.join(out, 'check')
    files = [os.path.join(CORE, f) for f in CORE_FILES]
    files += [os.path.join(IOS, 'Shared', 'Session.swift'), os.path.join(IOS, 'check', 'SessionCheck.swift')]
    res = subprocess.run(['xcrun', 'swiftc', '-O', '-parse-as-library', *files, '-o', exe], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return exe


def swift_files(*dirs):
    return [os.path.join(IOS, d, f) for d in dirs for f in sorted(os.listdir(os.path.join(IOS, d))) if f.endswith('.swift')]


def test_ios_typecheck():
    if not shutil.which('swiftc'):
        print('SKIP: swiftc not installed')
        return
    sdk = subprocess.run(['xcrun', '--show-sdk-path'], capture_output=True, text=True).stdout.strip()
    ios = os.path.join(sdk, 'System', 'iOSSupport')
    if not os.path.isdir(os.path.join(ios, 'System', 'Library', 'Frameworks', 'UIKit.framework')):
        print('SKIP: no Mac Catalyst UIKit in the SDK')
        return
    core = [os.path.join(CORE, f) for f in CORE_FILES]
    flags = ['-typecheck', '-swift-version', '5', '-parse-as-library', '-target', 'arm64-apple-ios17.0-macabi', '-sdk', sdk,
             '-Fsystem', os.path.join(ios, 'System', 'Library', 'Frameworks'), '-I', os.path.join(ios, 'usr', 'lib', 'swift')]
    for target in ('Keyboard', 'App'):
        res = subprocess.run(['xcrun', 'swiftc', *flags, *core, *swift_files('Shared', target)], capture_output=True, text=True)
        assert res.returncode == 0, f'{target}:\n{res.stderr}'
    print('keyboard and app typecheck against UIKit')


def test_ios_session():
    if not shutil.which('swiftc'):
        print('SKIP: swiftc not installed')
        return
    env = dict(os.environ, DIAFON_EMOJI=os.path.join(ROOT, 'data', 'emoji.json'))
    res = subprocess.run([build(), os.path.join(ROOT, 'docs', 'spec.json')], capture_output=True, text=True, env=env)
    print(res.stdout.strip())
    assert res.returncode == 0, res.stdout + res.stderr


if __name__ == '__main__':
    test_ios_session()
    test_ios_typecheck()

# System imports
import os
import subprocess
import types

from PyGitUp import gitup
from PyGitUp.gitup import GitUp, prepare_windows_log_hook


def test_bash_style_arguments_are_accepted():
    assert prepare_windows_log_hook('git log $1 $2') == \
        'git log !GITUP_ARG1! !GITUP_ARG2!'


def test_cmd_style_arguments_are_rewritten():
    assert prepare_windows_log_hook('git log %1 %2') == \
        'git log !GITUP_ARG1! !GITUP_ARG2!'


def test_format_placeholders_are_escaped():
    assert prepare_windows_log_hook('git log --pretty=format:"%Cred%h"') == \
        'git log --pretty=format:"%%Cred%%h"'


def test_exclamation_marks_stay_literal():
    # Delayed expansion is enabled for the whole script, so a literal '!' in
    # the user's own hook has to be escaped.
    assert prepare_windows_log_hook('echo done!') == 'echo done^!'


def test_semicolons_become_newlines():
    assert prepare_windows_log_hook('echo a; echo b') == 'echo a\necho b'


def test_no_positional_placeholder_survives():
    """The branch name must never be substituted into the script textually."""
    prepared = prepare_windows_log_hook('echo %1 > out; echo $2 >> out')

    assert '%1' not in prepared
    assert '$2' not in prepared


class _FakeName(object):
    def __init__(self, name):
        self.name = name


def _run_windows_log_hook(monkeypatch, hook, branch_name):
    """Run GitUp.log() through the Windows branch and capture the call."""
    calls = {}

    def fake_call(args, env=None):
        with open(args[0]) as f:
            calls['script'] = f.read()
        calls['args'] = args
        calls['env'] = env
        return 0

    monkeypatch.setattr(gitup, 'ON_WINDOWS', True)
    monkeypatch.setattr(subprocess, 'call', fake_call)

    fake_self = types.SimpleNamespace(
        settings={'rebase.log-hook': hook},
        testing=True,
    )
    GitUp.log(fake_self, _FakeName(branch_name), _FakeName('origin'))

    return calls


def test_branch_name_is_passed_via_environment(monkeypatch):
    calls = _run_windows_log_hook(monkeypatch, 'echo %1', 'my-branch')

    assert calls['env']['GITUP_ARG1'] == 'my-branch'
    assert calls['env']['GITUP_ARG2'] == 'origin'

    # Nothing untrusted on the command line cmd.exe parses
    assert calls['args'] == [calls['args'][0]]


def test_metacharacters_in_branch_name_are_not_injected(monkeypatch):
    payload = 'poc&calc.exe'
    calls = _run_windows_log_hook(monkeypatch, 'echo %1 > out', payload)

    # The payload reaches the hook as data, never as part of the script
    assert payload not in calls['script']
    assert calls['env']['GITUP_ARG1'] == payload
    assert 'setlocal enabledelayedexpansion' in calls['script']
    assert '!GITUP_ARG1!' in calls['script']


def test_temporary_script_is_removed(monkeypatch):
    calls = _run_windows_log_hook(monkeypatch, 'echo %1', 'my-branch')

    assert not os.path.exists(calls['args'][0])

import shutil

import pytest
from git import Git, Repo

from PyGitUp.git_wrapper import GitError, GitWrapper, RebaseError
from PyGitUp.gitup import GitUp


@pytest.fixture
def worktree_repo(tmp_path, monkeypatch):
    repo = Repo.init(tmp_path / 'repo')
    repo.git.symbolic_ref('HEAD', 'refs/heads/main')
    repo.git.config('user.name', 'Example User')
    repo.git.config('user.email', 'user@example.com')
    tracked_file = tmp_path / 'repo' / 'file.txt'
    tracked_file.write_text('initial\n')
    (tmp_path / 'repo' / 'local.txt').write_text('local\n')
    repo.git.add('file.txt', 'local.txt')
    repo.git.commit(m='initial')

    repo.git.branch('upstream')
    repo.git.branch('--track', 'side', 'upstream')
    worktree_path = tmp_path / 'side worktree'
    repo.git.worktree('add', str(worktree_path), 'side')

    repo.git.checkout('upstream')
    tracked_file.write_text('upstream change\n')
    repo.git.commit('-am', 'upstream change')
    repo.git.checkout('main')
    monkeypatch.chdir(repo.working_dir)
    try:
        yield repo, worktree_path
    finally:
        repo.close()


@pytest.mark.parametrize(
    'upstream', ['existing', 'deleted_local', 'deleted_remote'])
def test_prunable_worktree_is_skipped(worktree_repo, capsys, upstream):
    repo, worktree_path = worktree_repo
    initial_commit = repo.head.commit
    repo.git.branch('--track', 'z-live', 'upstream')
    repo.branches['z-live'].commit = initial_commit
    repo.git.worktree('add', str(worktree_path.parent / 'live'), 'z-live')

    if upstream == 'deleted_local':
        repo.git.branch('deleted-upstream', 'upstream')
        repo.git.branch('--set-upstream-to', 'deleted-upstream', 'side')
        repo.git.branch('-D', 'deleted-upstream')
    elif upstream == 'deleted_remote':
        ref = 'refs/remotes/origin/deleted-upstream'
        repo.git.remote('add', 'origin', repo.working_dir)
        repo.git.update_ref(ref, repo.branches['upstream'].commit.hexsha)
        repo.git.branch('--set-upstream-to', 'origin/deleted-upstream', 'side')
        repo.git.update_ref('-d', ref)

    shutil.rmtree(worktree_path)
    assert 'prunable' in repo.git.worktree('list', '--porcelain')

    gitup = GitUp(testing=True)
    gitup.should_fetch = False
    gitup.run()

    assert repo.head.commit == initial_commit
    assert repo.branches['side'].commit == initial_commit
    assert repo.branches['z-live'].commit == repo.branches['upstream'].commit
    assert gitup.states == ['prunable worktree', 'fast-forwarding']
    assert 'git worktree prune' in capsys.readouterr().out
    assert 'prunable' in repo.git.worktree('list', '--porcelain')


def test_worktree_removed_after_discovery(worktree_repo, capsys):
    repo, worktree_path = worktree_repo
    initial_commit = repo.head.commit
    gitup = GitUp()
    gitup.should_fetch = False
    shutil.rmtree(worktree_path)

    with pytest.raises(SystemExit) as error:
        gitup.run()

    assert error.value.code == 1
    assert repo.head.commit == initial_commit
    assert repo.branches['side'].commit == initial_commit
    assert 'returned exit status 128' in capsys.readouterr().err


@pytest.mark.parametrize('diverged', [False, True],
                         ids=['fast_forward', 'rebase'])
@pytest.mark.parametrize('checkout', ['replacement', '--detach'],
                         ids=['branch', 'detached'])
def test_worktree_checkout_changed_after_discovery(
        worktree_repo, diverged, checkout):
    repo, worktree_path = worktree_repo
    worktree_git = Git(str(worktree_path))
    if diverged:
        (worktree_path / 'side.txt').write_text('side change\n')
        worktree_git.add('side.txt')
        worktree_git.commit(m='side change')
    repo.git.branch('replacement', 'side')
    initial_commit = repo.head.commit
    side_commit = repo.branches['side'].commit
    gitup = GitUp(testing=True)
    gitup.should_fetch = False

    worktree_git.checkout(checkout)
    (worktree_path / 'local.txt').write_text('uncommitted change\n')
    status = worktree_git.status('--porcelain')

    with pytest.raises(GitError):
        gitup.run()

    assert repo.active_branch.name == 'main'
    assert repo.head.commit == initial_commit
    assert repo.branches['side'].commit == side_commit
    assert repo.branches['replacement'].commit == side_commit
    assert worktree_git.rev_parse('HEAD') == side_commit.hexsha
    assert worktree_git.rev_parse('--abbrev-ref', 'HEAD') == (
        'HEAD' if checkout == '--detach' else 'replacement')
    assert (worktree_path / 'local.txt').read_text() == 'uncommitted change\n'
    assert worktree_git.status('--porcelain') == status
    assert worktree_git.stash('list') == ''


@pytest.mark.parametrize('removal_point', ['before_preflight', 'after_preflight'])
def test_worktree_removed_during_conflict_resolution(
        worktree_repo, monkeypatch, capsys, removal_point):
    repo, worktree_path = worktree_repo
    (worktree_path / 'file.txt').write_text('side change\n')
    Git(str(worktree_path)).commit('-am', 'side change')
    initial_commit = repo.head.commit
    side_commit = repo.branches['side'].commit
    repo.git.config('git-up.rebase.conflict-resolver', 'exit 0')
    gitup = GitUp()
    gitup.should_fetch = False

    if removal_point == 'before_preflight':
        rebase = GitWrapper.rebase

        def remove_after_rebase(self, target):
            try:
                return rebase(self, target)
            except RebaseError:
                shutil.rmtree(worktree_path)
                raise

        monkeypatch.setattr(GitWrapper, 'rebase', remove_after_rebase)
        expected_error = 'Failed to rebase'
    else:
        rebase_in_progress = GitUp._rebase_in_progress

        def remove_after_preflight(repo_path):
            assert rebase_in_progress(repo_path)
            shutil.rmtree(worktree_path)
            return True

        monkeypatch.setattr(GitUp, '_rebase_in_progress',
                            staticmethod(remove_after_preflight))
        expected_error = 'The resolver could not be started'

    with pytest.raises(SystemExit) as error:
        gitup.run()

    assert error.value.code == 1
    assert not worktree_path.exists()
    assert repo.head.commit == initial_commit
    assert repo.branches['side'].commit == side_commit
    assert expected_error in capsys.readouterr().err


@pytest.mark.parametrize('attribute', ['is_dirty', 'change_count'])
def test_missing_worktree_status_reports_git_error(worktree_repo, attribute):
    repo, worktree_path = worktree_repo
    worktree_git = GitWrapper(None, str(worktree_path))
    shutil.rmtree(worktree_path)

    with pytest.raises(GitError):
        getattr(worktree_git, attribute)

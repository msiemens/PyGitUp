# Contribution Guidelines

Whether reporting bugs, discussing ideas or writing code: contributions to
PyGitUp are welcome! Here's how to get started:

1. Check for open issues or open a fresh issue to start a discussion —
   bugfixes can go straight to a pull request, but please discuss new
   features first
2. Fork [the repository](https://github.com/msiemens/PyGitUp/) on GitHub
   and create a new branch off the `master` branch
3. Write a test which shows that the bug was fixed or that the feature
   works as expected
4. Send a pull request and bug the maintainer until it gets merged and
   published :)

## Running the Tests

PyGitUp uses [uv](https://docs.astral.sh/uv/):

    uv sync
    uv run pytest PyGitUp/tests/

Two warnings: the tests run real git commands, and they currently read
your global git config — configured `git-up.*` settings can change test
outcomes.

## Windows Counts

PyGitUp supports native Windows and MinGW, and both run in CI. If your
change touches shell commands, hooks or path handling, it needs to work
there too (see `prepare_windows_log_hook` in `gitup.py` for what that
can involve). If you can't test on Windows, say so in the pull request.

## Pull Requests

Rebase on the current `master` branch before opening the pull request
and after review rounds; don't merge `master` into your branch. Keep
unrelated refactors in separate commits.

## AI-Assisted Contributions

AI-generated code is fine if you have reviewed it yourself, understand it,
and can answer review questions about it. Don't submit output you haven't
read; that just offloads the actual work of reviewing onto others.

Write issues, pull request descriptions and review replies yourself. Using
AI to clean up grammar or wording is fine, pasting generated replies is
not. Two rough sentences of your own are worth a pound of AI-generated
filler.

PyGitUp |Version| |Build Status| |Coverage Status|
==================================================

``PyGitUp`` is a Python implementation of the great
`aanand/git-up/ <https://github.com/aanand/git-up/>`__. It not only
fully covers the abilities of git-up and should be a drop-in replacement,
but also extends it slightly.

Why use ``git up``?
-------------------

    git pull has two problems:

    * It merges upstream changes by default, when it's really more polite to `rebase
      over them <http://gitready.com/advanced/2009/02/11/pull-with-rebase.html>`__,
      unless your collaborators enjoy a commit graph that looks like bedhead.

    * It only updates the branch you're currently on, which means git push will
      shout at you for being behind on branches you don't particularly care about
      right now.

    (https://github.com/aanand/git-up/)

Demonstration
-------------

.. image:: http://i.imgur.com/EC3pvYu.gif

Why use the Python port?
------------------------

I wasn't able to use the original ``git-up``, because I didn't want to install
a whole Ruby suite just for `git-up` and even with Ruby installed, there were
some problems running on my Windows machine. So, my reasons for writing
and using this port are:

1. Windows support.
2. Written in Python ;)

How do I install it?
--------------------

1. Install ``git-up`` via `pip <https://pip.pypa.io/en/latest/installing.html>`__: ``$ pip install git-up``
2. ``cd`` to your project's directory.
3. Run ``git up`` and enjoy!

Note for Windows users:
~~~~~~~~~~~~~~~~~~~~~~~

See `these instructions <http://stackoverflow.com/q/4750806/997063>`__
for installing pip, if you haven't already installed it. And don't forget
to either:

- make your ``Python/Scripts`` and ``Python/Lib/site-packages`` writable for
  you,
- run ``pip`` with admin privileges
- or use ``pip install --user git-up`` and add ``%APPDATA%/Python/Scripts``
  to ``%PATH%``.

Otherwise pip will refuse to install ``git-up`` due to ``Access denied`` errors.

Python 3 compatibility:
~~~~~~~~~~~~~~~~~~~~~~~

``PyGitUp`` is not compatible with Python 3 because some essential 3rd party
libs don't support it. Sorry.

Options and Configuration
-------------------------

Command Line Arguments
~~~~~~~~~~~~~~~~~~~~~~

- ``git up -h`` shows a help message.

- ``git up --quiet`` suppresses all output except for error messages.

- ``git up --version`` shows the current version and optionally checks for
  updates (see below).

Configuration
~~~~~~~~~~~~~

To configure ``PyGitUp``, you can set options in your git config. Run
``git config [--global] git-up.[name] [value]`` to set one of these
options:

-  ``git-up.bundler.check [true|*false*]``: If set to
   ``true``,\ ``PyGitUp`` will check your app for any new bundled gems
   and suggest a ``bundle install`` if necessary.

-  ``git-up.bundler.autoinstall [true|*false*]``: If set to
   ``true``,\ ``PyGitUp`` will run ``bundle install`` automatically.
   Requires ``git-up.bundler.check`` to be true.

-  ``git-up.bundler.local [true|*false*]``: If you've ``bundle package``-ed
   your  project gems, you can tell ``PyGitUp`` to run ``bundle install
   --local`` for you if it finds missing gems. Much faster than just a plain
   old ``bundle install``. Don't worry if you're missing gems, it will
   backtrack to ``bundle install`` if anything goes wrong. Make sure
   ``git-up.bundler.autoinstall`` is also set to ``true`` or it won't do
   anything.

- ``git-up.bundler.rbenv [true|*false*]``: If you have rbenv installed,
  you can tell ``PyGitUp`` to run ``rbenv rehash`` for you after it installs
  your gems so any binaries will be available right away. Make sure ``git-up
  .bundler.autoinstall`` is also set to ``true`` or it won't do anything.

-  ``git-up.fetch.prune [*true*|false]``: If set to ``true``,
   ``PyGitUp`` will append the ``--prune``\ option to ``git fetch`` and
   thus remove any remote tracking branches which no longer exist on
   the remote (see `git fetch
   --help <http://linux.die.net/man/1/git-fetch>`__).

-  ``git-up.fetch.all [true|*false*]``: If set to ``false``, ``PyGitUp``
   will only fetch remotes for which there is at least one local
   tracking branch. Setting this option will make ``git up`` always fetch
   from all remotes, which is useful if e.g. you use a remote to push to
   your CI system but never check those branches out.

-  ``git-up.rebase.arguments [string]``: If set, ``PyGitUp`` will use
   this string as additional arguments when calling ``git rebase``.
   Example: ``--preserve-merges`` to recreate merge commits in the
   rebased branch.

-  ``git-up.rebase.auto [*true*|false]``: If set to ``false``,
   ``PyGitUp`` won't rebase your branches for you but notify you that
   they diverged. This can be useful if you have a lot of in-progress
   work that you don't want to deal with at once, but still want to
   update other branches.

-  ``git-up.rebase.log-hook [cmd]``: Runs ``cmd`` every time a branch
   is rebased or fast-forwarded, with the old head as ``$1`` and the new
   head as ``$2``. This can be used to view logs or diffs of incoming
   changes. Example:
   ``echo "changes on $1:"; git log --oneline --decorate $1..$2``.

- ``git-up.rebase.show-hashes [true|*false*]``: If set to ``true``,
  ``PyGitUp`` will show the hashes of the current commit (or the point
  where the rebase starts) and the target commit like ``git pull`` does.

New in v1.0.0:
~~~~~~~~~~~~~~

- ``git-up.updates.check [*true*|false]``: When running ``git up --version``,
  it shows the version number and checks for updates. If you feel
  uncomfortable with it, just set it to ``false`` to turn off the checks.

Credits
-------

The original ``git-up`` has been written by aanand:
`aanand/git-up/ <https://github.com/aanand/git-up/>`__.


Changelog
---------

v1.2.2 (*2015-02-23*)
~~~~~~~~~~~~~~~~~~~~~

- Now updates submodules when called from ``git submodule foreach`` (`#8 <https://github.com/msiemens/PyGitUp/issues/8>`__).

v1.2.1 (*2014-12-16*)
~~~~~~~~~~~~~~~~~~~~~

- Fixed a problem with ``setuptools 8.x`` (`#19 <https://github.com/msiemens/PyGitUp/issues/19>`__).
- 3rd party dependencies have been updated

v1.2.0 (*2014-12-10*)
~~~~~~~~~~~~~~~~~~~~~

- Added an option to show hashes when fast-forwarding/rebasing like ``git pull``
  does (``git-up.rebase.show-hashes``).
- Fixed a bug when having branches with both local tracking branches and
  remote tracking branches (`#17 <https://github.com/msiemens/PyGitUp/issues/17>`__).

v1.1.5 (*2014-11-19*)
~~~~~~~~~~~~~~~~~~~~~

- 3rd party dependencies have been updated to fix a problem with a 3rd party
  library (`#18 <https://github.com/msiemens/PyGitUp/issues/18>`__).

v1.1.4 (*2014-04-18*)
~~~~~~~~~~~~~~~~~~~~~

- Fixed some typos in README and ``PyGitUp`` output.
- 3rd party dependencies have been updated.

v1.1.3 (*2014-03-23*)
~~~~~~~~~~~~~~~~~~~~~

- ``ahead of upstream`` messages are now cyan (see `aanand/git-up#60 <https://github.com/aanand/git-up/issues/60>`__).
- Fixed problem when using % in the log hook (`#11 <https://github.com/msiemens/PyGitUp/issues/11>`__).

v1.1.2 (*2013-10-08*)
~~~~~~~~~~~~~~~~~~~~~

- Fixed problems with the dependency declaration.

v1.1.1 (*2013-10-07*)
~~~~~~~~~~~~~~~~~~~~~

- Fix for `#7 <https://github.com/msiemens/PyGitUp/issues/7>`__
  (AttributeError: 'GitUp' object has no attribute 'git') introduced by
  v1.1.0.

v1.1.0 (*2013-10-07*)
~~~~~~~~~~~~~~~~~~~~~

- Prior to v1.1.0, ``PyGitUp`` tried to guess the upstream branch for a local
  branch by looking for a branch on any remote with the same name. With v1.1.0,
  ``PyGitUp`` stops guessing and uses the upstream branch config instead.

  This by the way fixes issue `#6 <https://github.com/msiemens/PyGitUp/issues/6>`__
  (``git up`` doesn't work with local only branches).

  **Note:**
  This change may break setups, where a local branch accidently has
  the same name as a remote branch without any tracking information set. Prior
  to v1.1.0, ``git up`` would still fetch and rebase from the remote branch.
  If you run into troubles with such a setup, setting tracking information
  using ``git branch -u <remote>/<remote branch> <local branch>`` should help.

- 3rd party dependencies have been updated.

- Allows to run ``git up --version`` from non-git dirs, too.

v1.0.0 (*2013-09-05*)
~~~~~~~~~~~~~~~~~~~~~

Finally ``PyGitUp`` reaches 1.0.0. You can consider it stable now :)

- Added a comprehensive test suite, now with a coverage of about 90%.
- Lots of code cleanup.
- Added option ``-h`` to display a help screen (``--help`` **won't** work, because
  ``git`` catches this option and handles it before ``PyGitUp`` can do).
- Added option ``--version`` to show, what version of ``PyGitUp`` is running.
  Also checks for updates (can be disabled, see configuration).
- Added option ``--quiet`` to be quiet and only display error messages.

v0.2.3 (*2013-06-05*)
~~~~~~~~~~~~~~~~~~~~~

- Fixed issue `#4 <https://github.com/msiemens/PyGitUp/issues/4>`__ (ugly
  exception if remote branch has been deleted).

v0.2.2 (*2013-05-04*)
~~~~~~~~~~~~~~~~~~~~~

- Fixed issue `#3 <https://github.com/msiemens/PyGitUp/issues/3>`__ (didn't
  return to previous branch).


v0.2.1 (*2013-03-18*)
~~~~~~~~~~~~~~~~~~~~~

- Fixed problem: check-bundler.rb has not been installed when installing via
  PyPI (problems with setup.py).

v0.2 (*2013-03-18*)
~~~~~~~~~~~~~~~~~~~

- Incorporated `aanand/git-up#41 <https://github
  .com/aanand/git-up/pull/41>`__: Support for ``bundle install --local`` and
  ``rbenv rehash``.
- Fixed issue `#1 <https://github.com/msiemens/PyGitUp/issues/1>`__ (strange
  output buffering when having multiple remotes to fetch from).
- Some under-the-hood improvements.

v0.1 (*2013-03-14*)
~~~~~~~~~~~~~~~~~~~

- Initial Release

.. |Build Status| image:: http://img.shields.io/travis/msiemens/PyGitUp/master.svg?style=flat-square
   :target: https://travis-ci.org/msiemens/PyGitUp

.. |Coverage Status| image:: http://img.shields.io/coveralls/msiemens/PyGitUp/master.svg?style=flat-square
  :target: https://coveralls.io/r/msiemens/PyGitUp

.. |Version| image:: http://img.shields.io/pypi/v/git-up.svg?style=flat-square
  :target: https://pypi.python.org/pypi/git-up

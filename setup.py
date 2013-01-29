from setuptools import setup, find_packages

setup(
    name = "PyGitUp",
    version = "0.1dev",
    packages = find_packages(),
    scripts = ['PyGitUp/gitup.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['GitPython', 'colorama', 'termcolor'],

    entry_points = {
        'console_scripts': [
            'git-up = gitup:run'
        ]
    },

    package_data = {
        # If any package contains *.txt or *.md files, include them:
        '': ['*.txt', '*.md', 'LICENCE']
    },

    # development metadata
    use_2to3 = True,
    zip_safe = True,

    # metadata for upload to PyPI
    author = "Markus Siemens",
    author_email = "markus@m-siemens.de",
    description = "TODO",
    license = "MIT",
    keywords = "git git-up helper",
    url = "https://github.com/msiemens/PyGitUp",

    # could also include long_description, download_url, classifiers, etc.
)

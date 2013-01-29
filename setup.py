from setuptools import setup, find_packages

setup(
    name = "PyGitUp",
    version = "0.1dev",
    scripts = ['PyGitUp.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['GitPython', 'colorama', 'termcolor'],

    entry_points = {
        'console_scripts': [
            'git-up = PyGitUp:run'
        ]
    },

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
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
    keywords = "TODO",
    url = "TODO",

    # could also include long_description, download_url, classifiers, etc.
)

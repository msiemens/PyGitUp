# coding=utf-8
from setuptools import setup, find_packages
try:
    from pip.req import parse_requirements
except ImportError:
    def requirements(f):
        reqs = open(f, 'r').read().splitlines()
        reqs = [r for r in reqs if not r.strip().startswith('#')]
        return reqs
else:
    def requirements(f):
        install_reqs = parse_requirements(f)
        reqs = [str(r.req) for r in install_reqs]
        return reqs

setup(
    name = "git-up",
    version = "1.0.0",
    packages = find_packages(),
    scripts = ['PyGitUp/gitup.py'],
    install_requires = requirements('requirements.txt'),

    # Tests
    test_suite="nose.collector",
    tests_require = requirements('dev-requirements.txt'),

    entry_points = {
        'console_scripts': [
            'git-up = gitup:run'
        ]
    },

    package_data = {
        'PyGitUp': ['check-bundler.rb']
    },

    zip_safe = False,

    # metadata for upload to PyPI
    author = "Markus Siemens",
    author_email = "markus@m-siemens.de",
    description = "A python implementation of 'git up'",
    license = "MIT",
    keywords = "git git-up",
    url = "https://github.com/msiemens/PyGitUp",
    classifiers  = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Version Control",
        "Topic :: Utilities"
    ],

    long_description = open('README.rst', 'r').read()
    # could also include download_url etc.
)

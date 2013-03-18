# coding=utf-8
import sys
from setuptools import setup, find_packages

README = None
with open('README.rst', 'r') as f:
    README = f.read()

setup(
    name = "git-up",
    version = "0.2",
    packages = find_packages(),
    scripts = ['PyGitUp/gitup.py'],
    install_requires = ['GitPython', 'colorama', 'termcolor'],

    entry_points = {
        'console_scripts': [
            'git-up = gitup:run'
        ]
    },

    package_data = {
        'PyGitUp': ['check-bundler.rb']
    },

    # development metadata
    zip_safe = True,

    # metadata for upload to PyPI
    author = "Markus Siemens",
    author_email = "markus@m-siemens.de",
    description = "A python implementation of 'git up'",
    license = "MIT",
    keywords = "git git-up",
    url = "https://github.com/msiemens/PyGitUp",
    classifiers  = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Version Control",
        "Topic :: Utilities"
    ],

    long_description = README
    # could also include download_url etc.
)

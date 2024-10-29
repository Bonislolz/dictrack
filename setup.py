from os import path

from setuptools import find_packages, setup

working_directory = path.abspath(path.dirname(__file__))


try:
    with open(path.join(working_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except TypeError:
    with open(path.join(working_directory, "README.md")) as f:
        long_description = f.read()

setup(
    name="dictrack",
    version="1.1.0",
    author="Tim Liao",
    author_email="bonis0324work@gmail.com",
    description="A componentized dictionary tracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    install_requires=[
        "dictor >= 0.1.12",
        "python-redis-lock == 3.7.0;python_version == '2.7'",
        "python-redis-lock >= 4.0.0;python_version >= '3.7'",
        "hiredis == 1.1.0;python_version == '2.7'",
        "redis == 3.5.3;python_version == '2.7'",
        "redis[hiredis] >= 5.1.1;python_version >= '3.7'",
        "six >= 1.16.0",
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, !=3.6.*",
)

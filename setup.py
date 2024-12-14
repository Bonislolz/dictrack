from os import path

from setuptools import find_packages, setup

working_directory = path.abspath(path.dirname(__file__))


try:
    with open(path.join(working_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except TypeError:
    with open(path.join(working_directory, "README.md")) as f:
        long_description = f.read()


def get_version():
    version_file = path.join(working_directory, "app/dictrack/__init__.py")
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("dictrack", version_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError:
        import imp

        module_name = "dictrack"
        module = imp.load_source(module_name, version_file)

    return module.__version__


setup(
    name="dictrack",
    version=get_version(),
    author="Tim Liao",
    author_email="bonis0324work@gmail.com",
    description="A componentized dictionary tracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    install_requires=[
        "dictor >= 0.1.12, < 1.0",
        "six >= 1.16.0, < 2.0",
        "tzlocal == 2.1;python_version == '2.7'",
        "apscheduler == 3.8.1;python_version == '2.7'",
        "apscheduler >= 3.10.4, < 4.0;python_version >= '3.7'",
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, !=3.6.*",
    extras_require={
        "redis": [
            "python-redis-lock == 3.7.0;python_version == '2.7'",
            "python-redis-lock >= 4.0.0, < 5.0;python_version >= '3.7'",
            "hiredis == 1.1.0;python_version == '2.7'",
            "redis == 3.5.3;python_version == '2.7'",
            "redis[hiredis] >= 5.1.1, < 6.0;python_version >= '3.7'",
        ],
        "memory": [
            "sortedcontainers >= 2.4.0, < 3.0",
        ],
        "mongodb": [
            "pymongo == 3.13.0;python_version == '2.7'",
            "pymongo >= 3.0, < 5.0;python_version >= '3.7'",
        ],
        "gevent": [
            "apscheduler[gevent] == 3.8.1;python_version == '2.7'",
            "apscheduler[gevent] >= 3.10.4, < 4.0;python_version >= '3.7'",
        ],
    },
)

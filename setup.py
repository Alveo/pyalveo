from setuptools import setup
import io, re, os


def read(*names, **kwargs):
    with io.open(
            os.path.join(os.path.dirname(__file__), *names),
            encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='pyalveo',
    version=find_version('pyalveo', '__init__.py'),
    description="A Python library for interfacing with the Alveo API",
    long_description=read('README.rst'),

    url='https://github.com/Alveo/pyalveo',

    maintainer='Steve Cassidy',
    maintainer_email='Steve.Cassidy@mq.edu.au',
    license = 'BSD',

    keywords='alveo hcsvlab python library',

    packages = ['pyalveo'],

    install_requires=[
        "python-dateutil",
        "requests",
        "oauthlib",
        "requests-oauthlib",
    ],

    tests_require=[
        "requests-mock"
    ],

    test_suite='tests'
    )

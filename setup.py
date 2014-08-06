from setuptools import setup, find_packages
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'readme.rst'), encoding='utf-8') as f:
	long_description = f.read()

setup(
	name='pyalveo',
	version='0.3',
	description="A Python library for interfacing with the HCSvLab/Alveo API",
	long_description=long_description,

	url='https://github.com/Alveo/pyhcsvlab',

	maintainer='Steve Cassidy',
	maintainer_email='Steve.Cassidy@mq.edu.au',
	license = 'BSD',

	keywords='alveo HCSvLab python library',

	packages = find_packages(exclude=['contrib', 'docs', 'tests*']),
	
    install_requires=[
        "pyyaml",
        "python-dateutil",
    ],
	)
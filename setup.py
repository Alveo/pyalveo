from setuptools import setup, find_packages
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'readme.md'), encoding='utf-8') as f:
	long_descripotion = f.read()

setup(
	name='pyalveo',
	version='0.2',
	description="A Python library for interfacing with the HCSvLab/Alveo API",
	long_descripotion=long_descripotion,

	url='https://github.com/Alveo/pyhcsvlab',

	author='',
	author_email='',
	license = 'BSD',

	keywords='alveo HCSvLab python library',

	packages = find_packages(exclude=['contrib', 'docs', 'tests*']),
	
    install_requires=[
        "pyyaml",
        "python-dateutil",
    ],
	)
from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='coinswitch-client',
    version='0.1.0',
    description='Python client for CoinSwitch PRO Futures API (Ed25519 auth)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Virencq/coinswitch-client',
    author='Virencq',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Office/Business :: Financial',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='coinswitch futures crypto trading api client',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['requests', 'cryptography'],
    extras_require={
        'dotenv': ['python-dotenv'],
    },
    project_urls={
        'Source': 'https://github.com/Virencq/coinswitch-client',
    },
    python_requires='>=3.8',
)

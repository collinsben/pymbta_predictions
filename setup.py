from setuptools import setup, find_packages

setup(
    name='pymbta_predictions',
    author='Ben Collins',
    version='0.1.0',
    packages=find_packages(include=[
        'pymbta_predictions',
    ]),
    install_requires=[
        'requests',
    ],
)

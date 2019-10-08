from setuptools import setup

setup(
    name='proxy_manager',    # This is the name of your PyPI-package.
    version='0.1',                          # Update the version number for new releases
    packages=setuptools.find_packages(),
    install_requires=[
          'requests'
      ],
)
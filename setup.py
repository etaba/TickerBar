from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
  name = 'tickerbar',
  packages = ['tickerbar'],
  version = '0.5',
  description = 'Stock quotes on the mac touch bar',
  author = 'Eric Taba',
  author_email = 'eptaba@gmail.com',
  url = 'https://github.com/etaba/tickerbar', # use the URL to the github repo
  download_url = 'https://github.com/etaba/tickerbar/tarball/0.1',
  keywords = [
    'mac',
    'touch bar',
    'stock',
    'stocks,'
    'macbook',
    'ticker',
    'quotes'
    ], 
  classifiers = [],
  install_requires=[
        'pinance'
  ],
  scripts=['bin/tickerbar'],
  include_package_data=True
)


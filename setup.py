import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-seuranta',
    version=__import__('seuranta').__version__,
    description='Django app for live gps tracking of orienteering events',
    long_description=README,
    author='Raphael Stefanini',
    author_email='rphl@rphl.net',
    url='http://github.com/rphlo/django-seuranta',
    packages=find_packages(),
    license="MIT License",
    classifiers=[
      'Development Status :: Beta',
      'Environment :: Web Environment',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Framework :: Django',
    ],
    install_requires=['django-timezone-field >= 1.0'],
)

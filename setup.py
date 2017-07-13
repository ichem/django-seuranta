import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='django-seuranta',
    version=__import__('seuranta').__version__,
    packages=['seuranta'],
    include_package_data=True,
    license="MIT License",
    description='Live gps tracking server for orienteering events',
    long_description=README,
    url='http://github.com/rphlo/django-seuranta',
    author='Raphael Stefanini',
    author_email='rphl@rphl.net',
    zip_safe=False,
    classifiers=[
        'Development Status :: Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    install_requires=required
)

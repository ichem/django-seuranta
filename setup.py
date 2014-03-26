import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-seuranta',
    version=__import__('seuranta').__version__,
    packages=['seuranta'],
    include_package_data=True,
    license="MIT License",
    description='Django app for live gps tracking of orienteering events',
    long_description=README,
    url='http://github.com/rphlo/django-seuranta',
    author='Raphael Stefanini',
    author_email='rphl@rphl.net',
    zip_safe=False,
    package_data={
        'seuranta': [
            'templates/seuranta/*.html',
            'static/seuranta/*',
        ],
    },
    classifiers=[
      'Development Status :: Beta',
      'Environment :: Web Environment',
      'Framework :: Django',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
    ],
    install_requires=['django-timezone-field >= 1.0', 'django-country', 'django-globetrotting', 'requests', 'simplejson'],
)

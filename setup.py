import re
from os import path
from setuptools import setup, find_packages


def read(*parts):
    return open(path.join(path.dirname(__file__), *parts)).read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='simple-invoice',
    version=find_version('invoice', '__init__.py'),
    description='Invoicing for Django',
    author='tloiret',
    author_email='mathiaswolff@mac.com',
    url='https://bitbucket.org/mwolff/django-simple-invoice',
    packages=find_packages(),
    zip_safe=False,
    package_data={
        'menu_manager': [
            'locale/*/LC_MESSAGES/*',
            'templates/invoice/*',
            'static/*',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    install_requires=[
        'django>=1.5',
        'reportlab>=2.7',
        'PyPDF2>=1.20',
        'django-extensions>=1.3.3',
    ]
)

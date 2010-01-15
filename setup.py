import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-authority',
    version='0.4',
    description="A Django app that provides generic per-object-permissions for Django's auth app.",
    long_description=read('README'),
    author='Jannis Leidel',
    author_email='jannis@leidel.info',
    license='BSD',
    url='http://bitbucket.org/jezdez/django-authority/',
    download_url='http://bitbucket.org/jezdez/django-authority/downloads/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    package_data = {
        'authority': [
            'fixtures/test.json',
            'templates/authority/*.html',
            'templates/admin/edit_inline/action_tabular.html',
            'templates/admin/permission_change_form.html',
        ]
    },
    zip_safe=False,
)

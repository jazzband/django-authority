from setuptools import setup, find_packages

setup(
    name='django-authority',
    version='0.0.1',
    description="A Django app that provides generic per-object-permissions for Django's auth app.",
    long_description=open('README').read(),
    author='Jannis Leidel',
    author_email='jannis@leidel.info',
    url='http://bitbucket.org/jezdez/django-authority/',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
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
            'templates/authority/*.html',
        ]
    },
    zip_safe=False,
    install_requires=(
        'decorator>=3.0.1'
    ),
)

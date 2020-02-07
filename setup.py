import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="django-authority",
    use_scm_version=True,
    description=(
        "A Django app that provides generic per-object-permissions "
        "for Django's auth app."
    ),
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    author="Jannis Leidel",
    author_email="jannis@leidel.info",
    license="BSD",
    url="https://github.com/jazzband/django-authority/",
    packages=find_packages(exclude=("example", "example.*")),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Framework :: Django",
    ],
    install_requires=["django"],
    setup_requires=["setuptools_scm"],
    include_package_data=True,
    zip_safe=False,
)

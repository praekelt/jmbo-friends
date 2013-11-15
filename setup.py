from setuptools import setup, find_packages

setup(
    name='jmbo-friends',
    version='0.2.4',
    description='Friends and badges for Jmbo.',
    long_description = open('README.rst', 'r').read() + open('AUTHORS.rst', 'r').read() + open('CHANGELOG.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekelt.com',
    license='BSD',
    url='http://github.com/praekelt/jmbo-friends',
    packages = find_packages(),
    install_requires = [
        'jmbo-foundry',
    ],
    include_package_data=True,
    tests_require=[
        'django-setuptest',
    ],
    test_suite="setuptest.SetupTestSuite",
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    zip_safe=False,
)

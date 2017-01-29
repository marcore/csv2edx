from setuptools import setup

setup(
    name='csv2edx',
    version='0.2.0',
    author='Marco Re',
    author_email='marco.re@polimi.it',
    packages=['csv2edx','csv2edx.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/csv2edx/',
    license='LICENSE.txt',
    description='Convert from csv to edx XML format course content files',
    long_description=open('README.txt').read(),
    entry_points={
        'console_scripts': [
            'csv2edx = csv2edx.main:CommandLine',
            ],
        },
    install_requires=['lxml == 3.2.0',
                      'path.py <= 7.7.1',
                      'pysrt == 1.0.1',
                      'dropbox == 7.1.1'
                      ],
    package_dir={'csv2edx': 'csv2edx'},
    package_data={ 'csv2edx': ['render/*',] },
    # data_files = data_files,
    test_suite = "csv2edx.test",
)

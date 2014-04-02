=========
csv2edx
=========

Converts a csv format to edX XML format.
Inspired by latex2edx tool by mitx (https://github.com/mitocw/latex2edx)

A pre-parse phase can be activated with flag "pre-parse" if the csv file contains extra columns not needed.
Columns needed are CHAPTERNAME,SEQUENTIALNAME,VERTICALNAME,[VERTICAL_URL_NAME],LINK.
VERTICAL_URL_NAME is optional and will be generated if missed 
At this moment LINK is the url of youtube video as currently only video vertical are supported
    
The script can be run from any directory and generated files outputs to currently directory

Installation
============

    pip install -e git+https://github.com/marcore/csv2edx.git#egg=csv2edx

Note that xmllint and lxml are required; for ubuntu, this may work:

    apt-get install libxml2-utils python-lxml

Usage
=====

Usage: csv2edx [options] filename.csv

	Options:
	  --version             show program's version number and exit
	  -h, --help            show this help message and exit
	  -v, --verbose         verbose error messages
	  -o OUTPUT_FN, --output-xbundle=OUTPUT_FN
	                        Filename for output xbundle file
	  -d OUTPUT_DIR, --output-directory=OUTPUT_DIR
	                        Directory name for output course XML files
	  -m, --merge-chapters  merge chapters into existing course directory
	  -p, --prepare-csv     Prepare csv file to be in the csv2edx format
	  -c COLS2PRESERVE, --cols2preserve=COLS2PRESERVE
	                        Columns to preserve in the final format of csv file
	                        (see -p option)

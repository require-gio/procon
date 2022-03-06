import setuptools
from os.path import dirname, join

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="procon",
    version="0.0.7",
    author="Giorgi Lomidze",
    author_email="giorgi@giolom.com",
    description="Conformance Checking on BPMN models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    url='https://github.com/require-gio/procon',
    license='GPL 3.0',
    python_requires='>=3.7',
    py_modules=["procon"],
    install_requires=[
        'pm4py==2.2.19.2',
        'pm4pycvxopt',
        'psutil'
    ],
    project_urls={
        'Documentation': 'https://github.com/require-gio/procon',
        'Source': 'https://github.com/require-gio/procon',
        'Tracker': 'https://github.com/require-gio/procon/issues',
    }
)
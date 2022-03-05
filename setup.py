import setuptools
from os.path import dirname, join

with open("README.md", "r") as fh:
    long_description = fh.read()

def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()

setuptools.setup(
    name="procon",
    version="0.0.1",
    author="Giorgi Lomidze",
    author_email="giorgi@giolom.com",
    description="Conformance Checking on BPMN models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLL v3 License",
        "Operating System :: OS Independent",
    ],
    url='https://github.com/require-gio/procon',
    license='GPL 3.0',
    python_requires='>=3.7',
    py_modules=["procon"],
    install_requires=read_file("requirements.txt").split("\n"),
    project_urls={
        'Documentation': 'https://github.com/require-gio/procon',
        'Source': 'https://github.com/require-gio/procon',
        'Tracker': 'https://github.com/require-gio/procon/issues',
    }
)
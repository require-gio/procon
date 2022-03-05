import setuptools
from os.path import dirname, join


with open("README.md", "r") as fh:
    long_description = fh.read()

def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()

setuptools.setup(
    name="procon",                     # This is the name of the package
    version="0.0.1",                        # The initial release version
    author="Giorgi Lomidze",                     # Full name of the author
    author_email="giorgi@giolom.com",
    description="Conformance Checking on BPMN models",
    long_description=long_description,      # Long description read from the the readme file
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),    # List of all python modules to be installed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLL v3 License",
        "Operating System :: OS Independent",
    ],
    url='https://github.com/require-gio/procon',
    license='GPL 3.0',
    python_requires='>=3.6',                # Minimum version requirement of the package
    py_modules=["procon"],             # Name of the python package
    package_dir={'':'procon'},     # Directory of the source code of the package
    install_requires=read_file("requirements_stable.txt").split("\n")  # Install other dependencies if any
)
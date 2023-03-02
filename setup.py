import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="keller_protocol",
    version="1.0.0",
    author="Lukas Weber",
    author_email="engineering@keller-druck.com",
    description="Python package source for KELLER protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KELLERAGfuerDruckmesstechnik/keller_protocol_python",
    install_requires=["pyserial"]
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

from setuptools import setup

setup(
    name="tap-gharchive",
    version="0.1.0",
    py_modules=["tap_gharchive"],
    install_requires=[
        "tap-rest-api-msdk",
    ],
    entry_points={
        "console_scripts": ["tap-gharchive=tap_gharchive:TapGHArchive.cli"],
    },
) 
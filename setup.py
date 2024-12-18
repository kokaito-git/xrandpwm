from setuptools import setup, find_packages

setup(
    name="xrandpwm",
    version="0.0.5",
    packages=find_packages(),
    description="xrandr screen/monitors info collector classes (intended for bspwm)",
    author="kokaito",
    author_email="kokaito.git@gmail.com",
    url="https://github.com/kokaito-git/xrandpwm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
        "pydantic",
        "kcolors",
    ],
)

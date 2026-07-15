from setuptools import setup, find_packages

setup(
    name="codevault-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click", "requests", "rich"],
    entry_points={
        "console_scripts": [
            "codevault=codevault_cli.main:cli",
        ],
    },
)
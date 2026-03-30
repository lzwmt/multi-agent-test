from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-mdproc",
    version="1.0.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "markdown>=3.5.0",
        "weasyprint>=60.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-mdproc=cli_anything.mdproc.mdproc_cli:main",
        ],
    },
    python_requires=">=3.10",
)

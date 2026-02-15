from setuptools import setup

setup(
    name="flakyfence",
    version="0.1.0",
    description="Test pollution bisection & shared state forensics engine",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    py_modules=["flakyfence", "flakyfence_plugin"],
    entry_points={
        "console_scripts": ["flakyfence=flakyfence:main"],
        "pytest11": ["flakyfence = flakyfence_plugin"],
    },

    install_requires=["pytest>=7.0"],
    python_requires=">=3.8",
    author="FlakyFence",
    url="https://github.com/flakyfence/flakyfence",
    license="MIT",
    classifiers=[
        "Framework :: Pytest",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

from setuptools import setup, find_packages

setup(
    name="proxmox-nli",
    version="0.1.0",
    description="Natural Language Interface for Proxmox VE",
    author="Proxmox NLI Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "flask",
        "nltk",
        "spacy",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "proxmox-nli=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
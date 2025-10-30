from setuptools import setup, find_packages
from pathlib import Path

# Cargar README si existe
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="dropshipping-inspector",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "beautifulsoup4",
        "lxml",
        "rich",
        "python-dotenv",
    ],
    entry_points={
        'console_scripts': [
            'inspector=inspector.cli:main',
        ],
    },
    author="Jorge Abisay Quezada Montes",
    author_email="tuemail@ejemplo.com",
    description="Herramienta de scraping y análisis para dropshipping con validación de licencias Gumroad.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="dropshipping, scraping, ecommerce, gumroad, inspector",
    url="https://gumroad.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)

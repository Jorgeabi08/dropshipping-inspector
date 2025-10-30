from setuptools import setup, find_packages

setup(
    name="dropshipping-inspector",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "beautifulsoup4",
        "rich",
        "lxml",
    ],
    entry_points={
        "console_scripts": [
            "dropshipping-inspector=inspector.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Jorge Abisay Quezada Montes",
    description="Herramienta de scraping y análisis para dropshipping con verificación de licencia Gumroad.",
    url="https://gumroad.com",
)

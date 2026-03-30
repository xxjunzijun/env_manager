from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="env_manager",
    version="0.1.0",
    author="xxjunzijun",
    author_email="",
    description="环境变量管理工具 - 轻松管理、切换、备份项目环境配置",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xxjunzijun/env_manager",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "envmanager=env_manager.main:main",
        ],
    },
)

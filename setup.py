from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mech-drawing-analyzer",
    version="0.1.0",
    author="Rui Li",
    author_email="ray.rui.2013@gmail.com",
    description="AI-powered mechanical drawing analysis and compliance checking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/raylirui-self/mech-drawing-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "ui": [
            "gradio>=4.0.0",
            "plotly>=5.17.0",
        ],
        "llm": [
            "openai>=1.0.0",
            "anthropic>=0.18.0",
            "ollama>=0.1.7",
        ],
        "finetune": [
            "torch>=2.0.0",
            "transformers>=4.35.0",
            "peft>=0.6.0",
            "bitsandbytes>=0.41.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mech-analyze=src.analyzer:main",
            "mech-ui=app.gradio_app:main",
        ],
    },
)
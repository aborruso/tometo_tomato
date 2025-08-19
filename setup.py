from setuptools import setup, find_packages

setup(
    name='tometo_tomato',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'duckdb',
        'rapidfuzz', # Although optional in script, it's a primary dependency
    ],
    entry_points={
        'console_scripts': [
            'tometo_tomato=fuzzy_join:main',
        ],
    },
    author='Your Name', # TODO: Replace with actual author name
    author_email='your.email@example.com', # TODO: Replace with actual author email
    description='A utility for fuzzy joining tabular data using DuckDB.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/aborruso/tometo_tomato', # TODO: Replace with actual project URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # TODO: Adjust license if needed
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)

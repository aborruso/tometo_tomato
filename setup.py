from setuptools import setup, find_packages

setup(
    packages=find_packages(where='src'),
    include_package_data=True,
    use_scm_version={
        "write_to": "src/_version.py",
        "version_scheme": "release-branch-semver",
        "local_scheme": "dirty-tag",
    },
    setup_requires=['setuptools_scm'],
)
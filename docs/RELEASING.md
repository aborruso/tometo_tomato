# Releasing and Versioning `tometo_tomato`

This document outlines the process for releasing and versioning the `tometo_tomato` project, leveraging Git tags and `setuptools_scm` for automatic version management.

## Versioning Strategy

`tometo_tomato` uses `setuptools_scm` to automatically determine its version based on Git tags. This means you do not need to manually update version numbers in `pyproject.toml` or `setup.py`. The version is derived directly from your Git history.

The version format typically follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

-   **`MAJOR`**: Incremented for incompatible API changes.
-   **`MINOR`**: Incremented for adding functionality in a backward-compatible manner.
-   **`PATCH`**: Incremented for backward-compatible bug fixes.

`setuptools_scm` also handles development versions:
-   `X.Y.Z.devN`: Indicates a development version, `N` commits after tag `X.Y.Z`.
-   `+dirty`: Appended if there are uncommitted changes in your working directory.

## Release Process

Follow these steps to create a new release:

1.  **Ensure Your Changes Are Committed**:
    Before creating a release tag, make sure all the changes you want to include in the release are committed to your `main` branch (or the branch you are releasing from).

    ```bash
    git status
    git add .
    git commit -m "feat: Prepare for vX.Y.Z release" # Or appropriate commit message
    ```

2.  **Create a Git Tag**:
    Create an annotated Git tag for the new version. This tag will be used by `setuptools_scm` to determine the release version.

    ```bash
    git tag -a vX.Y.Z -m "Release vX.Y.Z"
    ```
    Replace `X.Y.Z` with the actual version number (e.g., `v1.0.0`).

3.  **Push the Tag to GitHub**:
    Push the newly created tag to your GitHub repository.

    ```bash
    git push origin vX.Y.Z
    ```
    You might also want to push all commits if you haven't already:
    ```bash
    git push origin main
    ```

4.  **GitHub Actions (Optional but Recommended)**:
    If your repository is configured with GitHub Actions for releases (e.g., a workflow that triggers on new tags), pushing the tag will automatically trigger the build, testing, and release process (e.g., publishing to PyPI, creating a GitHub Release).

5.  **Verify the Version**:
    After the release process is complete (and if you've installed the new version), you can verify the version of the `tometo_tomato` tool:

    ```bash
    python3 src/tometo_tomato.py --version
    ```
    This should output the exact version you tagged (e.g., `tometo_tomato.py vX.Y.Z`).

## Development Workflow

During development, `setuptools_scm` will automatically generate a version string that reflects the current state of your repository. For example, if your last tag was `v0.1.0` and you have made 5 commits since then, your development version might look like `0.1.0.dev5`. If you have uncommitted changes, it will append `+dirty` (e.g., `0.1.0.dev5+dirty`).

This provides immediate feedback on the exact code state you are working with, which is invaluable for debugging and collaboration.

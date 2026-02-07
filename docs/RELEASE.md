# Release

This project publishes to PyPI from a GitHub Release.

Prereqs (first time only)
- Configure this GitHub repo as a trusted publisher on PyPI for `tometo_tomato`.

Create a release (example `0.0.1`)
1. `git tag v0.0.1`
2. `git push origin v0.0.1`
3. `gh release create v0.0.1 --generate-notes`

Notes
- The GitHub Actions workflow `release.yml` runs on release publish and uploads to PyPI.
- If you prefer a local upload, you can run:
  - `python -m build`
  - `twine upload dist/*`

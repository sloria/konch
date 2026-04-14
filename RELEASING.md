# Releasing

1. Bump version in `pyproject.toml` and update the changelog
   with today's date.
2. `uv sync`
3. Commit: `git commit -m "Bump version and update changelog"`
4. Tag the commit: `git tag x.y.z`
5. Push: `git push --tags origin main`. CI will take care of the
   PyPI release.

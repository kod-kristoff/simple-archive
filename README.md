# simple-archive

[![PyPI version](https://badge.fury.io/py/simple-archive.svg)](https://pypi.org/project/simple-archive/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/simple-archive)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/simple-archive)](https://pypi.org/project/simple-archive/)

[![Maturity badge - level 2](https://img.shields.io/badge/Maturity-Level%202%20--%20First%20Release-yellowgreen.svg)](https://github.com/spraakbanken/getting-started/blob/main/scorecard.md)
[![Stage](https://img.shields.io/pypi/status/simple-archive)](https://pypi.org/project/simple-archive/)

[![Code Coverage](https://codecov.io/gh/spraakbanken/simple-archive/branch/main/graph/badge.svg)](https://codecov.io/gh/spraakbanken/simple-archive/)

[![CI(check)](https://github.com/spraakbanken/simple-archive/actions/workflows/check.yml/badge.svg)](https://github.com/spraakbanken/simple-archive/actions/workflows/check.yml)
[![CI(release)](https://github.com/spraakbanken/simple-archive/actions/workflows/release.yml/badge.svg)](https://github.com/spraakbanken/simple-archive/actions/workflows/release.yml)
[![CI(scheduled)](https://github.com/spraakbanken/simple-archive/actions/workflows/scheduled.yml/badge.svg)](https://github.com/spraakbanken/simple-archive/actions/workflows/scheduled.yml)
[![CI(test)](https://github.com/spraakbanken/simple-archive/actions/workflows/test.yml/badge.svg)](https://github.com/spraakbanken/simple-archive/actions/workflows/test.yml)

CLI and library for managing DSpace's Simple Archive Format (SAF)

## Install

To use as CLI:

```bash
pip install --user simple-archive
```

or with `pipx`:

```bash
pipx install simple-archive
```

or:

1. Clone repo
2. Run `pdm install` in repo root
3. Activate the virtual environment.

Use as a  library: `pdm add simple-archive`.

## Usage

Run `safar <path/to/csv>`

- Use `--zip` if you want to create a zip-archive.
- By default all archives is written to `./output` but you can give `--output dir` to change that.

### CSV Format

The expected CSV format is shown below where the metadata is given in the form `namespace.element[.qualifier]`.

Language can be specified by `namespace.element[language]` or `namespace.element.qualifier[language]`

Example: `dc.description[sv_SE]`

Supported namespaces:

- `dc` (required)
- `local`
- `metashare`
- `dcterms`

```csv
files,dc.title,dc.date.issued,...
filename1||filename2,Title,2023-03-14,...
``

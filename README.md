# simple-archive
CLI and library for managing DSpace's Simple Archive Format (SAF)

## Install

1. Clone repo
2. Run `poetry install` in repo root


## Usage

1. Run `poetry shell` to enter virtual environment
2. Run `safar <path/to/csv>`
    - Use `--zip` if you want to create a zip-archive.
3. By default all archives is written to `./output` but you can give `--output dir` to change that.

### CSV Format

The expected CSV format is shown below where the metadata is given in the form `namespace.element[.qualifier[.language]]`.

**NOTE** Currently only the `dc` namespace is handled.

```csv
files,dc.title,dc.date.issued,...
filename1||filename2,Title,2023-03-14,...
``


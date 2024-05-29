# Data Utility Package: _IO_

[![test](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml)
[![python support version](https://img.shields.io/pypi/pyversions/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![size](https://img.shields.io/github/languages/code-size/korawica/ddeutil-io)](https://github.com/korawica/ddeutil-io)

**Table of Contents**:

- [Installation](#installation)
- [Features](#features)
  - [Files](#files)
  - [Config](#config)
  - [Register](#register)

This **Utility IO** Object was created for `load` the config data from any file
format types like `.yaml`, `.json`, or `.toml`, and manage retention and version
of this config file lifecycle.

## Installation

```shell
pip install ddeutil-io
```

This package need to install `ddeutil` for core package namespace.

## Features

### Files

File Objects that use to read or write data to that format.

For example, I will represent YamlEnvFl object that passing environment variable
to reading content before passing to the Yaml loader.

```yaml
data:
  get: HELLO ${HELLO}
```

```python
import os
from ddeutil.io import YamlEnvFl

os.environ["HELLO"] = "WORLD"

content = YamlEnvFl('./.pre-commit-config.yaml').read(safe=True)
assert content['data']['get'] == "HELLO WORLD"
```

### Config

Config Object is the dir system handler object that manage any files in that
input dir path like `load`, `save`, `load_stage`, `save_stage`, or `files`.

```python
from pathlib import Path
from ddeutil.io.config import ConfFl

config: ConfFl = ConfFl(path=Path('./conf'), compress="gzip")

data = config.load('config_file.yaml')
config.save_stage('./stage/file.json', data)
```

### Register

The **Register Object** is the metadata generator object for the config data.
If you passing name and configs to this object, it will find the config name
in any stage storage and generate its metadata to you.

```python
from ddeutil.io.register import Register
from ddeutil.io.param import Params

registry: Register = Register(
    name='examples:conn_data_local_file',
    params=Params.model_validate({
        "stages": {
            "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
        },
    }),
)
registry.move(stage="raw")
```

The raw data of this config was written in `conn_file.yaml` file.

```text
conf/
  examples/
    conn_file.yaml
```

When call `move` method, it will transfer data from `.yaml` file to `json` file
with the data hashing algorithm.

```text
data/
  raw/
    conn_file_20240101_000000.json
```


## License

This project was licensed under the terms of the [MIT license](LICENSE).

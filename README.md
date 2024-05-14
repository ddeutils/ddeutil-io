# Data Utility Package: _IO_

[![test](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml)
[![python support version](https://img.shields.io/pypi/pyversions/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![size](https://img.shields.io/github/languages/code-size/korawica/ddeutil-io)](https://github.com/korawica/ddeutil-io)

**Table of Contents**:

- [Installation](#installation)
- [Features](#features)
  - [Config](#config)
  - [Register](#register)

This **Utility IO** Object was created for `load` the config data from any file
format types like `.yaml`, `.json`, or `.toml`, and manage retention and version
of this config file lifecycle.

## Installation

```shell
pip install ddeutil-io
```

## Features

### Config

The **Config Object** is the file system handler object.

```python
from pathlib import Path
from ddeutil.io.config import ConfFl

config: ConfFl = ConfFl(path=Path('./file.gz.yaml'), compress="gzip")
```

### Register

The **Register Object** is the metadata generator object for the config data.
If you passing name and configs to this object, it will find the config name
in any stage storage and generate its metadata to you.

```python
from ddeutil.io.register import Register
from ddeutil.io.models import Params

registry: Register = Register(
    name='examples:conn_data_local_file',
    config=Params.model_validate({
        "stages": {
            "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
        },
    }),
)
registry.move(stage="raw")
```

## License

This project was licensed under the terms of the [MIT license](LICENSE).

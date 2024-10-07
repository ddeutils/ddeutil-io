# Input/Output Data Transport

[![test](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml)
[![pypi version](https://img.shields.io/pypi/v/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![python support version](https://img.shields.io/pypi/pyversions/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![size](https://img.shields.io/github/languages/code-size/korawica/ddeutil-io)](https://github.com/korawica/ddeutil-io)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![type check: mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

The **Input/Output Data Transport** utility objects was created for full managed
engine of configuration file that include `load` from any config file format types
like `.yaml`, `.json`, or `.toml`, and manage retention and version of config files
lifecycle.

## :round_pushpin: Installation

```shell
pip install -U ddeutil-io
```

**Python version supported**:

| Python Version | Installation                  | Support Fixed Bug  |
|----------------|-------------------------------|--------------------|
| `>=3.9,<3.14`  | `pip install -U ddeutil-io`   | :heavy_check_mark: |

> [!NOTE]
> This package need to install `ddeutil` for core package namespace.

## :dart: Features

The features of this package is Input/Output data transport utility objects.

| Module   |     Name      | Description | Remark |
|----------|:-------------:|-------------|--------|
| files    |     CsvFl     |             |        |
|          |   CsvPipeFl   |             |        |
|          |     EnvFl     |             |        |
|          |      Fl       |             |        |
|          |   JsonEnvFl   |             |        |
|          |    JsonFl     |             |        |
|          |   MarshalFl   |             |        |
|          |   PickleFl    |             |        |
|          |   TomlEnvFl   |             |        |
|          |    TomlFl     |             |        |
|          |   YamlEnvFl   |             |        |
|          |    YamlFl     |             |        |
|          | YamlFlResolve |             |        |
|          |  PathSearch   |             |        |
|          |   RegexConf   |             |        |
| config   |               |             |        |
| register |   Register    |             |        |

## :beers: Usages

I will show some usage example of function in this package. If you want to use
complex or adjust some parameter, please see doc-string or real source code
(I think it do not complex and you can see how that function work).

### Files

For example, I will represent `YamlEnvFl` object that passing environment variable
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

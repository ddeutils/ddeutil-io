# Data Utility Package: _IO_

[![test](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/korawica/ddeutil-io/actions/workflows/tests.yml)
[![pypi version](https://img.shields.io/pypi/v/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![python support version](https://img.shields.io/pypi/pyversions/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![size](https://img.shields.io/github/languages/code-size/korawica/ddeutil-io)](https://github.com/korawica/ddeutil-io)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The **Input/Output transport utility objects** with less dependencies created for
`load` the config data from any file format types like `.yaml`, `.json`,
or `.toml`, and manage retention and version of this config file lifecycle, or
data serialization object with Pydantic model.

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

The features of this package is Input/Output utility objects.

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

### Models

The Model objects was implemented from the [Pydantic V2](https://docs.pydantic.dev/latest/)
which is the powerful parsing and serializing data model to the Python object.

> [!NOTE]
> So, I use this project to learn and implement a limit and trick of the Pydantic
> package.

The model able to handle common logic validations and able to adjust by custom code
for your specific requirements (Yeah, it just inherits Sub-Class from `BaseModel`).

#### Data Types

```python
from ddeutil.io.models.dtype import StringType

dtype = StringType()
assert dtype.type == "string"
assert dtype.max_length == -1
```

#### Constraints

```python
from ddeutil.io.models.const import Pk

const = Pk(of="foo", cols=["bar", "baz"])
assert const.name == "foo_bar_baz_pk"
assert const.cols == ["bar", "baz"]
```

#### Datasets

```python
from ddeutil.io.models.datasets import Col, Tbl

tbl = Tbl(
  name="table_foo",
  features=[
    Col(name="id", dtype="integer primary key"),
    Col(name="foo", dtype="varchar( 10 )"),
  ],
)
assert tbl.name == "table_foo"
assert tbl.features[0].name == "id"
assert tbl.features[0].dtype.type == "integer"
```

## :beers: Usage

### Models

If I have some catalog config, it easy to pass this config to model object.

```python
import yaml
from ddeutil.io.models.datasets import Scm


config = yaml.safe_load("""
name: "warehouse"
tables:
  - name: "customer_master"
    features:
      - name: "id"
        dtype: "integer"
        pk: true
      - name: "name"
        dtype: "varchar( 256 )"
        nullable: false
""")
schema = Scm.model_validate(config)
assert len(schema.tables) == 1
assert schema.tables[0].name == 'customer_master'
```

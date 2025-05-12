# Input/Output Data Transport

[![test](https://github.com/ddeutils/ddeutil-io/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/ddeutils/ddeutil-io/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/ddeutils/ddeutil-io/graph/badge.svg?token=3NDPN2I0H9)](https://codecov.io/gh/ddeutils/ddeutil-io)
[![pypi version](https://img.shields.io/pypi/v/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![python support version](https://img.shields.io/pypi/pyversions/ddeutil-io)](https://pypi.org/project/ddeutil-io/)
[![size](https://img.shields.io/github/languages/code-size/ddeutils/ddeutil-io)](https://github.com/ddeutils/ddeutil-io)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![type check: mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

An **Input/Output Transport Objects** 🚅 was created for full managed configuration
file that include `read` and `write` from any file format like `.yaml`, `.json`,
or `.toml`. This package also provide retention and version management of config
files for configuration data lifecycle ♻️.

> [!NOTE]
> The core part of this project is **Files** module.

## 📦 Installation

```shell
pip install -U ddeutil-io
```

**Python version supported**:

| Python Version | Installation                | Support Fixed Bug  |
|:---------------|:----------------------------|:------------------:|
| `>=3.9,<3.14`  | `pip install -U ddeutil-io` | :heavy_check_mark: |

> [!NOTE]
> This package need to install `ddeutil` first to be core package namespace.
> You do not need to pip it because I include this package to the required list.
>
> For optional dependencies that should to additional installation;
>
> | Module      | Installation           | Additional dependencies                        |
> |-------------|------------------------|------------------------------------------------|
> | `YamlFl`    | `ddeutil-io[yaml]`     | `pip install PyYaml`                           |
> | `TomlFl`    | `ddeutil-io[toml]`     | `pip install rtoml`                            |
> | `MsgpackFl` | `ddeutil-io[msgpack]`  | `pip install msgpack`                          |
> | `Register`  | `ddeutil-io[register]` | `pip install python-dateutil deepdiff fmtutil` |

## 🎯 Features

The features of this package is Input/Output data transport utility objects.

| Module   |      Name       | Description                                                                                                                               | Remark   |
|:---------|:---------------:|:------------------------------------------------------------------------------------------------------------------------------------------|----------|
| paths    |   PathSearch    | Path Search object that use to search path tree from an input root path.                                                                  |          |
|          |       ls        | List files in a directory, applying ignore-style filtering.                                                                               |          |
| files    |       Fl        | Open File object that use to open any normal or compression file from current local file system                                           |          |
|          |   EnvFlMixin    | Environment Mapping to read method of open file object mixin.                                                                             |          |
|          |      EnvFl      | Dot env open file object which mapping search engine to data context that reading from dot env file format (.env).                        |          |
|          |    YamlEnvFl    | Yaml open file object which mapping search environment variable.                                                                          |          |
|          |     YamlFl      | Yaml open file object that read data context from Yaml file format (.yml, or .yaml).                                                      |          |
|          |  YamlFlResolve  | Yaml open file object with resolve boolean convert value problem such as convert 'on' value to true instead a string of 'on' value.       |          |
|          |    JsonEnvFl    | Json open file object which mapping search environment variable before parsing with json package.                                         |          |
|          |   JsonLineFl    | Json open file object that read data context from Json file format (.json) with a newline seperator.                                      |          |
|          |     JsonFl      | Json open file object that read data context from Json file format (.json).                                                               |          |
|          |      CsvFl      | CSV open file object with comma (`,`) seperator charactor.                                                                                |          |
|          |    CsvPipeFl    | CSV open file object with pipe (`\|`) seperator charactor.                                                                                |          |
|          |    TomlEnvFl    | TOML open file object which mapping search environment variable before parsing with toml package from TOML file format (.toml).           |          |
|          |     TomlFl      | TOML open file object that read data context from TOML file format (.toml).                                                               |          |
|          |    PickleFl     | Pickle open file object that read data context from Pickle file format (.pickle).                                                         | no cover |
|          |    MarshalFl    | Marshal open file object that read data context from Marshal file format.                                                                 | no cover |
|          |    MsgpackFl    | Msgpack open file object that read data context from Msgpack file format.                                                                 | no cover |
| stores   |      Store      | Store File Loading Object for get data from configuration and stage.                                                                      |          |
|          | StoreJsonToCsv  | Store object that getting the Json context data and save it to stage with CSV file format.                                                |          |
|          | StoreToJsonLine | Store object that getting the YAML context data and save it to stage with Json line file format.                                          |          |
| register |    Register     | Register Object that contain configuration loading methods and metadata management.                                                       |          |
|          | ArchiveRegister | Archiving Register object that implement archiving management on the Register object such as ``self.purge``, and ``self.remove`` methods. |          |
| utils    |       rm        | Remove a file or dir from an input path.                                                                                                  |          |
|          |      touch      | Create an empty file with specific name and modified time of path it an input times was set.                                              |          |

## 💡 Usages

I will show some usage example of function in this package. If you want to use
complex or adjust some parameter, please see doc-string or real source code
(I think it does not complex, and you can see how that function work).

### ⭕ Files

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
content = YamlEnvFl('./source.yaml').read(safe=True)
assert content['data']['get'] == "HELLO WORLD"
```

> [!NOTE]
> This module do not implement special function on IO like the build-in ``open``
> function. It also makes standard ``read`` and ``write`` file objects.

### ❌ Dirs

> [!WARNING]
> This module should not use on the production.

### ⭕ Store

Store object is the storing dir system handler object that manage any files in
that dir path with `get`, `move`, `load`, `save`, or `ls` operations.

```python
from ddeutil.io import Store

store: Store = Store(path='./conf', compress="gzip")

data = store.get(name='config_file.yaml')
store.save('./stage/file.json', data)
```

```text
conf/
 ├─ examples/
 │   ╰─ config_file.yaml
 ╰─ stage/
     ╰─ file.json
```

### ⭕ Register

The **Register Object** is the metadata generator object for the config data.
If you passing name and configs to this object, it will find the config name
in any stage storage and generate its metadata to you.

```python
from ddeutil.io.register import Register
from ddeutil.io import Params

registry: Register = Register(
    name='examples:conn_data_local_file',
    params=Params(**{
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
 ╰─ examples/
     ╰─ conn_file.yaml
```

When call `move` method, it will transfer data from `.yaml` file to `json` file
with the data hashing algorithm.

```text
data/
 ├─ __METADATA/
 │   ├─ exampleconn_data_local_file.base.json
 │   ╰─ exampleconn_data_local_file.raw.json
 ╰─ raw/
     ╰─ conn_file_20240101_000000.json
```

## 💬 Contribute

I do not think this project will go around the world because it has specific propose,
and you can create by your coding without this project dependency for long term
solution. So, on this time, you can open [the GitHub issue on this project 🙌](https://github.com/ddeutils/ddeutil-io/issues)
for fix bug or request new feature if you want it.

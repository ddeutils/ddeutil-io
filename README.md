# Data Utility Package: _IO_

**Table of Contents**:

- [Base](#)
  - Files
  - Path
- [Config](#config)
- [Register](#register)

This **Utility IO** Object was created for `load` the config data from any file
format types like `.yaml`, `.json`, or `.toml`, and manage retention and version
of this config file lifecycle.

**Install from PyPI**:

```shell
pip install ddeutil-io
```

## Config

The **Config Object** is the file system handler object.

```python

```

## Register

The **Register Object** is the metadata generator object for the config data.
If you passing name and configs to this object, it will find the config name
in any stage storage and generate its metadata to you.

```python
from ddeutil.io.register import Register

registry = Register(
    name='examples:conn_data_local_file',
    config={
        'format': '{name}_{timestamp}*',
    }
)
```

```python
from ddeutil.io.register import Register

registry = Register(
    name='examples:conn_data_local_file',
    config={
        'stages': {
            'raw': {
                'format': '{name}_{timestamp}*',
                'rules': {
                    'timestamp': 15
                }
            },
            'persisted': {
                'format': '{name}_{timestamp}*',
            }
        },
    }
)
```

## License

This project was licensed under the terms of the [MIT license](LICENSE).

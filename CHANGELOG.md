# Changelogs

## Latest Changes

## 0.2.13

### :bug: Bug fixes

- :gear: fixed: add threading lock for YAML resolve that error when run multithread (#50)

## 0.2.12

### :postbox: Dependencies

- :pushpin: deps: change toml package to rtoml for perf and python version support.

## 0.2.11

### :postbox: Dependencies

- :pushpin: deps: update ddeutil from 0.4.6 to 0.4.7.

## 0.2.10

### :bug: Bug fixes

- :gear: fixed: add no cov comment on import try-except.

### :postbox: Dependencies

- :pushpin: deps: remove import register module on init.

## 0.2.9

### :postbox: Dependencies

- :pushpin: deps: separate deepdiff and fmtutil packages from core deps. (#48)

## 0.2.8

### :stars: Highlight Features

- :star: hl: add ls func on paths module.

### :sparkles: Features

- :dart: feat: revise ignore filter algorithm.

### :black_nib: Code Changes

- :lipstick: styled: change prefix message for auto pr.

## 0.2.7

### :black_nib: Code Changes

- :test_tube: tests: update and fix testcase.
- :package: refactored: bump tzdata from 2025.1 to 2025.2 (#46)
- :package: refactored: bump deepdiff from 8.2.0 to 8.4.2 (#45)
- :package: refactored: bump deepdiff from 8.1.1 to 8.2.0 (#44)
- :package: refactored: bump fmtutil from 1.0.14 to 1.0.15 (#43)

### :broom: Deprecate & Clean

- :recycle: clean: clean and rename modules.

### :postbox: Dependencies

- :pushpin: deps: update clishelf version on pre-commit config file.

## 0.2.6

### :black_nib: Code Changes

- :package: refactored: bump fmtutil from 1.0.12 to 1.0.14 (#41)
- :package: refactored: bump tzdata from 2024.2 to 2025.1 (#42)
- :construction: refactored: ⬆ bump pypa/gh-action-pypi-publish from 1.12.3 to 1.12.4 (#40)

### :package: Build & Workflow

- :toolbox: build: add clishelf config for fix message does not parse.
- :toolbox: build: add test deps for tests workflow.

### :postbox: Dependencies

- :pushpin: deps: add lazy import for python dateutil package.

## 0.2.5

### :black_nib: Code Changes

- :art: styled: fixed typed hint on stores module. (_2025-01-21_)
- :art: styled: fixed typed hint on dir module. (_2025-01-21_)
- :art: styled: add comment for type checker that not valid in pycharm. (_2025-01-21_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file. (_2025-01-21_)

## 0.2.4

### :sparkles: Features

- :dart: feat: move conf on files to __conf. (_2025-01-19_)
- :dart: feat: move icon to __type mod. (_2025-01-18_)

### :black_nib: Code Changes

- :art: styled: change code style support typed hint. (_2025-01-19_)
- :test_tube: tests: update testcase for path search object. (_2025-01-07_)
- :construction: refactored: 📦 bump fmtutil from 1.0.11 to 1.0.12 (#39) (_2025-01-02_)
- :construction: refactored: ⬆ bump pypa/gh-action-pypi-publish from 1.12.2 to 1.12.3 (_2025-01-01_)
- :construction: refactored: 📦 bump ddeutil[all] from 0.4.3 to 0.4.4 (_2025-01-01_)
- :construction: refactored: 📦 bump deepdiff from 8.0.1 to 8.1.1 (_2025-01-01_)
- :construction: refactored: ⬆ bump pypa/gh-action-pypi-publish from 1.11.0 to 1.12.2 (_2024-12-01_)
- :construction: refactored: ⬆ bump codecov/codecov-action from 4 to 5 (_2024-12-01_)
- :construction: refactored: ⬆ bump deadsnakes/action from 3.1.0 to 3.2.0 (_2024-11-01_)
- :construction: refactored: ⬆ bump pypa/gh-action-pypi-publish from 1.10.2 to 1.11.0 (_2024-11-01_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file. (_2025-01-19_)
- :page_facing_up: docs: update readme file. (_2025-01-18_)
- :page_facing_up: docs: update header file. (_2025-01-18_)
- :page_facing_up: docs: update readme file on installation topic. (_2025-01-18_)
- :page_facing_up: docs: update readme file. (_2024-10-22_)

### :postbox: Dependencies

- :pushpin: deps: update pre-commit-hooks version to 5.0.0. (_2025-01-18_)
- :pushpin: deps: update core deps version. (_2025-01-18_)

## 0.2.3

### :sparkles: Features

- :dart: feat: add store that support json line on staging. (_2024-10-21_)
- :dart: feat: move metadata file from python object on mem to file base. (_2024-10-21_)
- :dart: feat: add archiving variable on archive register object. (_2024-10-21_)
- :dart: feat: add reverse_readline function on files utils. (_2024-10-20_)
- :dart: feat: move argument of open file on store module to class argument. (_2024-10-20_)

### :black_nib: Code Changes

- :test_tube: tests: add testcase for cover files module. (_2024-10-22_)
- :test_tube: tests: add testcase for cover register module. (_2024-10-22_)
- :test_tube: tests: update testcase for store module. (_2024-10-21_)
- :art: styled: move typing define to __type file. (_2024-10-21_)
- :test_tube: tests: add clear data path after testing. (_2024-10-21_)
- :art: styled: change param type annotation. (_2024-10-20_)

### :postbox: Dependencies

- :pushpin: deps: update version fmtutil==1.0.11. (_2024-10-21_)

## 0.2.2

### :sparkles: Features

- :dart: feat: remove loading argument from register object. (_2024-10-19_)

### :black_nib: Code Changes

- :art: styled: change code format on register module. (_2024-10-19_)
- :test_tube: tests: update testcase for register module. (_2024-10-19_)

### :bug: Fix Bugs

- :gear: fixed: remove store sqlite object. (_2024-10-19_)
- :gear: fixed: split metadata management from init to method. (_2024-10-19_)

## 0.2.1

### :sparkles: Features

- :dart: feat: change params from pydantic model to dataclass. (_2024-10-19_)
- :dart: feat: change config object to store object. (_2024-10-17_)

### :black_nib: Code Changes

- :test_tube: tests: update testcase for config module. (_2024-10-19_)
- :art: styled: change argument and variable name of store in register module. (_2024-10-19_)
- :test_tube: tests: update testcase for stores module. (_2024-10-18_)
- :construction: refactored: change method name in the stores module. (_2024-10-17_)
- :art: styled: change varible name on register module. (_2024-10-16_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file. (_2024-10-19_)

### :postbox: Dependencies

- :pushpin: deps: update version ddeutil[all]==0.4.3. (_2024-10-17_)

## 0.2.0

### :sparkles: Features

- :dart: feat: add dynamic reading data on csv file format. (_2024-10-09_)
- :dart: feat: remove engine and value from param model. (_2024-10-07_)
- :dart: feat: add comment pragma for exclude coverage. (_2024-10-07_)

### :black_nib: Code Changes

- :test_tube: tests: add testcase for json open file object. (_2024-10-09_)
- :art: styled: change variable name that use on testcase. (_2024-10-08_)
- :art: styled: change variable name on files module. (_2024-10-08_)
- :test_tube: tests: reformat testcase name for support features change. (_2024-10-08_)
- :art: styled: change code styled. (_2024-10-07_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme for optional deps. (_2024-10-09_)
- :page_facing_up: docs: update readme file. (_2024-10-07_)

### :bug: Fix Bugs

- :gear: fixed: change import for support ddeutil 0.4.2. (_2024-10-07_)

### :package: Build & Workflow

- :toolbox: build: change ruff run only pre-commit stage. (_2024-10-09_)
- :toolbox: build: add coverage workflow. (_2024-10-07_)
- :toolbox: build: change pre-commit config syntax support pre-commit version 4. (_2024-10-07_)
- :toolbox: build: add support nogil for python version 3.13. (_2024-10-07_)

### :postbox: Dependencies

- :pushpin: deps: adjust optional dependency. (_2024-10-08_)

## 0.1.14

### :black_nib: Code Changes

- :construction: refactored: move models to vendor package. (_2024-10-07_)
- :art: styled: change __conf and __regex to conf module. (_2024-10-07_)
- :construction: refactored: 📦 bump msgpack from 1.0.8 to 1.1.0 (_2024-10-01_)
- :construction: refactored: ⬆ bump pypa/gh-action-pypi-publish from 1.10.0 to 1.10.2 (_2024-10-01_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file. (_2024-10-07_)
- :page_facing_up: docs: update docs-string on files module. (_2024-09-26_)
- :page_facing_up: docs: update doc-string on files. (_2024-09-26_)

## 0.1.13

### :sparkles: Features

- :dart: feat: add config and base import on root package. (_2024-09-26_)

### :card_file_box: Documents

- :page_facing_up: docs: update header of readme. (_2024-09-26_)

### :bug: Fix Bugs

- :gear: fixed: change keyword of this package. (_2024-09-26_)

### :postbox: Dependencies

- :pushpin: deps: fixed install ddeutil with all optional. (_2024-09-26_)
- :pushpin: deps: update pydantic to 2.9.2. (_2024-09-26_)
- :pushpin: deps: update dependency; ddeutil==0.4.0 fmtutil==1.0.10. (_2024-09-26_)

## 0.1.12

### :postbox: Dependencies

- :pushpin: deps: update testing workflow support python version 3.13. (_2024-09-13_)
- :pushpin: deps: remove msgspec from this project. (_2024-09-13_)
- :pushpin: deps: add lower bound dependencies. (_2024-09-13_)

## 0.1.11

### :black_nib: Code Changes

- :test_tube: tests: fix a testcase that use list to check equal. (_2024-08-06_)
- :construction: refactored: 📦 bump pydantic from 2.8.0 to 2.8.2 (_2024-07-25_)
- :construction: refactored: ⬆ bump pypa/gh-action-pypi-publish from 1.8.14 to 1.9.0 (_2024-07-01_)
- :construction: refactored: 📦 bump pydantic from 2.7.2 to 2.8.0 (_2024-07-01_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file. (_2024-08-06_)

### :postbox: Dependencies

- :pushpin: deps: update pyyaml version to 6.0.2. (_2024-08-23_)

## 0.1.10

### :card_file_box: Documents

- :page_facing_up: docs: update doc-str on param. (_2024-06-04_)

### :bug: Fix Bugs

- :gear: fixed: edit print statement to logging. (_2024-06-03_)

## 0.1.9

### :sparkles: Features

- :dart: feat: merge ddeutil-model to this proj. (_2024-06-03_)
- :dart: feat: override tar and zip class for make the same protocol. (_2024-05-29_)

### :black_nib: Code Changes

- :construction: refactored: 📦 bump pydantic from 2.7.1 to 2.7.2 (_2024-06-01_)
- :test_tube: tests: add testcase for make coverage. (_2024-05-31_)
- :test_tube: tests: add testcases for base path search. (_2024-05-31_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file for more examples. (_2024-05-29_)

### :bug: Fix Bugs

- :gear: fixed: tarfil extract deprecate on python version 3.12. (_2024-05-31_)
- :gear: fixed: change charactor that does not display. (_2024-05-31_)
- :gear: fixed: change list equal to set for file search path. (_2024-05-31_)
- :gear: fixed: change extract method on test cases. (_2024-05-29_)

### :package: Build & Workflow

- :toolbox: build: update ignore dir for examples on models. (_2024-06-03_)

## 0.1.8

### :sparkles: Features

- :dart: feat: add toml file for base file loader. (_2024-05-28_)

### :black_nib: Code Changes

- :construction: refactored: update dir on file utils func. (_2024-05-28_)
- :test_tube: tests: remve unittest to assert test. (_2024-05-28_)

### :card_file_box: Documents

- :page_facing_up: docs: update docs-string for mapping utils func. (_2024-05-27_)

### :bug: Fix Bugs

- :gear: fixed: add pre-load yaml file instead comment search replace. (_2024-05-22_)

## 0.1.7

### :sparkles: Features

- :dart: feat: seperate Register with archiving step to FullRegister. (_2024-05-18_)

### :black_nib: Code Changes

- :construction: refactored: change constructure of regex conf class. (_2024-05-17_)

### :card_file_box: Documents

- :page_facing_up: docs: update doc-string and type hint. (_2024-05-18_)

### :bug: Fix Bugs

- :gear: fixed: regex config for yaml env that catch caller. (_2024-05-22_)

## 0.1.6

### :black_nib: Code Changes

- :construction: refactored: rename param models and add __conf file for keep tracking keys. (_2024-05-17_)
- :construction: refactored: change module name from models to param. (_2024-05-17_)
- :construction: refactored: change args name on move method and add doc-string on utils. (_2024-05-17_)

### :card_file_box: Documents

- :page_facing_up: docs: update feature on readme file. (_2024-05-17_)
- :page_facing_up: docs: update doc-string on __base.utils module. (_2024-05-17_)

### :postbox: Dependencies

- :pushpin: deps: add modules importer on __init__ file. (_2024-05-16_)

## 0.1.5

### :sparkles: Features

- :dart: feat: add unsafe load on yaml file loader. (_2024-05-16_)
- :dart: feat: add dynamic staging loader. (_2024-05-16_)
- :dart: feat: add dynamic staging loader. (_2024-05-16_)

### :black_nib: Code Changes

- :construction: refactored: add type hint on sqlite conf. (_2024-05-16_)
- :test_tube: tests: remove example files on tests. (_2024-05-16_)

### :package: Build & Workflow

- :toolbox: build: remove default run on test workflow. (_2024-05-15_)

## 0.1.4

### :postbox: Dependencies

- :pushpin: deps: remove un-use deps from pyproject. (_2024-05-15_)

## 0.1.3

### :black_nib: Code Changes

- :construction: refactored: remove code for node and migrate to ddeutil-pipe. (_2024-05-14_)

## 0.1.2

### :sparkles: Features

- :dart: feat: remove config param fron register args. (_2024-05-14_)

### :black_nib: Code Changes

- :test_tube: tests: migrate unittest to pytest with assert. (_2024-05-14_)
- :art: style: rename file system name to Fl and dir opener to Dir. (_2024-05-14_)
- :construction: refactored: change file system object name. (_2024-05-14_)
- :test_tube: tests: reformat model test case. (_2024-05-13_)

### :card_file_box: Documents

- :page_facing_up: docs: update readme file that rename config file obj. (_2024-05-14_)

### :bug: Fix Bugs

- :gear: fixed: remove self from test case that use on uniitest. (_2024-05-13_)

## 0.1.1

### :black_nib: Code Changes

- :test_tube: tests: refactored testcase file from io dir. (_2024-05-13_)
- :test_tube: tests: tried to use fixture module scope for testing config reading. (_2024-05-13_)
- :test_tube: tests: rename and move test files of base to the same level of common module. (_2024-05-13_)
- :construction: refactored: refactored code on files objects. (_2024-05-13_)
- :construction: refactored: change code format for valid param name. (_2024-05-13_)
- :construction: refactored: rewrite __base.files. (_2024-05-13_)
- :test_tube: test: upgrade import package from updated ddeutil. (_2024-05-13_)
- :construction: refactored: move setting file to __regex on base module. (_2024-05-13_)
- :construction: refactored: 📦 bump pydantic from 2.3.0 to 2.7.1 (#17) (_2024-05-05_)
- :construction: refactored: 📦 bump openpyxl from 3.0.10 to 3.1.2 (_2024-05-05_)
- :construction: refactored: 📦 bump boto3 from 1.28.35 to 1.34.98 (_2024-05-05_)
- :construction: refactored: 📦 bump polars from 0.18.15 to 0.20.23 (_2024-05-05_)
- :construction: refactored: 📦 bump pandas from 2.0.3 to 2.2.2 (_2024-05-05_)
- :construction: refactored: 📦 bump python-dotenv from 1.0.0 to 1.0.1 (_2024-05-05_)
- :construction: refactored: 📦 bump psycopg2 from 2.9.3 to 2.9.9 (_2024-05-05_)

### :postbox: Dependencies

- :pushpin: deps: upgrade pre-commit hook deps. (_2024-05-05_)

## 0.1.0

### :sparkles: Features

- :dart: feat: migrate ddeutil-node to this package. (_2023-10-02_)

### :black_nib: Code Changes

- :bookmark: Bump up to version 0.0.3 -> 0.0.4. (_2024-05-05_)
- :test_tube: test: reformat testcase results. (_2024-05-05_)
- :test_tube: test: add optional import dotenv package for dev env. (_2023-10-12_)

### :bug: Fix Bugs

- :gear: fixed: update python version from 38 to 39. (_2024-05-05_)
- :gear: fixed: change version deps that updated from fmtutil. (_2023-10-12_)

### :package: Build & Workflow

- :toolbox: build: split step on publish workflow for each env. (_2024-05-05_)

## 0.0.3

### Features

- :dart: feat: add loader arg to Register object for dynamic config loader. (_2023-09-26_)
- :dart: feat: add OpenDir object that read compress dir like zip or tar. (_2023-09-26_)

### Code Changes

- :construction: refactored: change openfile cls attr to init attr for dynamic open file. (_2023-09-26_)
- :construction: refactored: add classmethod after field_validate decorator. (_2023-09-16_)

### Documents

- :page_facing_up: docs: update README file that move all module to features topic. (_2023-09-26_)

## 0.0.2

### Features

- :dart: feat: add engine path config in Params model object for dynamic paths. (_2023-09-15_)
- :dart: feat: add mapping utils modules for map config data from file. (_2023-09-15_)

### Code Changes

- :construction: refactored: add the io modules to __init__ file. (_2023-09-15_)

### Documents

- :page_facing_up: docs: update python supported version on README. (_2023-09-15_)

## 0.0.1

### Features

- :dart: feat: initial first version of IO module to this proj (_2023-09-13_)

### Code Changes

- :test_tube: test: test case register object initialize without Params config. (_2023-09-14_)
- :construction: refactored: change timestamp value on RuleData from pair of metric to dict. (_2023-09-14_)
- :construction: refactored: add reset class method to Register object. (_2023-09-14_)
- :construction: refactor: Initial commit (_2023-09-13_)

### Documents

- :page_facing_up: docs: update README file for config and register modules. (_2023-09-14_)

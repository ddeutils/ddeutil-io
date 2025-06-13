import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from ddeutil.io.paths import PathSearch, is_ignored, ls, replace_sep
from ddeutil.io.utils import touch


@pytest.fixture(scope="module")
def make_empty_path(test_path: Path) -> Generator[Path, None, None]:
    path_search = test_path / "test_empty_path_search"
    path_search.mkdir(exist_ok=True)

    yield path_search

    shutil.rmtree(path_search)


@pytest.fixture(scope="module")
def make_path(test_path: Path) -> Generator[Path, None, None]:
    path_search: Path = test_path / "test_path_search"
    path_search.mkdir(exist_ok=True)

    touch(path_search / "00_01_test.text")
    (path_search / "dir01").mkdir(exist_ok=True)
    touch(path_search / "dir01" / "01_01_test.text")
    touch(path_search / "dir01" / "01_02_test.text")
    (path_search / "dir02").mkdir(exist_ok=True)
    touch(path_search / "dir02" / "02_01_test.text")

    yield path_search

    shutil.rmtree(path_search)


def test_base_path_search_empty(make_empty_path):
    ps = PathSearch(make_empty_path)
    assert [] == ps.files
    assert 1 == ps.level


def test_base_path_search_raise(make_empty_path):
    with pytest.raises(FileNotFoundError):
        PathSearch(make_empty_path / "demo")


def test_base_path_search(make_path):
    ps = PathSearch(make_path)
    assert {
        make_path / "00_01_test.text",
        make_path / "dir01/01_01_test.text",
        make_path / "dir01/01_02_test.text",
        make_path / "dir02/02_01_test.text",
    } == set(ps.files)

    ps = PathSearch(make_path, exclude=["dir02"])
    assert {
        make_path / "00_01_test.text",
        make_path / "dir01/01_01_test.text",
        make_path / "dir01/01_02_test.text",
    } == set(ps.files)


@pytest.fixture(scope="module")
def make_ls(test_path: Path) -> Generator[Path, None, None]:
    path_search: Path = test_path / "test_path_ls"
    path_search.mkdir(exist_ok=True)

    touch(path_search / "00_01_test.yml")
    (path_search / "dir01").mkdir(exist_ok=True)
    touch(path_search / "dir01" / "01_01_test.yml")
    touch(path_search / "dir01" / "01_02_test.yml")

    (path_search / "dir02").mkdir(exist_ok=True)
    touch(path_search / "dir02" / "02_01_test.yml")
    touch(path_search / "dir02" / "02_01_test.json")
    touch(path_search / "dir02" / "02_02_test_ignore.yml")
    touch(path_search / "dir02" / "02_03_test.yml")

    (path_search / "dir02/tests").mkdir(exist_ok=True)
    touch(path_search / "dir02/tests" / "02_01_01_demo.yml")

    (path_search / "tests").mkdir(exist_ok=True)
    touch(path_search / "tests" / "03_01_test.yml")
    touch(path_search / "tests" / "03_02_test.yml")

    (path_search / "ignore_dir").mkdir(exist_ok=True)
    touch(path_search / "ignore_dir" / "ignore_01.yml")
    touch(path_search / "ignore_dir" / "ignore_02.yml")

    with open(path_search / ".ignore_file", mode="w") as f:
        f.write("tests\n")
        f.write("*.json\n")
        f.write("*_ignore.yml\n")
        f.write("02_03_*\n")
        f.write("ignore_dir/\n")

    yield path_search

    shutil.rmtree(path_search)


def test_ls(make_ls: Path):
    files = ls(make_ls, ignore_file=".ignore_file")
    print([replace_sep(str(f.relative_to(make_ls))) for f in files])
    assert {replace_sep(str(f.relative_to(make_ls))) for f in files} == {
        "00_01_test.yml",
        "dir01/01_01_test.yml",
        "dir01/01_02_test.yml",
        "dir02/02_01_test.yml",
    }


def test_ls_empty(test_path):
    path_search: Path = test_path / "test_path_ls_empty"
    path_search.mkdir(exist_ok=True)

    files = ls(path_search, ignore_file=".ignore")
    assert list(files) == []

    shutil.rmtree(path_search)


def test_is_ignored():
    assert is_ignored(Path(".foo/ignore_dir"), ["ignore_dir/"])
    assert is_ignored(Path(".foo/ignore_dir/test.yml"), ["ignore_dir/"])
    assert is_ignored(Path(".foo/ignore_dir"), ["ignore_dir"])
    assert is_ignored(Path(".foo/ignore_dir/test.yml"), ["ignore_dir"])
    assert is_ignored(Path(".foo/test/ignore_dir/test.yml"), ["ignore_dir"])
    assert is_ignored(Path(".foo/test/ignore_dir/test.yml"), ["ignore_dir/"])

    # Test case 1: Basic directory and file patterns
    patterns1 = ["ignore_dir/", "*_test.json"]
    assert is_ignored(Path("foo/demo_test.json"), patterns1)
    assert is_ignored(Path("foo/ignore_dir"), patterns1)
    assert is_ignored(Path("foo/ignore_dir/file.json"), patterns1)
    assert not is_ignored(Path("foo/regular_file.json"), patterns1)

    # Test case 2: Wildcard patterns
    patterns2 = ["*.log", "temp*/", "build/"]
    assert is_ignored(Path("error.log"), patterns2)
    assert is_ignored(Path("debug.log"), patterns2)
    assert is_ignored(Path("temp_backup/"), patterns2)
    assert is_ignored(Path("temp_backup/file.txt"), patterns2)
    assert is_ignored(Path("build/output.exe"), patterns2)
    assert not is_ignored(Path("src/main.py"), patterns2)

    # Test case 3: Nested patterns
    patterns3 = ["node_modules/", "**/*.pyc", ".git/"]
    assert is_ignored(Path("node_modules/package/index.js"), patterns3)
    assert is_ignored(Path("src/__pycache__/module.pyc"), patterns3)
    assert is_ignored(Path(".git/config"), patterns3)
    assert not is_ignored(Path("src/main.py"), patterns3)

    # Test case 4: Complex patterns
    patterns4 = ["*.tmp", "cache*/", "*_backup.*", "test_*"]
    assert is_ignored(Path("data.tmp"), patterns4)
    assert is_ignored(Path("cache_old/data.json"), patterns4)
    assert is_ignored(Path("config_backup.json"), patterns4)
    assert is_ignored(Path("test_module.py"), patterns4)
    assert not is_ignored(Path("main.py"), patterns4)

    # Test case 5: Edge cases
    patterns5 = [".DS_Store", "Thumbs.db", "*.swp", "__pycache__/"]
    assert is_ignored(Path(".DS_Store"), patterns5)
    assert is_ignored(Path("folder/.DS_Store"), patterns5)
    assert is_ignored(Path("Thumbs.db"), patterns5)
    assert is_ignored(Path("file.swp"), patterns5)
    assert is_ignored(Path("__pycache__/module.pyc"), patterns5)
    assert not is_ignored(Path("regular_file.txt"), patterns5)

    # Test case 6: Path-specific patterns
    patterns6 = ["src/test/", "docs/*.md", "config/*.ini"]
    assert is_ignored(Path("src/test/unit_test.py"), patterns6)
    assert is_ignored(Path("docs/readme.md"), patterns6)
    assert is_ignored(Path("config/settings.ini"), patterns6)
    assert not is_ignored(Path("src/main.py"), patterns6)
    assert not is_ignored(Path("readme.md"), patterns6)

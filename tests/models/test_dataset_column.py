import ddeutil.io.models.datasets.col as col
import ddeutil.io.models.dtype as dtype


def test_base_column_init():
    t = col.BaseCol(name="foo", dtype={"type": "base"})
    assert "foo" == t.name
    assert "base" == t.dtype.type

    t = col.BaseCol(name="foo", dtype="varchar( 100 )")
    assert "foo" == t.name
    assert "varchar" == t.dtype.type
    assert 100 == t.dtype.max_length

    t = col.BaseCol(name="foo", dtype={"type": "varchar", "max_length": 100})
    assert "foo" == t.name
    assert "varchar" == t.dtype.type
    assert 100 == t.dtype.max_length


def test_base_column_model_validate():
    t = col.BaseCol.model_validate(
        {
            "name": "foo",
            "dtype": {
                "type": "varchar",
                "max_length": 1000,
            },
        }
    )
    assert "foo" == t.name
    assert "varchar" == t.dtype.type
    assert 1000 == t.dtype.max_length

    t = col.BaseCol.model_validate(
        {
            "name": "foo",
            "dtype": {"type": "int"},
        }
    )
    assert "foo" == t.name
    assert "integer" == t.dtype.type


def test_column_init():
    t = col.Col(name="foo", dtype=dtype.BaseType())
    assert {
        "name": "foo",
        "dtype": {"type": "base"},
        "desc": None,
        "nullable": True,
        "unique": False,
        "default": None,
        "check": None,
        "pk": False,
        "fk": {},
    } == t.model_dump(by_alias=False)

    t = col.Col(name="foo", dtype={"type": "base"})
    assert {
        "name": "foo",
        "dtype": {"type": "base"},
        "desc": None,
        "nullable": True,
        "unique": False,
        "default": None,
        "check": None,
        "pk": False,
        "fk": {},
    } == t.model_dump(by_alias=False)

    t = col.Col(name="foo", dtype="base")
    assert {
        "name": "foo",
        "dtype": {"type": "base"},
        "desc": None,
        "nullable": True,
        "unique": False,
        "default": None,
        "check": None,
        "pk": False,
        "fk": {},
    } == t.model_dump(by_alias=False)

    t = col.Col(
        name="foo",
        dtype="varchar( 20 )",
        fk={"table": "bar", "column": "baz"},
    )
    assert {
        "name": "foo",
        "dtype": {"max_length": 20, "type": "varchar"},
        "desc": None,
        "nullable": True,
        "unique": False,
        "default": None,
        "check": None,
        "pk": False,
        "fk": {"table": "bar", "column": "baz"},
    } == t.model_dump(by_alias=False)


def test_column_extract_column_from_dtype():
    t = col.Col.extract_column_from_dtype("numeric( 10, 2 )")
    assert t == {
        "unique": False,
        "pk": False,
        "nullable": True,
        "dtype": "numeric( 10, 2 )",
    }

    t = col.Col.extract_column_from_dtype(
        "varchar( 100 ) not null default 'Empty' check( <name> <> 'test' )"
    )
    assert t == {
        "unique": False,
        "pk": False,
        "nullable": False,
        "check": "check( <name> <> 'test' )",
        "dtype": "varchar( 100 )",
        "default": "'Empty'",
    }

    t = col.Col.extract_column_from_dtype("serial primary key")
    assert t == {
        "unique": False,
        "pk": True,
        "nullable": False,
        "dtype": "integer",
        "default": "nextval('tablename_colname_seq')",
    }

    t = col.Col.extract_column_from_dtype("integer null default 1")
    assert t == {
        "unique": False,
        "pk": False,
        "nullable": True,
        "dtype": "integer",
        "default": "1",
    }

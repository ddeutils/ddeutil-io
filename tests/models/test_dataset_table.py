import ddeutil.io.models.datasets.db as db


def test_base_table_init():
    t = db.BaseTbl(
        name="foo",
        features=[db.Col(name="foo", dtype="varchar( 10 )")],
    )
    assert t.features == [db.Col(name="foo", dtype="varchar( 10 )")]


def test_table_init():
    t = db.Tbl(
        name="foo",
        features=[db.Col(name="foo", dtype="varchar( 10 )")],
    )
    assert t.features == [db.Col(name="foo", dtype="varchar( 10 )")]
    assert t.pk == db.Pk(of="foo")
    assert t.fk == []

    t = db.Tbl(
        name="foo", features=[{"name": "foo", "dtype": "varchar( 100 )"}]
    )
    assert t.model_dump(by_alias=False) == {
        "name": "foo",
        "desc": None,
        "features": [
            {
                "check": None,
                "default": None,
                "desc": None,
                "dtype": {"max_length": 100, "type": "varchar"},
                "fk": {},
                "name": "foo",
                "nullable": True,
                "pk": False,
                "unique": False,
            }
        ],
        "pk": {"cols": [], "of": "foo"},
        "fk": [],
        "consts": [],
    }

    t = db.Tbl(
        name="foo",
        features=[{"name": "foo", "dtype": "varchar( 100 ) primary key"}],
    )
    assert t.model_dump(by_alias=False) == {
        "name": "foo",
        "desc": None,
        "features": [
            {
                "check": None,
                "default": None,
                "desc": None,
                "dtype": {"max_length": 100, "type": "varchar"},
                "fk": {},
                "name": "foo",
                "nullable": False,
                "pk": True,
                "unique": False,
            }
        ],
        "pk": {"cols": ["foo"], "of": "foo"},
        "fk": [],
        "consts": [],
    }


def test_table_init_with_pk():
    t = db.Tbl(
        name="foo",
        features=[{"name": "id", "dtype": "integer", "pk": True}],
    )
    assert t.model_dump(by_alias=False) == {
        "name": "foo",
        "desc": None,
        "features": [
            {
                "check": None,
                "default": None,
                "desc": None,
                "dtype": {"type": "integer"},
                "fk": {},
                "name": "id",
                "nullable": False,
                "pk": True,
                "unique": False,
            }
        ],
        "pk": {"cols": ["id"], "of": "foo"},
        "fk": [],
        "consts": [],
    }


def test_table_model_validate():
    t = db.Tbl.model_validate(
        {
            "name": "foo",
            "features": [
                {"name": "id", "dtype": "integer", "pk": True},
                {
                    "name": "name",
                    "dtype": "varchar( 256 )",
                    "nullable": False,
                },
            ],
        },
    )
    assert t.model_dump(by_alias=False) == {
        "name": "foo",
        "desc": None,
        "features": [
            {
                "check": None,
                "default": None,
                "desc": None,
                "dtype": {"type": "integer"},
                "fk": {},
                "name": "id",
                "nullable": False,
                "pk": True,
                "unique": False,
            },
            {
                "check": None,
                "default": None,
                "desc": None,
                "dtype": {"type": "varchar", "max_length": 256},
                "fk": {},
                "name": "name",
                "nullable": False,
                "pk": False,
                "unique": False,
            },
        ],
        "pk": {"cols": ["id"], "of": "foo"},
        "fk": [],
        "consts": [],
    }

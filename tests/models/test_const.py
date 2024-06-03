import ddeutil.io.models.const as const


def test_pk_init():
    t = const.Pk(of="foo")
    assert "foo" == t.of
    assert [] == t.cols

    t = const.Pk(of="foo", cols=["col1"])
    assert "foo_col1_pk" == t.name
    assert ["col1"] == t.cols

    t = const.Pk(of="foo", cols=["col1", "col2"])
    assert "foo_col1_col2_pk" == t.name
    assert ["col1", "col2"] == t.cols


def test_pk_model_validate():
    t = const.Pk.model_validate(
        {
            "of": "foo",
            "cols": ["col1"],
        }
    )
    assert "foo" == t.of
    assert ["col1"] == t.cols
    assert "foo_col1_pk" == t.name


def test_ref_init():
    t = const.Ref(tbl="foo", col="bar")
    assert "foo" == t.tbl
    assert "bar" == t.col


def test_fk_init():
    t = const.Fk(
        of="foo",
        to="test",
        ref=const.Ref(tbl="bar", col="baz"),
    )
    assert "foo" == t.of
    assert "test" == t.to
    assert "bar" == t.ref.tbl
    assert "baz" == t.ref.col
    assert "foo_test_bar_baz_fk" == t.name


def test_fk_model_validate():
    t = const.Fk.model_validate(
        {
            "of": "foo",
            "to": "test",
            "ref": {
                "tbl": "bar",
                "col": "baz",
            },
        }
    )
    assert "foo" == t.of
    assert "test" == t.to
    assert "bar" == t.ref.tbl
    assert "baz" == t.ref.col
    assert "foo_test_bar_baz_fk" == t.name

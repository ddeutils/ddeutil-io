import ddeutil.io.models.dtype as dtype


def test_char_init():
    t = dtype.CharType(type="char")
    assert "char" == t.type
    assert -1 == t.max_length

    t = dtype.CharType(type="char", max_length=1000)
    assert "char" == t.type
    assert 1000 == t.max_length


def test_char_model_validate():
    t = dtype.CharType.model_validate({"type": "char", "max_length": 1000})
    assert "char" == t.type
    assert 1000 == t.max_length


def test_varchar_init():
    t = dtype.VarcharType(type="varchar")
    assert "varchar" == t.type
    assert -1 == t.max_length

    t = dtype.VarcharType(type="varchar", max_length=1000)
    assert "varchar" == t.type
    assert 1000 == t.max_length

    t = dtype.VarcharType(type="varchar", max_length="1000")
    assert "varchar" == t.type
    assert 1000 == t.max_length


def test_varchar_model_validate():
    t = dtype.VarcharType.model_validate(
        {"type": "varchar", "max_length": 1000}
    )
    assert "varchar" == t.type
    assert 1000 == t.max_length

    t = dtype.VarcharType.model_validate(
        {"type": "varchar", "max_length": "1000"}
    )
    assert "varchar" == t.type
    assert 1000 == t.max_length


def test_int_init():
    t = dtype.IntegerType(type="int")
    assert "integer" == t.type

import ddeutil.io.models.__types as tp


def test_db_url():
    t = tp.CustomUrl(url="driver://name:pass@host:1234")
    assert "driver" == t.scheme
    assert "name" == t.username
    assert "pass" == t.password
    assert "host" == t.host
    assert 1234 == t.port
    assert {} == dict(t.query_params())

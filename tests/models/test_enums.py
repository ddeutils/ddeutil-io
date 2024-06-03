from ddeutil.io.models.__enums import Loading, Status


def test_status_failed():
    e: Status = Status.FAILED

    assert e == Status.FAILED
    assert e in Status
    assert e != Status.WAITING
    assert e.value == "FAILED"
    assert not e.in_process()
    assert e.is_failed()
    assert not e.is_done()


def test_loading():
    e: Loading = Loading.FULL_DUMP

    assert e == Loading.FULL_DUMP
    assert e != Loading.DELTA
    assert e.value == "F"
    assert not e.is_scd()

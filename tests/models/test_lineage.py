import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import ddeutil.io.models.__enums as enum
import ddeutil.io.models.lineage as lineages
from ddeutil.io.models.lineage import TZ


@mock.patch("ddeutil.io.models.lineage.datetime", wraps=datetime.datetime)
def test_ts_init(mock_datetime):
    mock_datetime.now.return_value = datetime.datetime(2023, 1, 1, 0, 0, 0)
    t = lineages.Ts()
    assert t.model_dump(by_alias=False) == {
        "ts": datetime.datetime(2023, 1, 1, 0, 0, 0).astimezone(
            tz=ZoneInfo(TZ)
        ),
        "tz": "Asia/Bangkok",
    }


@mock.patch("ddeutil.io.models.lineage.date", wraps=datetime.date)
@mock.patch("ddeutil.io.models.lineage.datetime", wraps=datetime.datetime)
def test_tag_init(mock_datetime, mock_date):
    mock_date.return_value = datetime.date(2023, 1, 1)
    mock_datetime.now.return_value = datetime.datetime(2023, 1, 1, 0, 0, 0)
    t = lineages.Tag()
    assert t.model_dump(by_alias=False) == {
        "author": "undefined",
        "desc": None,
        "labels": [],
        "ts": datetime.datetime(2023, 1, 1, 0, 0, 0).astimezone(
            tz=ZoneInfo(TZ)
        ),
        "vs": datetime.date(2023, 1, 1),
        "tz": "Asia/Bangkok",
    }


def test_task_init():
    t = lineages.Task()
    assert t.st == enum.Status.WAITING


def test_base_param_init():
    t = lineages.BaseParam.model_validate(
        obj={
            "foo": "bar",
            "test": "demo",
        }
    )
    assert t.extras == {
        "foo": "bar",
        "test": "demo",
    }


def test_normal_param():
    t = lineages.NormalParam.model_validate(
        obj={
            "run_date": "2023-01-01 00:00:00",
            "foo": "bar",
            "test": "demo",
            "extras": {
                "test": "replace",
            },
        }
    )
    assert t.run_date == datetime.datetime(2023, 1, 1, 0)
    assert t.extras == {
        "foo": "bar",
        "test": "replace",
    }


def test_base_task_init():
    t = lineages.BaseTask(st=enum.Status.WAITING)
    print(t.model_dump())

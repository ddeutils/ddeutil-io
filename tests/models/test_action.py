import ddeutil.io.models.action as act
import pytest

from .utils import param


@pytest.mark.parametrize(
    "inputs",
    [
        param({"elements": [1, 2, 3, 4], "do": "foo"}),
        param({"elements": ["1", "2", "3", "4"], "do": "foo"}),
        param({"elements": [{"foo": "bar"}, {"foo": "bar"}], "do": "foo"}),
    ],
)
def test_for_loop(inputs):
    t = act.Loop.model_validate(inputs)
    assert inputs["elements"] == t.elements
    assert inputs["do"] == t.do


def test_copy():
    t = act.Copy.model_validate(
        {
            "src": "input_df",
            "sink": "output_location",
        }
    )
    assert t.src == "input_df"
    assert t.sink == "output_location"

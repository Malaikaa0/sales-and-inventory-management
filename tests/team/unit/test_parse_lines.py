import pytest
from django.core.exceptions import ValidationError
from transactions.services import parse_lines


def test_empty_cart_rejected():
    with pytest.raises(ValidationError):
        parse_lines([])

def test_not_a_list_rejected():
    with pytest.raises(ValidationError):
        parse_lines("abc")

def test_missing_quantity_rejected():
    with pytest.raises(ValidationError):
        parse_lines([{"id": 1}])

@pytest.mark.parametrize("qty", [0, 100001])
def test_quantity_outside_limits_rejected(qty):
    with pytest.raises(ValidationError):
        parse_lines([{"id": 1, "quantity": qty}])

@pytest.mark.parametrize("qty", [1, 2, 99999, 100000])
def test_quantity_inside_limits_accepted(qty):
    assert parse_lines([{"id": 1, "quantity": qty}])[1] == qty

def test_200_lines_ok_201_rejected():
    ok = [{"id": i, "quantity": 1} for i in range(200)]
    assert len(parse_lines(ok)) == 200
    with pytest.raises(ValidationError):
        parse_lines(ok + [{"id": 999, "quantity": 1}])

def test_duplicate_items_are_merged():
    assert parse_lines([{"id": 1, "quantity": 2}, {"id": 1, "quantity": 3}])[1] == 5

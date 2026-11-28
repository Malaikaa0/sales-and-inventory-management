"""D1 (GitHub Issue #1): a quantity above the maximum must be told the maximum."""
import pytest
from django.core.exceptions import ValidationError

from transactions.services import parse_lines


@pytest.mark.parametrize('quantity, message', [
    (0, 'Quantities must be at least 1.'),
    (100001, 'Quantities cannot be more than 100000.'),
])
def test_quantity_rejection_names_the_limit_that_was_broken(quantity, message):
    with pytest.raises(ValidationError) as error:
        parse_lines([{'id': 1, 'quantity': quantity}])
    assert error.value.messages == [message]

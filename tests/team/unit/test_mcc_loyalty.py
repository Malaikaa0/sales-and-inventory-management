"""
MCC for the loyalty redemption decision in transactions.services.create_sale.

For a redemption of R points (R > 0), the redemption is accepted when
C1 and C2 and C3 and C4:

    C1  loyalty is enabled
    C2  R >= min_redeem
    C3  R <= customer balance
    C4  R <= loyalty.max_redeemable(balance, sub_total)

C4 true forces C1 and C3 true, so 10 of the 16 combinations are feasible.
"""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from accounts.models import Customer
from store.models import Category, Item
from transactions import loyalty
from transactions.models import Sale
from transactions.services import create_sale

REDEEM = 50

# row id, enabled, min_redeem, balance, bill, (C1, C2, C3, C4), expected error
ROWS = [
    ('R1-TTTT', True, 10, 100, '100.00', 'TTTT', None),
    ('R2-TFTT', True, 60, 100, '100.00', 'TFTT', 'at least'),
    ('R3-TTTF', True, 10, 100, '20.00', 'TTTF', 'cannot exceed'),
    ('R4-TTFF', True, 10, 30, '100.00', 'TTFF', 'only has'),
    ('R5-TFTF', True, 60, 100, '20.00', 'TFTF', 'at least'),
    ('R6-TFFF', True, 60, 30, '100.00', 'TFFF', 'at least'),
    ('R7-FTTF', False, 10, 100, '100.00', 'FTTF', 'not enabled'),
    ('R8-FTFF', False, 10, 30, '100.00', 'FTFF', 'not enabled'),
    ('R9-FFTF', False, 60, 100, '100.00', 'FFTF', 'not enabled'),
    ('R10-FFFF', False, 60, 30, '100.00', 'FFFF', 'not enabled'),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'enabled, min_redeem, balance, bill, conditions, error',
    [row[1:] for row in ROWS], ids=[row[0] for row in ROWS],
)
def test_redemption_mcc(settings, enabled, min_redeem, balance, bill, conditions, error):
    settings.LOYALTY = {
        'enabled': enabled, 'earn_per': '100', 'point_value': '1.00', 'min_redeem': min_redeem,
    }
    category = Category.objects.create(name='Test')
    item = Item.objects.create(name='Keyboard', category=category, quantity=10, price=Decimal(bill))
    customer = Customer.objects.create(first_name='Ali', loyalty_points=balance)

    # The inputs really produce the condition values this row claims.
    cfg = loyalty.config()
    actual = (
        cfg['enabled'],
        REDEEM >= cfg['min_redeem'],
        REDEEM <= balance,
        REDEEM <= loyalty.max_redeemable(balance, Decimal(bill)),
    )
    assert ''.join('T' if value else 'F' for value in actual) == conditions

    def sell():
        return create_sale(
            user=None, customer_id=customer.pk, items=[{'id': item.pk, 'quantity': 1}],
            amount_paid=1000, redeem_points=REDEEM,
        )

    if error is None:
        sale = sell()
        assert sale.loyalty_points_redeemed == REDEEM
        assert sale.discount_amount == Decimal('50.00')
        assert sale.grand_total == Decimal('50.00')
        customer.refresh_from_db()
        item.refresh_from_db()
        assert (customer.loyalty_points, item.quantity) == (balance - REDEEM, 9)
    else:
        with pytest.raises(ValidationError, match=error):
            sell()
        customer.refresh_from_db()
        item.refresh_from_db()
        assert (customer.loyalty_points, item.quantity) == (balance, 10)
        assert Sale.objects.count() == 0

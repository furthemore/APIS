from unittest import TestCase

from registration.models import Order


class TestOrderPreSave(TestCase):
    def test_order_pre_save(self):
        order = Order(total=20, reference="FOOBAR")
        order.save()
        self.assertEqual(order.billingState, "")

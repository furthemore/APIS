from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from registration.models import *


"""
There's a few options for where these metrics could end up.  These should eventually be configurable:
 - built-in database metrics table: (simplest, no external dependancy).
 - prometheus: Time-series database, with existing reporters for e.g. django request processors.
 - influxdb: Another great time-series database.
"""


def get_paid_order_items(event):
    """
    Returns all order items for paid and completed orders with a valid price-level assignment.
    (Effectively, the total number of badges for a particular event)

    :param event: event to filter by
    :return: List[order_items]
    """
    order_items = OrderItem.objects.filter(badge__event=event).exclude(
        Q(order__isnull=True)
        | Q(order__billingType=Order.UNPAID)
        | Q(priceLevel__isnull=True)
    )
    return order_items


class Command(BaseCommand):
    help = "Calculates metrics for all events to record to time-series"

    def handle(self, *args, **options):
        for event in Event.objects.filter():
            # Attendee data
            order_items = get_paid_order_items(event)
            total_count = order_items.count()

            # Bin by registration level
            level_bins = {}
            price_levels = PriceLevel.objects.filter()
            for level in price_levels:
                level_bins[level.id] = order_items.filter(priceLevel=level).count()

            # Staff counts
            staff = Staff.objects.filter(event=event)
            total_staff_count = staff.count()

            active_staff_count = 0
            for s in staff:
                if s.attendee.getBadge() is not None:
                    active_staff_count += 1

            print "Event: {0} - (total: {1})".format(event, total_count)
            for level in price_levels:
                print level, "-", level_bins[level.id]
            print "Staff: {0} ({1} active)".format(
                total_staff_count, active_staff_count
            )
            print ("==========")

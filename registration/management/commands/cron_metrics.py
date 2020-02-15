import datetime
from abc import ABCMeta, abstractmethod

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from influxdb import InfluxDBClient

from registration.models import *


"""
There's a few options for where these metrics could end up.  These should eventually be configurable:
 - built-in database metrics table: (simplest, no external dependency).
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
        | Q(order__status__in=(Order.FAILED, Order.REFUNDED, Order.REFUND_PENDING))
        | Q(priceLevel__isnull=True)
    )
    return order_items


class Command(BaseCommand):
    help = "Calculates metrics for all events to record to time-series"

    def handle(self, *args, **options):
        backend_class = eval(settings.APIS_METRICS_BACKEND)
        try:
            backend_settings = settings.APIS_METRICS_SETTINGS
        except AttributeError:
            backend_settings = {}
        backend = backend_class(backend_settings)

        backend_writer = backend.write
        if hasattr(backend, "batch"):
            backend_writer = backend.batch

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
            staff = Staff.objects.filter(event=event).select_related("attendee")
            total_staff_count = staff.count()

            active_staff = (
                Staff.objects.filter(event=event)
                .prefetch_related("attendee__badge")
                .filter(attendee__badge__event=event)
            )
            active_staff_count = active_staff.count()

            print "Event: {0} - (total: {1})".format(event, total_count)
            for level in price_levels:
                print level, "-", level_bins[level.id]
                backend.write(event, level, level_bins[level.id])
            print "Staff: {0} ({1} active)".format(
                total_staff_count, active_staff_count
            )
            backend.write(event, "staff_total", total_staff_count)
            backend.write(event, "staff_active", active_staff_count)
            print ("==========")

        if hasattr(backend, "batch"):
            backend.flush()


class CronReporterABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, config):
        pass

    @abstractmethod
    def write(self, event, topic, value):
        pass


class DummyReporter(CronReporterABC):
    def __init__(self, config):
        pass

    def write(self, event, topic, value):
        pass


CronReporterABC.register(DummyReporter)


class InfluxDBReporter(CronReporterABC):
    def __init__(self, config):
        """
        Statistics collecting backend for recording to InfluxDB

        :param config: dictionary of InfluxDB-specific client parameters
               (see https://influxdb-python.readthedocs.io/en/latest/api-documentation.html#influxdbclient)
        """
        self.client = InfluxDBClient(**config)
        db_name = config.get("database")
        if db_name:
            self.client.create_database(db_name)

        self.json_body = []

    @staticmethod
    def timestamp():
        now = datetime.datetime.utcnow()
        return now.isoformat("T") + "Z"

    def batch(self, event, topic, value):
        """
        Stage a data point to record to be committed to the database in bulk

        :param event:
        :param topic:
        :param value:
        :return:
        """
        document = {
            "measurement": topic,
            "tags": {"event": event, "site": Site.objects.get_current().domain,},
            "time": self.timestamp(),
            "fields": {"Int_value": value,},
        }
        self.json_body.append(document)

    def flush(self):
        self.client.write_points(self.json_body)
        self.json_body = []

    def write(self, event, topic, value):
        now = datetime.datetime.utcnow()
        timestamp = now.isoformat("T") + "Z"

        json_body = [
            {
                "measurement": topic,
                "tags": {"event": event, "site": Site.objects.get_current().domain,},
                "time": timestamp,
                "fields": {"Int_value": value,},
            }
        ]

        self.client.write_points(json_body)


CronReporterABC.register(InfluxDBReporter)

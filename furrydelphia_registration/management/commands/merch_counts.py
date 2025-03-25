from django.core.management.base import BaseCommand

from registration.models import (
    AttendeeOptions,
    Event,
    PriceLevelOption,
    ShirtSizes,
)


class Command(BaseCommand):
    help = "Generates a merchandise (order items) report"

    def prompt_int(self, prompt, silent=False):
        selection = input(prompt)
        try:
            return int(selection)
        except ValueError:
            if not silent:
                print("Invalid selection!")
            return None

    def handle(self, *args, **options):
        default_event = Event.objects.get(default=True)
        SHIRT_SIZES = {
            str(shirt.id): shirt.name for shirt in ShirtSizes.objects.filter()
        }
        for idx, event in enumerate(Event.objects.filter()):
            print(("{0} - {1}".format(idx + 1, event)))
        selection = self.prompt_int(
            "Enter index of event to report on [{0}] > ".format(default_event.name),
            True,
        )
        if selection is None:
            event = default_event
        else:
            event = Event.objects.get(id=selection)
        options = PriceLevelOption.objects.filter()
        for oc, option in enumerate(options):
            print(("{0} - {1}".format(oc, option)))
        selection = self.prompt_int("Enter index of item to report on > ")
        if selection is None:
            return
        selected_options = AttendeeOptions.objects.filter(
            option=options[selection], orderItem__badge__event=event
        )
        bins = {}
        staff = 0
        levels = {}
        print(
            (
                "{0} orders with {1} option selected for {2}".format(
                    selected_options.count(), options[selection], event
                )
            )
        )
        for attendee_option in selected_options:
            attendee_option.orderItem.badge
            try:
                levels[str(attendee_option.orderItem.priceLevel)] += 1
            except KeyError:
                levels[str(attendee_option.orderItem.priceLevel)] = 1

            if attendee_option.option.optionExtraType == "ShirtSizes":
                assert str(attendee_option.optionValue) in list(
                    SHIRT_SIZES.keys()
                ), "Invalid response in AttendeeOption(id={0})".format(
                    attendee_option.id
                )
                try:
                    bins[SHIRT_SIZES[str(attendee_option.optionValue)]] += 1
                except KeyError:
                    bins[SHIRT_SIZES[str(attendee_option.optionValue)]] = 1
            else:
                try:
                    bins[str(attendee_option.optionValue)] += 1
                except KeyError:
                    bins[str(attendee_option.optionValue)] = 1
        for k, v in bins.items():
            print(("{0}, {1}".format(k, v)))
        print("Levels:")
        for k, v in levels.items():
            print(("{0}, {1}".format(k, v)))

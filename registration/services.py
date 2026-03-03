from typing import Dict, Iterable, Iterator, List, Optional, Union

from registration.models import AttendeeOptions, OrderItem, PriceLevelOption


class CreateAttendeeOptions:
    def __init__(self, order_item: OrderItem):
        self.order_item = order_item
        if not self.order_item.priceLevel:
            raise ValueError("OrderItem must have PriceLevel")

        self.price_level_options: Dict[int, PriceLevelOption] = {
            plo.id: plo for plo in self.order_item.priceLevel.priceLevelOptions.all()
        }

    def save_options(self, options: Iterable[dict]) -> List[AttendeeOptions]:
        entries = []

        for option in options:
            price_level_option = self.get_option(option["id"])
            if not price_level_option:
                raise ValueError(f"Unknown option ID: {option['id']}")

            value = None
            if price_level_option.optionExtraType == "int" and option["value"] == "":
                value = "0"
            elif option["value"] != "":
                value = option["value"]

            if value is not None:
                entries.append((price_level_option, value))

        for price_level_option in self.private_options():
            value = self._default_option_value(price_level_option)
            entries.append((price_level_option, value))

        attendee_options = [
            AttendeeOptions(orderItem=self.order_item, option=option, optionValue=value)
            for option, value in entries
        ]

        return AttendeeOptions.objects.bulk_create(attendee_options)

    def get_option(
        self, option_id: Union[str, int], only_public: bool = True
    ) -> Optional[PriceLevelOption]:
        option = self.price_level_options.get(int(option_id))
        if option and (option.public or not only_public):
            return option

    def private_options(self) -> Iterator[PriceLevelOption]:
        for price_level_option in self.price_level_options.values():
            if not price_level_option.public:
                yield price_level_option

    @staticmethod
    def _default_option_value(price_level_option: PriceLevelOption) -> str:
        match price_level_option.optionExtraType:
            case "int":
                return "1"
            case "bool":
                return "True"
            case extraType:
                raise ValueError(
                    f"Cannot get default value for {extraType} option type"
                )

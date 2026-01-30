from unittest import TestCase

from registration.mqtt import format_topic, get_topic


class TestMqtt(TestCase):
    def test_format_topic(self):
        test_cases = [
            ("$hello", "hello"),
            ("hello+", "hello"),
            ("hello/world", "hello/world"),
            ("hello / world", "hello/world"),
        ]

        for test_case, expected in test_cases:
            self.assertEqual(format_topic(test_case), expected)

        with self.assertRaises(ValueError):
            format_topic("test/#")

        self.assertEqual(format_topic("test/#", allow_wildcard=True), "test/#")

    def test_get_topic(self):
        test_cases = [
            (["$testing/1/2/3"], "apis/name/testing/1/2/3"),
            (["hello", "multiple"], "apis/name/hello/multiple"),
        ]

        for test_case, expected in test_cases:
            self.assertEqual(get_topic(*test_case, name="name"), expected)

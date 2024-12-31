import os
from unittest import TestCase
from unittest.mock import patch

from registration import printing

TAGS = [
    {
        "name": "🦊 Barkley Woofington 🐶",
        "number": "S-6969",
        "level": "Top Dog",
        "title": "",
        "age": 20,
    },
    {
        "name": "🦊 rechñer fox",
        "number": "S-0001",
        "level": "Foxo",
        "title": "",
        "age": 12,
    },
]


class TestNametag(TestCase):
    def setUp(self) -> None:
        self.tags = TAGS
        self.default_theme = "apis"

        self.nametags = printing.Nametag()

    def test_list_templates(self) -> None:
        list = self.nametags.list_templates()
        self.assertEqual(list, ["apis", "fd_labels", "furrydelphia"])

    def test__get_template_path(self) -> None:
        result = self.nametags._get_template_path("foo", "/home/apis/resources")
        self.assertEqual(result, "/home/apis/resources/foo")

    def test_read_config(self) -> None:
        config = self.nametags.read_config(self.default_theme)
        expected_config = {
            "default": {
                "bottom": "0",
                "height": "89",
                "left": "0",
                "orientation": "landscape",
                "right": "0",
                "top": "0",
                "width": "28",
                "zoom": "0.89",
            }
        }

        self.assertEqual(config, expected_config)

    def test_nametag(self) -> None:
        for tag in self.tags:
            result = self.nametags.nametag("apis", **tag)
            self.assertIn(f"""<div class="name resize">{tag['name']}</div>""", result)
            self.assertIn(
                f"""<span class="pull-right">{tag['number']}</span>""", result
            )
            self.assertIn(f"""<span class="pull-left">{tag['level']}</span>""", result)


class TestMain(TestCase):
    def setUp(self) -> None:
        self.printing = printing.Main(False)

    def test_nametag(self) -> None:
        tag = {
            "name": "🦊 Barkley Woofington 🐶",
            "number": "S-6969",
            "level": "Top Dog",
            "title": "",
        }
        with patch("subprocess.check_call", return_value=0) as patched:
            pdf = self.printing.nametag(**tag)
        self.assertTrue(os.path.isfile(pdf))
        self.assertEqual(patched.call_count, 1)
        args = patched.call_args[0][0]
        # Last argument is always the filename with path
        self.assertEqual(args[-1], pdf)
        self.printing.cleanup()

    def test_nametags(self) -> None:
        with patch("subprocess.check_call", return_value=0) as patched:
            pdf = self.printing.nametags(TAGS)
        self.assertTrue(os.path.isfile(pdf))
        self.assertEqual(patched.call_count, 1)
        args = patched.call_args[0][0]
        # Last argument is always the filename with path
        self.assertEqual(args[-1], pdf)
        self.printing.cleanup()

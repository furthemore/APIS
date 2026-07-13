import tempfile
from http import HTTPStatus
from pathlib import Path

from django.test import SimpleTestCase, override_settings


class MaintenanceModeTest(SimpleTestCase):
    """Test that django-maintenance-mode works as configured.

    Uses SimpleTestCase (no database) since maintenance mode is purely
    middleware-based and doesn't require DB access.
    """

    def setUp(self):
        self.state_file = Path(tempfile.mktemp(suffix="_maintenance_mode_state.txt"))
        self.state_file.write_text("0")

    def tearDown(self):
        self.state_file.unlink(missing_ok=True)

    def _enable_maintenance(self):
        self.state_file.write_text("1")

    def _disable_maintenance(self):
        self.state_file.write_text("0")

    @override_settings(MAINTENANCE_MODE=True)
    def test_maintenance_mode_returns_503(self):
        """When maintenance mode is on, normal pages return 503."""
        response = self.client.get("/registration/")
        self.assertEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    @override_settings(MAINTENANCE_MODE=True)
    def test_maintenance_page_renders_without_error(self):
        """The 503 maintenance template renders successfully (no missing static files)."""
        response = self.client.get("/registration/")
        self.assertEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertIn(b"maintenance", response.content.lower())

    @override_settings(MAINTENANCE_MODE=False)
    def test_normal_mode_does_not_return_503(self):
        """When maintenance mode is off, pages are not blocked by maintenance middleware."""
        self.client.raise_request_exception = False
        response = self.client.get("/registration/")
        self.assertNotEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    @override_settings(MAINTENANCE_MODE=True, MAINTENANCE_MODE_IGNORE_ADMIN_SITE=True)
    def test_admin_site_accessible_during_maintenance(self):
        """Admin site is reachable even during maintenance (per MAINTENANCE_MODE_IGNORE_ADMIN_SITE)."""
        response = self.client.get("/admin/login/")
        self.assertNotEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    @override_settings(
        MAINTENANCE_MODE=True, MAINTENANCE_MODE_IGNORE_URLS=("^/accounts/",)
    )
    def test_ignored_urls_accessible_during_maintenance(self):
        """URLs matching MAINTENANCE_MODE_IGNORE_URLS are accessible during maintenance."""
        self.client.raise_request_exception = False
        response = self.client.get("/accounts/login/")
        self.assertNotEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    def test_state_file_controls_maintenance_mode(self):
        """The file-based state backend enables/disables maintenance mode."""
        self.client.raise_request_exception = False
        with self.settings(MAINTENANCE_MODE_STATE_FILE_PATH=str(self.state_file)):
            self._disable_maintenance()
            response = self.client.get("/registration/")
            self.assertNotEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

            self._enable_maintenance()
            response = self.client.get("/registration/")
            self.assertEqual(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

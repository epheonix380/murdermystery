from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class PublicFileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_case", "hollowpine", stdout=StringIO())

    def test_serves_map(self):
        response = self.client.get("/cases/hollowpine/public/map.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Floor plan of The Last Chapter at Hollowpine Lodge", b"".join(response.streaming_content))

    def test_case_json_files_are_not_reachable(self):
        for path in [
            "/cases/hollowpine/public/../solution.json",
            "/cases/hollowpine/public/%2e%2e/solution.json",
            "/cases/hollowpine/public/..%2fsolution.json",
            "/cases/hollowpine/solution.json",
            "/cases/hollowpine/roles.json",
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_unknown_case(self):
        self.assertEqual(self.client.get("/cases/nope/public/map.svg").status_code, 404)

from django.test import TestCase


class FormatSuffixTestCase(TestCase):
    def test_pages_without_a_format_argument_answer_a_suffix_with_404(self) -> None:
        # Scanners probe these; the homepage used to crash on them with a 500.
        for path in ("/.env", "/.npmrc", "/about.json"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        # The admin's own catch-all takes it, sending anonymous visitors to log in.
        self.assertEqual(self.client.get("/admin/login.json").status_code, 302)

    def test_api_views_keep_their_format_suffixes(self) -> None:
        for path in ("/manuscripts/", "/manuscripts.json"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

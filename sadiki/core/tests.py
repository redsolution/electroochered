from django.test import TestCase


class BasicUrlsTests(TestCase):

    def test_root(self):
        self.assertEqual(self.client.get('/').status_code, 200)

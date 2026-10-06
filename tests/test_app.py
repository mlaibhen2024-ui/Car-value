import unittest

from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_home_page_has_history_link_and_form_submission(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/evaluate"', response.data)
        self.assertIn(b'method="post"', response.data)
        self.assertIn(b'/history', response.data)



if __name__ == "__main__":
    unittest.main()
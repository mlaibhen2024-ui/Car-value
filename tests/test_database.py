import os
import tempfile
import unittest
from pathlib import Path

import db


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(
            suffix=".db",
            delete=False,
        )
        self.temp_db.close()

        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_db.name)

        db.init_db()

        db.create_user(
            name="Test User",
            email="test@example.com",
            password_hash="test-hash",
        )

        self.user = db.get_user_by_email(
            "test@example.com"
        )

    def tearDown(self):
        db.DB_PATH = self.original_db_path

        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_create_user(self):
        self.assertIsNotNone(self.user)
        self.assertEqual(
            self.user["email"],
            "test@example.com",
        )

    def test_save_and_retrieve_valuation(self):
        db.save_valuation(
            user_id=self.user["id"],
            make="Toyota",
            model="Camry",
            vehicle_type="sedan",
            price=30000,
            age=3,
            mileage=30000,
            estimated_value=22000,
        )

        rows = db.get_recent_valuations(
            user_id=self.user["id"],
            limit=5,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["make"], "Toyota")
        self.assertEqual(rows[0]["model"], "Camry")
        self.assertEqual(
            rows[0]["estimated_value"],
            22000,
        )

    def test_users_only_see_their_own_valuations(self):
        db.create_user(
            name="Second User",
            email="second@example.com",
            password_hash="test-hash",
        )

        second_user = db.get_user_by_email(
            "second@example.com"
        )

        db.save_valuation(
            user_id=self.user["id"],
            make="Toyota",
            model="Camry",
            vehicle_type="sedan",
            price=30000,
            age=3,
            mileage=30000,
            estimated_value=22000,
        )

        db.save_valuation(
            user_id=second_user["id"],
            make="Honda",
            model="Civic",
            vehicle_type="sedan",
            price=28000,
            age=2,
            mileage=20000,
            estimated_value=23000,
        )

        first_user_rows = db.get_recent_valuations(
            user_id=self.user["id"],
            limit=20,
        )

        self.assertEqual(len(first_user_rows), 1)
        self.assertEqual(
            first_user_rows[0]["make"],
            "Toyota",
        )


if __name__ == "__main__":
    unittest.main()
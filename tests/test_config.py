import importlib
import os
import unittest

import backend.config as config_module


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_env = {
            "MONGO_URI": os.environ.get("MONGO_URI"),
            "MONGO_DB_NAME": os.environ.get("MONGO_DB_NAME"),
        }

    def tearDown(self):
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(config_module)

    def test_mongo_settings_come_from_environment(self):
        os.environ["MONGO_URI"] = "mongodb://example-host:27017"
        os.environ["MONGO_DB_NAME"] = "helpdesk_test_db"

        importlib.reload(config_module)

        self.assertEqual(config_module.Config.MONGO_URI, "mongodb://example-host:27017")
        self.assertEqual(config_module.Config.MONGO_DB_NAME, "helpdesk_test_db")


if __name__ == "__main__":
    unittest.main()

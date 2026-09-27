import os
import unittest
from unittest import mock

from common.env import env_bool, env_int


class EnvBoolTests(unittest.TestCase):
    def test_true_values(self):
        for raw in ("1", "true", "True", "TRUE", "yes", "YES", "on", "On"):
            with mock.patch.dict(os.environ, {"FLAG": raw}):
                self.assertTrue(env_bool("FLAG"), raw)

    def test_false_values_ignore_default(self):
        for raw in ("0", "false", "False", "no", "off", ""):
            with mock.patch.dict(os.environ, {"FLAG": raw}):
                self.assertFalse(env_bool("FLAG", default=True), raw)

    def test_unset_uses_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(env_bool("FLAG"))
            self.assertTrue(env_bool("FLAG", default=True))


class EnvIntTests(unittest.TestCase):
    def test_parses_and_defaults(self):
        with mock.patch.dict(os.environ, {"N": "300"}):
            self.assertEqual(env_int("N", 1), 300)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_int("MISSING", 7), 7)

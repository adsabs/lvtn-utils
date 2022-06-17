import inspect
import os
import unittest
from builtins import str

from mock import patch

import lvtn_utils


class TestApp(unittest.TestCase):
    """
    Tests the appliction's methods
    """

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_load_config(self):
        with patch("lvtn_utils.load_module") as load_module:
            c = lvtn_utils.load_config()
            f = os.path.abspath(
                os.path.join(os.path.dirname(inspect.getsourcefile(lvtn_utils)), "..")
            )
            self.assertEqual((f + "/config.py",), load_module.call_args_list[0][0])
            self.assertEqual((f + "/local_config.py",), load_module.call_args_list[1][0])
            self.assertEqual(c["PROJ_HOME"], f)

        with patch("lvtn_utils.load_module") as load_module:
            lvtn_utils.load_config("/tmp")
            self.assertEqual(("/tmp/config.py",), load_module.call_args_list[0][0])
            self.assertEqual(("/tmp/local_config.py",), load_module.call_args_list[1][0])

    def test_load_module(self):
        f = os.path.abspath(
            os.path.join(
                os.path.dirname(inspect.getsourcefile(lvtn_utils)),
                "../tests/config_sample.py",
            )
        )
        x = lvtn_utils.load_module(f)
        self.assertEqual(x, {"FOO": {"bar": ["baz", 1]}})

    def test_setup_logging(self):
        with patch("lvtn_utils.ConcurrentRotatingFileHandler") as cloghandler:
            lvtn_utils.setup_logging("app")
            f = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

            test_data = "call(filename='{homedir}/logs/app.log', maxBytes=10485760, backupCount=10, mode='a', encoding='UTF-8')".format(
                homedir=f
            )

            self.assertEqual(test_data, str(cloghandler.call_args))

    def test_get_date(self):
        """Check we always work with UTC dates"""

        d = lvtn_utils.get_date()
        self.assertTrue(d.tzname() == "UTC")

        d1 = lvtn_utils.get_date("2009-09-04T01:56:35.450686Z")
        self.assertTrue(d1.tzname() == "UTC")
        self.assertEqual(d1.isoformat(), "2009-09-04T01:56:35.450686+00:00")
        self.assertEqual(lvtn_utils.date2solrstamp(d1), "2009-09-04T01:56:35.450686Z")

        d2 = lvtn_utils.get_date("2009-09-03T20:56:35.450686-05:00")
        self.assertTrue(d2.tzname() == "UTC")
        self.assertEqual(d2.isoformat(), "2009-09-04T01:56:35.450686+00:00")
        self.assertEqual(lvtn_utils.date2solrstamp(d2), "2009-09-04T01:56:35.450686Z")

        d3 = lvtn_utils.get_date("2009-09-03T20:56:35.450686")
        self.assertTrue(d3.tzname() == "UTC")
        self.assertEqual(d3.isoformat(), "2009-09-03T20:56:35.450686+00:00")
        self.assertEqual(lvtn_utils.date2solrstamp(d3), "2009-09-03T20:56:35.450686Z")

    def test_update_from_env(self):
        os.environ["FOO"] = "2"
        os.environ["BAR"] = "False"
        os.environ["ORCID_PIPELINE_BAR"] = "True"
        conf = {"FOO": 1, "BAR": False}
        lvtn_utils.conf_update_from_env("ORCID_PIPELINE", conf)
        self.assertEqual(conf, {"FOO": 2, "BAR": True})


if __name__ == "__main__":
    unittest.main()

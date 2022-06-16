# -*- coding: utf-8 -*-

import json
import os
import time
import unittest
from inspect import currentframe, getframeinfo

import lvtn1_utils
from lvtn1_utils.exceptions import UnicodeHandlerError


def _read_file(fpath):
    with open(fpath, "r") as fi:
        return fi.read()


class TestInit(unittest.TestCase):
    def test_logging(self):
        logdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs"))
        foo_log = logdir + "/foo.bar.log"
        if os.path.exists(foo_log):
            os.remove(foo_log)
        logger = lvtn1_utils.setup_logging("foo.bar")
        logger.warning("first")
        frameinfo = getframeinfo(currentframe())

        # print foo_log
        self.assertTrue(os.path.exists(foo_log))
        c = _read_file(foo_log)
        j = json.loads(c)

        self.assertEqual(j["message"], "first")
        self.assertTrue("hostname" in j)

        # verify warning has filename and linenumber
        self.assertEqual(os.path.basename(frameinfo.filename), j["filename"])
        self.assertEqual(j["lineno"], frameinfo.lineno - 1)

        time.sleep(0.01)
        # now multiline message
        logger.warning("second\nthird")
        logger.warning("last")
        c = _read_file(foo_log)

        found = False
        msecs = False
        for x in c.strip().split("\n"):
            j = json.loads(x)
            self.assertTrue(j)
            if j["message"] == "second\nthird":
                found = True
            t = lvtn1_utils.get_date(j["asctime"])
            if t.microsecond > 0:
                msecs = True

        self.assertTrue(found)
        self.assertTrue(msecs)

    def test_u2asc(self):

        input1 = "benìtez, n"
        input2 = "izzet, sakallı"

        output1 = lvtn1_utils.u2asc(input1)
        output2 = lvtn1_utils.u2asc(input2)

        self.assertEqual(output1, "benitez, n")
        self.assertEqual(output2, "izzet, sakalli")

        input3 = input2.encode("utf16")
        self.assertRaises(UnicodeHandlerError, lvtn1_utils.u2asc, input3)


if __name__ == "__main__":
    unittest.main()

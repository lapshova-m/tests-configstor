import unittest
import requests_ts


requests_test_suite = unittest.TestSuite()
requests_test_suite.addTest(unittest.makeSuite(requests_ts.GetConfigTestCase))

print("Count of tests: " + str(requests_test_suite.countTestCases()) + "\n")
runner = unittest.TextTestRunner(verbosity=2)
runner.run(requests_test_suite)
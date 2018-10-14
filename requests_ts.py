# Test suite for checking requests and responses for ConfigStore
import copy
import json
import unittest

import postgresql as psql
import requests
from recordtype import recordtype

SERVICE_URL = "http://127.0.0.1:8078/get_config"
INCORRECT_DATA = "There is incorrect data in response"
RECORD_NOT_FOUND = {"error": "record not found"}
MODEL_NOT_PRESENT = {"error": "config model not present"}
BAD_INPUT = {"error": "Bad input"}


class BasicGetConfig(unittest.TestCase):
    """
    Basic class for preparing test's data in DB before execution all tests
    and for deleting all test's data from DB at the end of testing
    """
    @classmethod
    def setUpClass(cls):
        # Create test's data
        cls.test_data_list = []
        cls.TestDataDevelop = recordtype("TestDataDevelop",
                                         "type data host port database user \
                                         password schema")
        cls.TestDataTest = recordtype("TestDataTest",
                                      "type data host port virtualhost user \
                                      password")
        cls.test_data_list.append(
            cls.TestDataDevelop("Develop.mr_robot", "test_data", "test_host",
                                1111, "test_database", "test_user",
                                "test_password", "test_schema"))
        cls.test_data_list.append(
            cls.TestDataTest("Test.vpn", "test_data", "test_host", 2222,
                             "test_virtualhost", "test_user", "test_password"))

        # add new test's data to table develop_mr_robot_configs
        with psql.open(host="localhost", user="test_work", database="db",
                       password="pass") as db:
            if not db.query(
                    f"SELECT data FROM develop_mr_robot_configs\
                    WHERE data='{cls.test_data_list[0].data}'"):
                db.query(f"INSERT INTO develop_mr_robot_configs (data, host,\
                                  port, database, \"user\", password, schema)\
                                  VALUES \
                                  ('{cls.test_data_list[0].data}',\
                                   '{cls.test_data_list[0].host}',\
                                   '{cls.test_data_list[0].port}',\
                                   '{cls.test_data_list[0].database}',\
                                   '{cls.test_data_list[0].user}',\
                                   '{cls.test_data_list[0].password}',\
                                   '{cls.test_data_list[0].schema}')")

        # add new test's data to table test_vpn_configs
        with psql.open(host="localhost", user="test_work", database="db",
                       password="pass") as db:
            if not db.query(
                    f"SELECT data FROM test_vpn_configs\
                    WHERE data='{cls.test_data_list[1].data}'"):
                db.query(f"INSERT INTO test_vpn_configs (data, host, port,\
                                  virtualhost, \"user\", password) VALUES \
                                  ('{cls.test_data_list[1].data}',\
                                   '{cls.test_data_list[1].host}',\
                                   '{cls.test_data_list[1].port}',\
                                   '{cls.test_data_list[1].virtualhost}',\
                                   '{cls.test_data_list[1].user}',\
                                   '{cls.test_data_list[1].password}')")

    @classmethod
    def tearDownClass(cls):
        # delete new test's data to table develop_mr_robot_configs
        with psql.open(host="localhost", user="test_work", database="db",
                       password="pass") as db:
            if db.query(
                    f"SELECT data FROM develop_mr_robot_configs\
                    WHERE data='{cls.test_data_list[0].data}'"):
                db.query(f"DELETE FROM develop_mr_robot_configs WHERE data = \
                  '{cls.test_data_list[0].data}'")

        # delete new test's data to table test_vpn_configs
        with psql.open(host="localhost", user="test_work", database="db",
                       password="pass") as db:
            if db.query(
                    f"SELECT data FROM test_vpn_configs\
                    WHERE data='{cls.test_data_list[1].data}'"):
                db.query(f"DELETE FROM test_vpn_configs WHERE data = \
                  '{cls.test_data_list[1].data}'")


class GetConfigTestCase(BasicGetConfig):
    """
    Functional test cases for Configstore
    """

    def get_config(self, test_data=None, data_json=None):
        """
        Send request to the service and receive response
        """
        if test_data:
            data_json = json.dumps({"Type": test_data.type,
                                    "Data": test_data.data})
        response = requests.post(SERVICE_URL, data=data_json)
        return json.loads(response.text)

    def assert_config_develop(self, received_config, expected_config):
        for field in ['Data', 'Host', 'Port', 'Database', 'User', 'Password',
                      'Schema']:
            self.assertEqual(received_config[field],
                             getattr(expected_config, field.lower()),
                             INCORRECT_DATA)

    def assert_config_test(self, received_config, expected_config):
        for field in ['Data', 'Host', 'Port', 'Virtualhost', 'User',
                      'Password']:
            self.assertEqual(received_config[field],
                             getattr(expected_config, field.lower()),
                             INCORRECT_DATA)

    def get_and_assert_config(self, test_data, error=None):
        """
        Basic test case: send request, receive and assert result
        """
        config = self.get_config(test_data)
        if error:
            self.assertEqual(config, error, "Incorrect error")
        else:
            if isinstance(test_data, self.TestDataDevelop):
                self.assert_config_develop(config, test_data)
            elif isinstance(test_data, self.TestDataTest):
                self.assert_config_test(config, test_data)
            else:
                self.fail('Unknown type of test data')

    def test_success(self):
        for test_data in self.test_data_list:
            self.get_and_assert_config(test_data)

    def test_nonexistent_data(self):
        for test_data in self.test_data_list:
            td = copy.deepcopy(test_data)
            td.data = test_data.data + "incorrect_suffix"
            self.get_and_assert_config(td, error=RECORD_NOT_FOUND)

    def test_nonexistent_type(self):
        for test_data in self.test_data_list:
            td = copy.deepcopy(test_data)
            td.type = test_data.type + "incorrect_suffix"
            self.get_and_assert_config(td, error=MODEL_NOT_PRESENT)

    def test_nonexistent_type_and_data(self):
        for test_data in self.test_data_list:
            td = copy.deepcopy(test_data)
            td.type = test_data.type + "incorrect_suffix_type"
            td.data = test_data.data + "incorrect_suffix_data"
            self.get_and_assert_config(td, error=MODEL_NOT_PRESENT)

    def test_without_data(self):
        for test_data in self.test_data_list:
            response = self.get_config(
                data_json=json.dumps({"Type": test_data.type}))
            self.assertEqual(response, RECORD_NOT_FOUND, "Incorrect error")
            response = self.get_config(data_json=json.dumps(
                {"Type": test_data.type + "incorrect suffix"}))
            self.assertEqual(response, MODEL_NOT_PRESENT, "Incorrect error")

    def test_without_type(self):
        for test_data in self.test_data_list:
            response = self.get_config(
                data_json=json.dumps({"Data": test_data.data}))
            self.assertEqual(response, MODEL_NOT_PRESENT, "Incorrect error")
            response = self.get_config(data_json=json.dumps(
                {"Data": test_data.data + "incorrect suffix"}))
            self.assertEqual(response, MODEL_NOT_PRESENT, "Incorrect error")

    def test_format_type(self):
        for test_data in self.test_data_list:
            for type in ["", None, "!@#$%^&*()\"<>/.,"]:
                td = copy.deepcopy(test_data)
                td.type = type
                self.get_and_assert_config(td, error=MODEL_NOT_PRESENT)
            td.type = 1111
            self.get_and_assert_config(td, error=BAD_INPUT)

    def test_format_data(self):
        for test_data in self.test_data_list:
            for data in ["", None, "!@#$%^&*()\"<>/.,"]:
                td = copy.deepcopy(test_data)
                td.data = data
                self.get_and_assert_config(td, error=RECORD_NOT_FOUND)
            td.data = 1111
            self.get_and_assert_config(td, error=BAD_INPUT)

    def test_empty_request(self):
        data_json = json.dumps({})
        response = requests.post(SERVICE_URL, data=data_json)
        self.assertEqual(json.loads(response.text), MODEL_NOT_PRESENT,
                         "Incorrect error")

    # TODO: Unskip when defect will be fixed
    @unittest.skip("Waiting for fix of defect")
    def test_child_type(self):
        data_json = json.dumps({"Type": "child",
                                "Data": "existentSample"})
        response = requests.post(SERVICE_URL, data=data_json)
        self.assertEqual(json.loads(response.text), MODEL_NOT_PRESENT,
                         "Incorrect error")

    def test_only_nonexistent_field(self):
        data_json = json.dumps({"Type_new": "Develop.mr_robot"})
        response = requests.post(SERVICE_URL, data=data_json)
        self.assertEqual(json.loads(response.text), MODEL_NOT_PRESENT,
                         "Incorrect error")

    # TODO: Update and unskip test when defect will be fixed
    @unittest.skip("Service should send some error about unknown fields")
    def test_nonexistent_field(self):
        for test_data in self.test_data_list:
            data_json = json.dumps({"Type": test_data.type,
                                    "Data": test_data.data,
                                    "Type_new": "Develop.mr_robot"})
            response = requests.post(SERVICE_URL, data=data_json)
            # self.assertEqual(json.loads(response.text), ***SOME_ERROR***, "Incorrect error")

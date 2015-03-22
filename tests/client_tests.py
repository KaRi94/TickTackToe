from unittest import TestCase, mock
from client.client import Interface, Client


class ClientTest(TestCase):
    def setUp(self):
        self.client = Client('127.0.0.1', 11111)

    def test_object_initialize(self):
        self.assertEqual('127.0.0.1', self.client.server)
        self.assertEqual(11111, self.client.port)
        self.assertTrue(isinstance(self.client.interface, Interface))


class ConnectionTest(TestCase):
    pass


class InterfaceTest(TestCase):
    pass
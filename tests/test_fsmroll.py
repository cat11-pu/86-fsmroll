import json
import threading
import unittest
import urllib.error
import urllib.request

from fsmroll import Machine
from server import serve

class TestMachine(unittest.TestCase):
    def test_fire_changes_state(self):
        machine = Machine()
        self.assertEqual(machine.fire("run")["state"], "run")

    def test_version_default(self):
        self.assertEqual(Machine().stats()["version"], 1)

    def test_history_records(self):
        machine = Machine()
        machine.fire("a")
        self.assertEqual(machine.stats()["history"], ["a"])

    def test_stats_shape(self):
        self.assertIn("migrations", Machine().stats())

    def test_http_fire(self):
        server = serve(0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:%d" % server.server_port
        with urllib.request.urlopen(base + "/fire", data=b'{"event": "run"}', timeout=5) as response:
            self.assertEqual(json.loads(response.read())["state"], "run")
        server.shutdown()

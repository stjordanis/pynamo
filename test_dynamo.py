#!/usr/bin/env python
"""Test code for Dynamo"""
import sys
import random
import unittest

from framework import Framework, reset
from history import History

import dynamomessages
import dynamo1
import dynamo2
import dynamo3
import dynamo4
import dynamo as dynamo99


class SimpleTestCase(unittest.TestCase):
    """Test simple Dynamo function"""
    def setUp(self):
        reset()

    def tearDown(self):
        reset()

    def test_simple_put(self):
        for _ in range(6):
            dynamo1.DynamoNode()
        a = dynamo1.DynamoClientNode('a')
        a.put('K1', None, 1)
        Framework.schedule()
        print History.ladder()

    def test_simple_get(self):
        for _ in range(6):
            dynamo1.DynamoNode()
        a = dynamo1.DynamoClientNode('a')
        a.put('K1', None, 1)
        Framework.schedule()
        from_line = len(History.history)
        a.get('K1')
        Framework.schedule()
        print History.ladder(start_line=from_line)

    def test_double_put(self):
        for _ in range(6):
            dynamo1.DynamoNode()
        a = dynamo1.DynamoClientNode('a')
        b = dynamo1.DynamoClientNode('b')
        a.put('K1', None, 1)
        Framework.schedule(1)
        b.put('K2', None, 17)
        Framework.schedule()
        print History.ladder(spacing=14)

    def test_put1_fail_initial_node(self):
        self.put_fail_initial_node(dynamo1)

    def test_put2_fail_initial_node(self):
        self.put_fail_initial_node(dynamo2)

    def put_fail_initial_node(self, cls):
        for _ in range(6):
            cls.DynamoNode()
        a = cls.DynamoClientNode('a')
        destnode = random.choice(cls.DynamoNode.nodelist)
        a.put('K1', None, 1, destnode=destnode)
        # Fail at the forwarding node before it gets a chance to forward
        destnode.fail()
        Framework.schedule()
        print History.ladder()

    def test_put1_fail_initial_node2(self):
        self.put_fail_initial_node2(dynamo1)

    def test_put2_fail_initial_node2(self):
        self.put_fail_initial_node2(dynamo2)

    def put_fail_initial_node2(self, cls):
        for _ in range(6):
            dynamo1.DynamoNode()
        a = dynamo1.DynamoClientNode('a')
        destnode = random.choice(dynamo1.DynamoNode.nodelist)
        a.put('K1', None, 1, destnode=destnode)
        # Fail at the forwarding node after it gets a chance to forward
        Framework.schedule(1)
        destnode.fail()
        Framework.schedule()
        print History.ladder()

    def test_put1_fail_node2(self):
        self.put_fail_node2(dynamo1)

    def test_put2_fail_node2(self):
        self.put_fail_node2(dynamo2)

    def put_fail_node2(self, cls):
        for _ in range(6):
            cls.DynamoNode()
        a = cls.DynamoClientNode('a')
        a.put('K1', None, 1)
        # Fail the second node in the preference list
        pref_list = cls.DynamoNode.chash.find_nodes('K1', 3)[0]
        Framework.schedule(1)
        pref_list[1].fail()
        Framework.schedule()
        a.get('K1')
        Framework.schedule()
        print History.ladder()

    def test_put1_fail_nodes23(self):
        self.put_fail_nodes23(dynamo1)
        print History.ladder(spacing=16)

    def test_put2_fail_nodes23(self):
        (_, pref_list) = self.put_fail_nodes23(dynamo2)
        # Force nodes that are of interest in put2_fail_nodes23_[234] to be included in the history
        print History.ladder(force_include=pref_list, spacing=16)

    def put_fail_nodes23(self, cls):
        # Set up 6 nodes and 1 client node
        for _ in range(6):
            cls.DynamoNode()
        a = cls.DynamoClientNode('a')
        # Fail the second and third node in the preference list
        pref_list = cls.DynamoNode.chash.find_nodes('K1', 5)[0]
        a.put('K1', None, 1, destnode=pref_list[0])
        Framework.schedule(1)
        pref_list[1].fail()
        pref_list[2].fail()
        Framework.schedule(timers_to_process=2)
        return a, pref_list

    def test_put2_fail_nodes23_2(self):
        """Show second request for same key skipping failed nodes"""
        (a, pref_list) = self.put_fail_nodes23(dynamo2)
        coordinator = pref_list[0]
        from_line = len(History.history)
        a.put('K1', None, 2, destnode=coordinator)  # Send client request to coordinator for clarity
        Framework.schedule()
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)

    def test_put2_fail_nodes23_3(self):
        """Show PingReq failing"""
        (a, pref_list) = self.put_fail_nodes23(dynamo99)
        coordinator = pref_list[0]
        a.put('K1', None, 2, destnode=coordinator)  # Send client request to coordinator for clarity
        Framework.schedule(timers_to_process=0)
        from_line = len(History.history)
        Framework.schedule(timers_to_process=3)
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)

    def test_put2_fail_nodes23_4a(self):
        """Show PingReq recovering but an inconsistent Get being returned"""
        (a, pref_list) = self.put_fail_nodes23(dynamo3)
        coordinator = pref_list[0]
        a.put('K1', None, 2, destnode=coordinator)  # Send client request to coordinator for clarity
        Framework.schedule(timers_to_process=10)
        from_line = len(History.history)
        pref_list[1].recover()
        pref_list[2].recover()
        Framework.schedule(timers_to_process=10)
        a.get('K1', destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)

    def test_put2_fail_nodes23_4b(self):
        """Show PingReq recovering, and a subsequent Put returning to the original preference list"""
        (a, pref_list) = self.put_fail_nodes23(dynamo3)
        coordinator = pref_list[0]
        a.put('K1', None, 2, destnode=coordinator)  # Send client request to coordinator for clarity
        Framework.schedule(timers_to_process=10)
        from_line = len(History.history)
        pref_list[1].recover()
        pref_list[2].recover()
        Framework.schedule(timers_to_process=15)
        a.put('K1', None, 3, destnode=coordinator)
        Framework.schedule(timers_to_process=5)
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)

    def test_put2_fail_nodes23_5(self):
        """Show Put after a failure including handoff, and the resulting Pings"""
        (a, pref_list) = self.put_fail_nodes23(dynamo4)
        coordinator = pref_list[0]
        from_line = len(History.history)
        a.put('K1', None, 2, destnode=coordinator)  # Send client request to coordinator for clarity
        Framework.schedule(timers_to_process=10)
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)

    def test_put2_fail_nodes23_6(self):
        """Show hinted handoff after recovery"""
        (a, pref_list) = self.put_fail_nodes23(dynamo4)
        coordinator = pref_list[0]
        a.put('K1', None, 2, destnode=coordinator)  # Send client request to coordinator for clarity
        Framework.schedule(timers_to_process=10)
        from_line = len(History.history)
        pref_list[1].recover()
        pref_list[2].recover()
        Framework.schedule(timers_to_process=15)
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)

    def get_put_get_put(self):
        cls = dynamo99
        for _ in range(6):
            cls.DynamoNode()
        a = cls.DynamoClientNode('a')
        pref_list = cls.DynamoNode.chash.find_nodes('K1', 5)[0]
        coordinator = pref_list[0]
        # Send in first get-then-put
        a.get('K1', destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        getrsp = a.last_msg
        a.put('K1', getrsp.metadata, 1, destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        # Send in second get-then-put
        a.get('K1', destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        getrsp = a.last_msg
        a.put('K1', getrsp.metadata, 2, destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        return (a, pref_list)

    def test_get_put_get_put(self):
        """Show 2 x get-then-put operation"""
        (a, pref_list) = self.get_put_get_put()
        dynamomessages._show_metadata = True
        print History.ladder(force_include=pref_list, spacing=16)
        dynamomessages._show_metadata = False

    def get_put_put(self, a, coordinator):
        # Send in a get-then-put-put
        a.get('K1', destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        getrsp = a.last_msg
        a.put('K1', getrsp.metadata, 3, destnode=coordinator)
        Framework.schedule(timers_to_process=0)
        metadata = [a.last_msg.metadata]  # PutRsp has a single VectorClock
        a.put('K1', metadata, 4, destnode=coordinator)
        Framework.schedule(timers_to_process=0)

    def test_get_put_put(self):
        """Show get-then-put-then-put operation"""
        (a, pref_list) = self.get_put_get_put()
        coordinator = pref_list[0]
        from_line = len(History.history)
        self.get_put_put(a, coordinator)
        dynamomessages._show_metadata = True
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)
        dynamomessages._show_metadata = False

    def test_metadata_simple_fail(self):
        """Show a vector clock not mattering on simple failures"""
        (a, pref_list) = self.get_put_get_put()
        coordinator = pref_list[0]
        self.get_put_put(a, coordinator)
        from_line = len(History.history)
        metadata = [a.last_msg.metadata]  # PutRsp has a single VectorClock
        # Fail the coordinator
        coordinator.fail()
        # Send in another put
        a.put('K1', metadata, 11, destnode=pref_list[1])
        Framework.schedule(timers_to_process=0)
        # Send in a get
        a.get('K1', destnode=pref_list[1])
        Framework.schedule(timers_to_process=0)
        dynamomessages._show_metadata = True
        print History.ladder(force_include=pref_list, start_line=from_line, spacing=16)
        dynamomessages._show_metadata = False
        
if __name__ == "__main__":
    for ii in range(1, len(sys.argv) - 1):  # pragma: no cover
        arg = sys.argv[ii]
        if arg == "-s" or arg == "--seed":
            random.seed(sys.argv[ii + 1])
            del sys.argv[ii:ii + 2]
            break
    unittest.main()

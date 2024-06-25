from flask import Flask, request
import ed25519
import share
import sign
import pickle



class CBC:
    def __init__(self, name, cluster_addr_with_ports, conn_pool, node_num, quorum_num, private_key, ts_public_key, ts_private_key):
        self.name = name
        self.cluster_addr_with_ports = cluster_addr_with_ports
        self.conn_pool = conn_pool
        self.node_num = node_num
        self.quorum_num = quorum_num
        self.pending_blocks = {}
        self.pending_vote = {}
        self.pending_ready = {}
        self.private_key = private_key
        self.ts_public_key = ts_public_key
        self.ts_private_key = ts_private_key
        self.lock = threading.RLock()
        self.block_ch = queue.Queue()
        self.done_ch = queue.Queue()
        self.block_output = {}
        self.done_output = {}
        self.block_send = {}
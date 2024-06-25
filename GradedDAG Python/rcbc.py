import sign
import pickle
import data_struct
import threading
import queue


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
        
    def return_block_chan(self):
        return self.block_ch
    def return_done_chan(self):
        return self.done_ch

    def handle_block_msg(self, block):
        self.lock.acquire()
        self.store_block_msg(block)
        self.lock.release()
        self.broadcast_vote(block.sender, block.round)
        self.check_if_quorum_vote(block.round, block.sender)

    def handle_vote_msg(self, vote):
        self.lock.acquire()
        self.store_vote_msg(vote)
        self.lock.release()
        self.check_if_quorum_vote(vote.round, vote.block_sender)

    def handle_ready_msg(self, ready):
        self.lock.acquire()
        self.store_ready_msg(ready)
        self.lock.release()
        self.check_if_quorum_ready(ready)
    def store_block_msg(self, block):
        if block.round not in self.pending_blocks:
            self.pending_blocks[block.round] = {}
        self.pending_blocks[block.round][block.sender] = block

    def store_vote_msg(self, vote):
        if vote.round not in self.pending_vote:
            self.pending_vote[vote.round] = {}
        if vote.block_sender not in self.pending_vote[vote.round]:
            self.pending_vote[vote.round][vote.block_sender] = 0
        self.pending_vote[vote.round][vote.block_sender] += 1

    def store_ready_msg(self, ready):
        if ready.round not in self.pending_ready:
            self.pending_ready[ready.round] = {}
        if ready.block_sender not in self.pending_ready[ready.round]:
            self.pending_ready[ready.round][ready.block_sender] = {}
        self.pending_ready[ready.round][ready.block_sender][ready.ready_sender] = ready.partial_sig
    def check_if_quorum_vote(self, round, block_sender):
        vote_count = self.pending_vote[round][block_sender]
        if vote_count >= self.quorum_num:
            self.try_to_output_blocks(round, block_sender)

    def check_if_quorum_ready(self, ready):
        readies = self.pending_ready[ready.round][ready.block_sender]
        if len(readies) >= self.quorum_num and (ready.round, ready.block_sender) not in self.done_output:
            partial_sig = [readies[sender] for sender in readies]
            done = Done(self.name, ready.block_sender, partial_sig, ready.hash, ready.round)
            self.done_ch.put(done)
            self.done_output[(ready.round, ready.block_sender)] = True

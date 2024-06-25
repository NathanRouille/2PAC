class Node:
    def __init__(self, id : int, host : str, port : int, peers : tuple,leader : int, publickey, privatekey):
        self.id = id
        self.host = host
        self.port = port
        self.peers = peers
        self.leader = leader
        self.publickey = publickey
        self.privatekey = privatekey


class Block:
    def __init__(self, sender):
        self.sender = sender

class Vote:
    def __init__(self, vote_sender, block_sender):
        self.vote_sender = vote_sender
        self.block_sender = block_sender
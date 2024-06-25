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

class Block1(Block):
    def __init__(self, sender, block):
        super().__init__(sender)
        self.block = block

class Block2(Block):
    def __init__(self, sender, block, qc):
        super().__init__(sender)
        self.block = block
        self.qc = qc

class Vote:
    def __init__(self, vote_sender):
        self.vote_sender = vote_sender

class Vote1(Vote):
    def __init__(self, vote_sender, block_sender):
        super().__init__(vote_sender)
        self.block_sender = block_sender

class Vote2(Vote):
    def __init__(self, vote_sender, qc_sender):
        super().__init__(vote_sender)
        self.qc_sender = qc_sender
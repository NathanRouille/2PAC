import json


class Block:
    def __init__(self, sender):
        self.sender = sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender
        })

class Block1(Block):
    def __init__(self, sender, block):
        super().__init__(sender)
        self.block = block

    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'Block': self.block
        })


class Block2(Block):
    def __init__(self, sender, block, qc):
        super().__init__(sender)
        self.block = block
        self.qc = qc
    
    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'Block': self.block,
            'QC': self.qc
        })

class Vote:
    def __init__(self, vote_sender):
        self.vote_sender = vote_sender

    def to_json(self):
        return json.dumps({
            'sender': self.vote_sender
        })


class Vote1(Vote):
    def __init__(self, vote_sender, block_sender):
        super().__init__(vote_sender)
        self.block_sender = block_sender

    def to_json(self):
        return json.dumps({
            'sender': self.vote_sender,
            'Block_sender': self.block_sender
        })

class Vote2(Vote):
    def __init__(self, vote_sender, qc_sender):
        super().__init__(vote_sender)
        self.qc_sender = qc_sender

    def to_json(self):
        return json.dumps({
            'sender': self.vote_sender,
            'qc_sender': self.qc_sender
        })
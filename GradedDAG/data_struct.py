import json


class Block:
    def __init__(self, sender):
        self.sender = sender
        #on abstrait les tx en supposant que la pool est inépuisable et qu'on peut toujours remplir la data du block avec des tx

    def to_json(self):
        return json.dumps({
            'sender': self.sender
        })


class Vote:
    def __init__(self, vote_sender):
        self.sender = vote_sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender
        })


class Echo(Vote):
    def __init__(self, vote_sender, block_sender):
        super().__init__(vote_sender)
        self.block_sender = block_sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'Block_sender': self.block_sender
        })

class Ready(Vote):
    def __init__(self, vote_sender, block_sender):
        super().__init__(vote_sender)
        self.block_sender = block_sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'qc_sender': self.block_sender
        })
    
class Elect:
    def __init__(self, sender):
        self.sender = sender
        #on abstrait data = qcCoinshare

class Leader:
    def __init__(self, sender,id_leader):
        self.sender = sender
        self.id_leader = id_leader
        #on pourrait rajouter block1 qc1 et qc2 du leader si on les a pour accélerer les commit
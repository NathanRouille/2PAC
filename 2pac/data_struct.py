import json


class Block:
    def __init__(self, sender):
        self.sender = sender
        #on abstrait les tx en supposant que la pool est inépuisable et qu'on peut toujours remplir la data du block avec des tx

    def to_json(self):
        return json.dumps({
            'sender': self.sender
        })

class Block1(Block):
    def __init__(self, sender):
        super().__init__(sender)

    def to_json(self):
        return json.dumps({
            'sender': self.sender
        })


class Block2(Block):
    def __init__(self, sender, qc):
        super().__init__(sender)
        self.qc = qc #qc peut valoir None, comme on est que sur une seule view on considère toujours que le Block2 d'un replica extend le Block1 de ce même replica
    
    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'QC': self.qc
        })

class Vote:
    def __init__(self, vote_sender):
        self.sender = vote_sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender
        })


class Vote1(Vote):
    def __init__(self, vote_sender, block_sender):
        super().__init__(vote_sender)
        self.block_sender = block_sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'Block_sender': self.block_sender
        })

class Vote2(Vote):
    def __init__(self, vote_sender, qc_sender):
        super().__init__(vote_sender)
        self.qc_sender = qc_sender

    def to_json(self):
        return json.dumps({
            'sender': self.sender,
            'qc_sender': self.qc_sender
        })
    
class Elect:
    def __init__(self, sender):
        self.sender = sender
        #on abstrait data = qcCoinshare

class Leader:
    def __init__(self, sender,id_leader):
        self.sender = sender
        self.id_leader = id_leader
        #on pouurrat rajouter block1 qc1 et qc2 du leader si on les a 
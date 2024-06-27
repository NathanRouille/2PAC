class Block:
    def __init__(self, sender, round, previous_hash, txs, timestamp):
        """
        Initialise un bloc.

        :param sender: Le nom de l'expéditeur du bloc.
        :param round: Le numéro du round auquel appartient le bloc.
        :param previous_hash: Dictionnaire mappant les expéditeurs aux hashs des blocs précédents.
        :param txs: Liste de transactions (chaque transaction est de type bytes).
        :param timestamp: L'horodatage du bloc.
        """
        self.sender = sender
        self.round = round
        self.previous_hash = previous_hash  # dictionnaire de l'expéditeur au hash (bytes)
        self.txs = txs  # liste de transactions (chaque transaction est de type bytes)
        self.timestamp = timestamp

    def __repr__(self):
        """
        Représentation lisible du bloc.
        """
        return (f"Block(sender={self.sender}, round={self.round}, previous_hash={self.previous_hash}, "
                f"txs={self.txs}, timestamp={self.timestamp})")


class Chain:
    def __init__(self, round):
        """
        Initialise une chaîne.

        :param round: Le round maximum du leader qui est engagé.
        """
        self.round = round  # le round maximum du leader qui est engagé
        self.blocks = {}  # dictionnaire mappant le hash au bloc

    def __repr__(self):
        """
        Représentation lisible de la chaîne.
        """
        return f"Chain(round={self.round}, blocks={self.blocks})"


class Vote:
    def __init__(self, vote_sender, block_sender, round):
        """
        Initialise un vote pour un bloc.

        :param vote_sender: Le nom de l'expéditeur du vote.
        :param block_sender: Le nom de l'expéditeur du bloc.
        :param round: Le numéro du round auquel le vote appartient.
        """
        self.vote_sender = vote_sender
        self.block_sender = block_sender
        self.round = round

    def __repr__(self):
        """
        Représentation lisible du vote.
        """
        return (f"Vote(vote_sender={self.vote_sender}, block_sender={self.block_sender}, "
                f"round={self.round})")


class Ready:
    def __init__(self, ready_sender, block_sender, round, hash, partial_sig):
        """
        Initialise un message Ready pour les blocs de sortie de CBC dans les rounds % 2 == 1.

        :param ready_sender: Le nom de l'expéditeur du message Ready.
        :param block_sender: Le nom de l'expéditeur du bloc.
        :param round: Le numéro du round auquel le message Ready appartient.
        :param hash: Le hash du bloc (bytes).
        :param partial_sig: La signature partielle (bytes).
        """
        self.ready_sender = ready_sender
        self.block_sender = block_sender
        self.round = round
        self.hash = hash  # le hash du bloc (bytes)
        self.partial_sig = partial_sig  # la signature partielle (bytes)

    def __repr__(self):
        """
        Représentation lisible du message Ready.
        """
        return (f"Ready(ready_sender={self.ready_sender}, block_sender={self.block_sender}, "
                f"round={self.round}, hash={self.hash}, partial_sig={self.partial_sig})")


class Done:
    def __init__(self, done_sender, block_sender, done, hash, round):
        """
        Initialise un message Done.

        :param done_sender: Le nom de l'expéditeur du message Done.
        :param block_sender: Le nom de l'expéditeur du bloc correspondant au message Done.
        :param done: Liste de bytes.
        :param hash: Le hash du bloc (bytes).
        :param round: Le numéro du round auquel le message Done appartient.
        """
        self.done_sender = done_sender
        self.block_sender = block_sender
        self.done = done  # liste de bytes
        self.hash = hash  # bytes
        self.round = round

    def __repr__(self):
        """
        Représentation lisible du message Done.
        """
        return (f"Done(done_sender={self.done_sender}, block_sender={self.block_sender}, "
                f"done={self.done}, hash={self.hash}, round={self.round})")


class Elect:
    def __init__(self, sender, round, partial_sig):
        """
        Initialise un message Elect pour élire un leader.

        :param sender: Le nom de l'expéditeur du message Elect.
        :param round: Le numéro du round auquel le message Elect appartient.
        :param partial_sig: La signature partielle (bytes).
        """
        self.sender = sender
        self.round = round
        self.partial_sig = partial_sig  # bytes

    def __repr__(self):
        """
        Représentation lisible du message Elect.
        """
        return (f"Elect(sender={self.sender}, round={self.round}, "
                f"partial_sig={self.partial_sig})")

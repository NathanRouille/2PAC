import ed25519
import math
import threading
import time
from config import Config
from conn import NetworkTransport
from sign import VerifySignEd25519, AssembleIntactTSPartial
from block import Block, encode  # Assumed imports
from chain import Chain
from done import Done
from elect import Elect
from cbc import CBCer

class Node:
    def __init__(self, conf: Config):
        self.name = conf.name
        self.lock = threading.RLock()
        self.dag = {}
        self.pendingBlocks = {}
        self.chain = Chain()
        self.leader = {}
        self.done = {}
        self.elect = {}
        self.round = 1
        self.moveRound = {}
        self.logger = conf.logger

        self.nodeNum = len(conf.clusterAddr)
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)

        self.clusterAddr = conf.clusterAddr
        self.clusterPort = conf.clusterPort
        self.clusterAddrWithPorts = conf.clusterAddrWithPorts
        self.isFaulty = conf.isFaulty

        self.maxPool = conf.maxPool
        self.trans = NetworkTransport()
        self.batchSize = conf.batchSize
        self.roundNumber = conf.round

        # Used for ED25519 signature
        self.publicKeyMap = conf.publicKeyMap
        self.privateKey = conf.privateKey

        # Used for threshold signature
        self.tsPublicKey = conf.tsPublicKey
        self.tsPrivateKey = conf.tsPrivateKey

        self.reflectedTypesMap = conf.reflectedTypesMap

        self.nextRound = threading.Event()
        self.leaderElect = {}

        self.evaluation = []
        self.commitTime = []
        self.cbc = None



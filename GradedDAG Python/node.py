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


    def RunLoop(self):
        currentRound = 1
        start = time.time_ns()
        while currentRound <= self.roundNumber:
            self.broadcastBlock(currentRound)
            if currentRound % 2 == 0:
                self.broadcastElect(currentRound)
            self.nextRound.wait()
            currentRound = self.nextRound_round

        # wait all blocks are committed
        time.sleep(5)

        with self.lock:
            end = self.commitTime[-1]
            pastTime = (end - start) / 1e9
            blockNum = len(self.evaluation)
            throughPut = (blockNum * self.batchSize) / pastTime
            totalTime = sum(self.evaluation)
            latency = (totalTime / 1e9) / blockNum

        self.logger.info("the average", latency=latency, throughput=throughPut)
        self.logger.info("the total commit", block_number=blockNum, time=pastTime)

    def InitCBC(self, conf: Config):
        self.cbc = CBCer(self.name, conf.clusterAddrWithPorts, self.trans, self.quorumNum, self.nodeNum, self.privateKey, self.tsPublicKey, self.tsPrivateKey)

    def selectPreviousBlocks(self, round):
        with self.lock:
            previousHash = {}
            if round == 0:
                return None
            for sender, block in self.dag.get(round, {}).items():
                hash = block.get_hash()
                previousHash[sender] = hash
        return previousHash

    def storeDone(self, done: Done):
        if done.Round not in self.done:
            self.done[done.Round] = {}
        if done.BlockSender not in self.done[done.Round]:
            self.done[done.Round][done.BlockSender] = done
            self.moveRound[done.Round] = self.moveRound.get(done.Round, 0) + 1

    def storeElectMsg(self, elect: Elect):
        if elect.Round not in self.elect:
            self.elect[elect.Round] = {}
        self.elect[elect.Round][elect.Sender] = elect.PartialSig

    
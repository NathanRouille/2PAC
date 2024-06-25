##############         IMPORTS         ##############
#####################################################
# Importer les bibliothèques nécessaires
import math
import threading
import time

#Importer d'autres fichier
from config import Config
from network import NetworkTransport
from sign import *
from data_struct import Block, Chain,Done,Elect  
from tools import encode
from rcbc import *

##############         CLASSES         ##############
#####################################################
class Node:
    def __init__(self, conf: Config):
        self.name = conf.name
        self.lock = threading.RLock()
        self.dag = {}
        self.pendingBlocks = {}
        self.chain = Chain(1)  #round =1
        self.leader = {}
        self.done = {}
        self.elect = {}
        self.round = 1
        self.moveRound = {}
        #self.logger = conf.logger

        self.nodeNum = len(conf.clusterAddr)
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)

        self.clusterAddr = conf.clusterAddr
        self.clusterPort = conf.clusterPort
        self.clusterAddrWithPorts = conf.clusterAddrWithPorts
        self.IsFaulty = conf.IsFaulty

        self.MaxPool = conf.MaxPool
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


#############         FUNCTIONS         #############
#####################################################
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
        self.cbc = CBC(self.name, conf.clusterAddrWithPorts, self.trans, self.quorumNum, self.nodeNum, self.privateKey, self.tsPublicKey, self.tsPrivateKey)

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

    def storePendingBlocks(self, block: Block):
        if block.Round not in self.pendingBlocks:
            self.pendingBlocks[block.Round] = {}
        self.pendingBlocks[block.Round][block.Sender] = block

    def tryToUpdateDAG(self, block: Block):
        with self.lock:
            if self.checkWhetherCanAddToDAG(block):
                if block.Round not in self.dag:
                    self.dag[block.Round] = {}
                self.dag[block.Round][block.Sender] = block
                if block.Round % 2 == 0:
                    self.moveRound[block.Round] = self.moveRound.get(block.Round, 0) + 1
                    self.tryToNextRound(block.Round)
                else:
                    self.tryToCommitLeader(block.Round)
                self.tryToUpdateDAGFromPending(block.Round + 1)
            else:
                self.storePendingBlocks(block)

    def tryToUpdateDAGFromPending(self, round):
        with self.lock:
            if round not in self.pendingBlocks:
                return
            for sender, block in self.pendingBlocks[round].items():
                del self.pendingBlocks[round][sender]
                self.tryToUpdateDAG(block)

    def checkWhetherCanAddToDAG(self, block: Block):
        linkHash = block.PreviousHash
        for sender in linkHash:
            if sender not in self.dag.get(block.Round - 1, {}):
                return False
        return True

    def tryToElectLeader(self, round):
        elect = self.elect.get(round, {})
        if len(elect) >= self.quorumNum and not self.leaderElect.get(round, False):
            self.leaderElect[round] = True
            partialSig = [sig for sig in elect.values()]
            data = encode(round)
            qc = AssembleIntactTSPartial(partialSig, self.tsPublicKey, data, self.quorumNum, self.nodeNum)
            qcAsInt = int.from_bytes(qc, byteorder='big')
            leader_id = qcAsInt % self.nodeNum
            leader_name = f"node{leader_id}"
            self.leader[round - 1] = leader_name
            self.tryToCommitLeader(round - 1)

    def tryToNextRound(self, round):
        with self.lock:
            if round != self.round:
                return
            count = self.moveRound.get(round, 0)
            if count >= self.quorumNum:
                self.round += 1
                self.nextRound_round = round + 1
                self.nextRound.set()
                self.tryToNextRound(round + 1)

    def tryToCommitLeader(self, round):
        if round <= self.chain.round:
            return
        leader = self.leader.get(round)
        if leader and leader in self.done.get(round, {}) and leader in self.dag.get(round, {}):
            self.tryToCommitAncestorLeader(round)
            block = self.dag[round][leader]
            hash = block.get_hash_as_string()
            self.chain.round = round
            self.chain.blocks[hash] = block
            self.logger.info("commit the leader block", node=self.name, round=round, block_proposer=block.Sender)
            commit_time = time.time_ns()
            latency = commit_time - block.TimeStamp
            self.evaluation.append(latency)
            self.commitAncestorBlocks(round)
            self.commitTime.append(commit_time)

    def tryToCommitAncestorLeader(self, round):
        if round < 2 or round - 2 <= self.chain.round:
            return
        validLeader = self.findValidLeader(round)
        for i in range(1, round, 2):
            if i in validLeader:
                block = self.dag[i][self.leader[i]]
                hash = block.get_hash_as_string()
                self.chain.round = i
                self.chain.blocks[hash] = block
                self.logger.info("commit the ancestor leader block", node=self.name, round=i, block_proposer=block.Sender)
                commit_time = time.time_ns()
                latency = commit_time - block.TimeStamp
                self.evaluation.append(latency)
                self.commitAncestorBlocks(i)

    def findValidLeader(self, round):
        templeBlocks = {}
        block = self.dag[round][self.leader[round]]
        hash = block.get_hash_as_string()
        templeBlocks[round] = {hash: block}
        validLeader = {}

        r = round
        while r > 0:
            templeBlocks[r - 1] = {}
            for b in templeBlocks[r].values():
                if b.Round % 2 == 1 and b.Sender == self.leader[b.Round]:
                    validLeader[b.Round] = b.Sender
                for sender in b.PreviousHash:
                    linkBlock = self.dag[r - 1][sender]
                    hash = linkBlock.get_hash_as_string()
                    templeBlocks[r - 1][hash] = linkBlock
            r -= 1
            if r == 0 or r == self.chain.round:
                break
        return validLeader

    def commitAncestorBlocks(self, round):
        templeBlocks = {}
        block = self.dag[round][self.leader[round]]
        hash = block.get_hash_as_string()
        templeBlocks[round] = {hash: block}
        r = round
        while r > 0:
            templeBlocks[r - 1] = {}
            for hash, b in templeBlocks[r].items():
                if hash not in self.chain.blocks:
                    self.chain.blocks[hash] = b
                    commit_time = time.time_ns()
                    latency = commit_time - b.TimeStamp
                    self.evaluation.append(latency)
                for sender in b.PreviousHash:
                    linkBlock = self.dag[r - 1][sender]
                    h = linkBlock.get_hash_as_string()
                    if h not in self.chain.blocks:
                        templeBlocks[r - 1][h] = linkBlock
            if not templeBlocks[r - 1]:
                break
            r -= 1

    def NewBlock(self, round, previousHash):
        batch = [generateTX(20) for _ in range(self.batchSize)]
        timestamp = time.time_ns()
        return Block(self.name, round, previousHash, batch, timestamp)

    def verifySigED25519(self, peer, data, sig):
        pubKey = self.publicKeyMap.get(peer)
        if not pubKey:
            self.logger.error("node is unknown", node=peer)
            return False
        dataAsBytes = encode(data)
        valid = Sign.verify_signature(pubKey, sig)
        '''
        if err:
            self.logger.error("fail to verify the ED25519 signature", error=err)
            return False
        '''
        return valid

    def IsFaultyNode(self):
        return self.isFaulty
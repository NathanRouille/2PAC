import math
import threading
import time
import random

#Importer d'autres fichier
from config import Config
from network import NetworkTransport
from sign import *
from data_struct import Block, Chain,Done,Elect  
from tools import encode
from rcbc import *

random.seed(1234)


class Node:
    def __init__(self, conf: Config):
        self.name = conf.name
        self.lock = threading.RLock()
        self.blocks = {}
        self.chain = {}
        self.leader = {}
        self.leaderElected = False
        self.done = {}
        self.elect = {}
        self.qccoin = random.randint(1,5)
        self.moveRound = 0
        #self.logger = conf.logger

        self.nodeNum = 4
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)

        self.clusterAddr = conf.clusterAddr
        self.clusterPort = conf.clusterPort
        self.clusterAddrWithPorts = conf.clusterAddrWithPorts

        # Used for ED25519 signature
        self.publicKeyMap = conf.publicKeyMap
        self.privateKey = conf.privateKey

        # Used for threshold signature
        self.tsPublicKey = conf.tsPublicKey
        self.tsPrivateKey = conf.tsPrivateKey

        self.reflectedTypesMap = conf.reflectedTypesMap

        self.evaluation = []
        self.commitTime = []


#############         FUNCTIONS         #############
#####################################################
    def RunLoop(self):
        #start = time.time_ns()
        self.broadcastBlock(currentRound)
        if currentRound % 2 == 0:
            self.broadcastElect(currentRound)
        self.nextRound.wait()
        currentRound = self.nextRound_round

        # wait all blocks are committed
        time.sleep(5)

        '''with self.lock:
            end = self.commitTime[-1]
            pastTime = (end - start) / 1e9
            blockNum = len(self.evaluation)
            throughPut = (blockNum * self.batchSize) / pastTime
            totalTime = sum(self.evaluation)
            latency = (totalTime / 1e9) / blockNum

        self.logger.info("the average", latency=latency, throughput=throughPut)
        self.logger.info("the total commit", block_number=blockNum, time=pastTime)'''

    def storeDone(self, done: Done):
        if done.BlockSender not in self.done:
            #vérifier signature
            self.done[done.BlockSender] = done
            self.moveRound += 1

    def storeElectMsg(self, elect: Elect):
        #vérifier que signature correspond bien à round et Sender
        self.elect[elect.Sender] = elect.PartialSig


    def tryToUpdateDAG(self, block: Block):
        with self.lock:
            self.blocks[block.Sender] = block
            if block.Round % 2 == 0:
                self.moveRound += 1
                self.tryToNextRound(block.Round)
            else:
                self.tryToCommitLeader(block.Round)


    def tryToElectLeader(self, round):
        if len(self.elect) >= self.quorumNum and not self.leaderElected:
            self.leaderElected = True
            leader_name = f"node{self.qccoin}"
            self.leader[round - 1] = leader_name
            self.tryToCommitLeader(round - 1)

    def tryToNextRound(self, round):
        with self.lock:
            if self.moveRound >= self.quorumNum:
                self.round += 1

    def tryToCommitLeader(self, round):
        if self.leader and self.leader in self.done and self.leader in self.blocks:
            block = self.blocks[self.leader]
            hash = block.get_hash_as_string()
            self.chain[hash] = block
            #self.logger.info("commit the leader block", node=self.name, round=round, block_proposer=block.Sender)
            #commit_time = time.time_ns()
            #latency = commit_time - block.TimeStamp
            #self.evaluation.append(latency)
            #self.commitTime.append(commit_time)

    def NewBlock(self):
        timestamp = time.time_ns()
        return Block(self.name,timestamp)

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
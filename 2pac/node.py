import math
import threading
import time
import random

#Importer d'autres fichier
from sign import verify_signed
from data_struct import Block, Chain,Done,Elect  
from tools import *
from com import *

random.seed(1234)


class Node:
    def __init__(self, id : int, host : str, port : int, peers : list,leader : int, publickey, privatekey, isDelayed: bool):
        self.id = id
        self.host = host
        self.port = port
        self.peers = peers
        self.leader = leader
        self.publickey = publickey
        self.privatekey = privatekey
        self.delay = isDelayed           #A rajouter

        self.lock = threading.RLock()
        self.blocks = {}
        self.chain = {}
        self.leader = {}
        self.leaderElected = False
        self.done = {}
        self.elect = {}
        self.qccoin = random.randint(1, 5)
        self.moveRound = 0
        self.nodeNum = 4
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)
        
        #self.publicKeyMap = conf.publicKeyMap
        #self.privateKey = conf.privateKey
        #self.tsPublicKey = conf.tsPublicKey
        #self.tsPrivateKey = conf.tsPrivateKey
        #self.reflectedTypesMap = conf.reflectedTypesMap
        self.evaluation = []
        self.commitTime = []
        #self.trans = NetworkTransport()
        self.pendingBlocks = {}
        self.pendingVote = {}
        self.pendingReady = {}
        self.blockCh = queue.Queue()
        self.doneCh = queue.Queue()
        self.blockOutput = {}
        self.doneOutput = {}
        self.blockSend = {}

    def handleMsgLoop(self):
        msgCh = self.com.recv
        while True:
            msgWithSig = msgCh.get()
            if not msgWithSig:
                continue
            msgAsserted = msgWithSig["data"]
            msg_type = msgWithSig["type"]
            msg_publickey= msgWithSig["public_key"]
            msg_signature= msgWithSig["signature"]
            if not verify_signed(msg_signature):
                self.logger.error(f"fail to verify the {msg_type.lower()}'s signature", "round", msgAsserted.Round, "sender", msgAsserted.Sender)
                continue
            if msg_type == 'Block1':
                threading.Thread(target=self.handleBlockMsg, args=(msgAsserted,)).start()
            elif msg_type == 'Vote1':
                threading.Thread(target=self.handleVoteMsg, args=(msgAsserted,)).start()
            elif msg_type == 'Block2':
                threading.Thread(target=self.handleReadyMsg, args=(msgAsserted,)).start()
            elif msg_type == 'Vote2':
                threading.Thread(target=self.handleDoneMsg, args=(msgAsserted,)).start()
            elif msg_type == 'Elect':
                threading.Thread(target=self.handleElectMsg, args=(msgAsserted,)).start()
            



    def handleBlockMsg(self, block: Block):
        with self.lock:
            self.storeBlockMsg(block)
        threading.Thread(target=self.broadcastVote, args=(block.sender)).start()
        threading.Thread(target=self.checkIfQuorumVote, args=(block.round, block.sender)).start() #pq on test quorum ? On peut récupérer des signatures ?
        self.tryToCommit()

    def handleVoteMsg(self, vote: Vote): #vérifier signature et 1er vote de ce replica pour ce block
        with self.lock:
            self.storeVoteMsg(vote)
        threading.Thread(target=self.checkIfQuorumVote, args=(vote.round, vote.blockSender)).start()

    def handleReadyMsg(self, ready: Ready):
        with self.lock:
            self.storeReadyMsg(ready)
        threading.Thread(target=self.checkIfQuorumReady, args=(ready)).start()

    def handleDoneMsg(self, done: Done):
        with self.lock:
            self.storeDoneMsg(done)
        threading.Thread(target=self.tryToNextRound).start()
        self.tryToCommit()

    def handleElectMsg(self, elect: Elect):
        with self.lock:
            self.storeElectMsg(elect)
            self.tryToElectLeader(elect.Round)




    def storeBlockMsg(self, block: Block):
        self.blocks[block.Sender] = block

    def storeVoteMsg(self, vote: Vote): #si déjà envoyé block hauteur 2 ne rien faire, vérifier signature vote
        if vote.blockSender not in self.pendingVote:
            self.pendingVote[vote.blockSender] = 0
        self.pendingVote[vote.blockSender] += 1

    def storeReadyMsg(self, ready: Ready): #readySender peut être différent de ready.blockSender ? Sinon enlever if et faire dict 1 dimension
        if ready.blockSender not in self.pendingReady:
            self.pendingReady[ready.blockSender] = {}
        self.pendingReady[ready.blockSender][ready.readySender] = ready.partialSig

    def storeDoneMsg(self, done: Done):
        if done.BlockSender not in self.done:
            self.done[done.BlockSender] = done
            self.moveRound += 1

    def storeElectMsg(self, elect: Elect):
        self.elect[elect.Sender] = elect.PartialSig



    def checkIfQuorumVote(self, round, blockSender):
        if self.pendingVote >= self.quorumNum:
            threading.Thread(target=self.tryToOutputBlocks, args=(round, blockSender)).start()

    def checkIfQuorumReady(self, ready: Ready):
        with self.lock: #est-ce que c'est nécessaire de lock
            if len(self.pendingReady) >= self.quorumNum and not self.doneOutput.get(ready.blockSender, False):
                self.doneOutput[ready.blockSender] = True
                partialSig = [parSig for parSig in self.pendingReady.values()]
        doneMsg = Done(doneSender=self.name, blockSender=ready.blockSender, done=partialSig, hash=ready.hash, round=ready.round)
        self.doneCh.put(doneMsg)


    def tryToOutputBlocks(self, round, sender):
        with self.lock:
            if round not in self.blockOutput:
                self.blockOutput[round] = {}
            if self.blockOutput[round].get(sender, False):
                return
            if sender not in self.pendingBlocks.get(round, {}):
                return
            block = self.pendingBlocks[round][sender]
            self.blockOutput[round][sender] = True
        if block.round % 2 == 1 and not self.blockSend.get(block.round + 1, False):
            hash_val = block.get_hash()
            threading.Thread(target=self.broadcastReady, args=(block.round, hash_val, block.sender)).start()
        self.blockCh.put(block)




    def broadcast(self, msgType, msg):
        msgAsBytes = encode(msg)
        sig = Sign.sign_ed25519(self.privateKey, msgAsBytes)
        for addrWithPort in self.clusterAddrWithPorts:
            netConn = self.connPool.get_conn(addrWithPort)
            conn.send_msg(netConn, msgType, msg, sig)
            self.connPool.return_conn(netConn)

    def broadcastBlock(self, block):
        self.broadcast('ProposalTag', block)
        with self.lock:
            self.blockSend[block.round] = True

    def broadcastVote(self, blockSender):
        vote = Vote(voteSender=self.name, blockSender=blockSender)
        self.broadcast('VoteTag', vote)

    def broadcastReady(self, hash, blockSender):
        partialSig = Sign.sign_ts_partial(self.tsPrivateKey, hash)
        ready = Ready(readySender=self.name, blockSender=blockSender, hash=hash, partialSig=partialSig)
        self.broadcast('ReadyTag', ready)





    def returnBlockChan(self):
        return self.blockCh

    def returnDoneChan(self):
        return self.doneCh
    



    """ def verifySigED25519(self, peer, data, sig):
        pubKey = self.publicKeyMap.get(peer)
        if not pubKey:
            self.logger.error("node is unknown", node=peer)
            return False
        dataAsBytes = encode(data)
        valid = Sign.verify_signature(pubKey, dataAsBytes, sig)
        if not valid:
            self.logger.error("fail to verify the ED25519 signature")
        return valid """

    def RunLoop(self): # à quoi sert RunLoop (quand est-ce que c'est appelé)
        #start = time.time_ns()
        self.broadcastBlock(currentRound)
        if currentRound % 2 == 0: #changer pour qu'une var dise quand on peut send Elect
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
            

    def tryToNextRound(self):
        with self.lock:
            if self.moveRound >= self.quorumNum:
                self.round += 1

    def tryToCommit(self):
        if self.leader and self.leader in self.done and self.leader in self.blocks:
            block = self.blocks[self.leader]
            hash = block.get_hash_as_string()
            self.chain[hash] = block
            #self.logger.info("commit the leader block", node=self.name, round=round, block_proposer=block.Sender)
            #commit_time = time.time_ns()
            #latency = commit_time - block.TimeStamp
            #self.evaluation.append(latency)
            #self.commitTime.append(commit_time)


    def tryToElectLeader(self, round):
        if len(self.elect) >= self.quorumNum and not self.leaderElected:
            self.leaderElected = True
            leader_name = f"node{self.qccoin}"
            self.leader[round - 1] = leader_name
            self.tryToCommitLeader(round - 1)


    def NewBlock(self):
        timestamp = time.time_ns()
        return Block(self.name,timestamp)
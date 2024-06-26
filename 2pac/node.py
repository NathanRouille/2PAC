import math
import threading
import time
import random

#Importer d'autres fichier
from sign import verify_signed, Sign
from data_struct import *  
from tools import *
from com import Com

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
        self.boradcastedBlock1 = False
        self.broadcastedBlock2 = False
        self.broadcastedCoinShare = False

        
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
        self.blockCh = "a changer "  #queue.Queue()
        self.doneCh = "a changer "  #queue.Queue()
        self.blockOutput = {}
        self.doneOutput = {}
        self.blockSend = {}
        self.com=Com(self.port,self.peers)

    def handleMsgLoop(self):
        msgCh = self.com.recv
        print(msgCh)
        while True:
            print("ok2")
            msgWithSig = msgCh.get()
            print(f"Message sign: {msgWithSig}")
            """ if not msgWithSig:
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
                threading.Thread(target=self.handleElectMsg, args=(msgAsserted,)).start() """
            



    def handleBlockMsg(self, block: Block1):
        with self.lock:
            self.storeBlockMsg(block)
        threading.Thread(target=self.broadcastVote, args=(block.sender)).start()
        threading.Thread(target=self.checkIfQuorum, args=(block.round, block.sender)).start() #pq on test quorum ? On peut récupérer des signatures ?
        self.tryToCommit()

    def handleVoteMsg(self, vote: Vote1): #vérifier signature et 1er vote de ce replica pour ce block
        with self.lock:
            self.storeVoteMsg(vote)
        threading.Thread(target=self.checkIfQuorum, args=(vote)).start()

    def handleReadyMsg(self, ready: Block2):
        with self.lock:
            self.storeReadyMsg(ready)
        threading.Thread(target=self.checkIfQuorumReady, args=(ready)).start()

    def handleDoneMsg(self, done: Vote2):
        with self.lock:
            self.storeDoneMsg(done)
        threading.Thread(target=self.tryToNextRound).start()
        self.tryToCommit()

    def handleElectMsg(self, elect: Elect):
        with self.lock:
            self.storeElectMsg(elect)
            self.tryToElectLeader(elect.Round)




    def storeBlockMsg(self, block: Block1):
        self.blocks[block.Sender] = block

    def storeVoteMsg(self, vote: Vote1): #si déjà envoyé block hauteur 2 ne rien faire, vérifier signature vote
        if vote.blockSender not in self.pendingVote:
            self.pendingVote[vote.blockSender] = 0
        self.pendingVote[vote.blockSender] += 1

    def storeReadyMsg(self, ready: Block2): #readySender peut être différent de ready.blockSender ? Sinon enlever if et faire dict 1 dimension
        if ready.blockSender not in self.pendingReady:
            self.pendingReady[ready.blockSender] = {}
        self.pendingReady[ready.blockSender][ready.readySender] = ready.partialSig

    def storeDoneMsg(self, done: Vote2):
        if done.BlockSender not in self.done:
            self.done[done.BlockSender] = done
            self.moveRound += 1

    def storeElectMsg(self, elect: Elect):
        self.elect[elect.Sender] = elect.PartialSig


    def checkIfQuorum(self, msg):
        if type(msg) == Vote1:
            if len(self.pendingVote1) >= self.quorumNum and not self.broadcastedBlock2:
                threading.Thread(target=self.broadcastBlock2).start()

        elif type(msg) == Vote2:
            if len(self.pendingVote2) >= self.quorumNum and not self.broadcastedCoinShare:
                threading.Thread(target=self.broadcastCoinShare).start()

        elif type(msg) == CoinShare:
            if len(self.pendingCoinShare) >= self.quorumNum and not self.ElectedLeader:
                threading.Thread(target=self.tryToElectLeader).start()

    """ def broadcast(self, msgType, msg):
        msgAsBytes = encode(msg)
        sig = Sign.sign_ed25519(self.privateKey, msgAsBytes)
        for addrWithPort in self.clusterAddrWithPorts:
            netConn = self.connPool.get_conn(addrWithPort)
            conn.send_msg(netConn, msgType, msg, sig)
            self.connPool.return_conn(netConn) """

    def broadcastBlock1(self, block):
        message=Block1(self.id,block)
        broadcast(self.com, to_json(message, self),delay = False)
        with self.lock:
            self.boradcastedBlock1 = True


            self.broadcastedBlock2 = True
            self.broadcastedCoinShare = True
            

    """ def broadcastVote(self, blockSender):
        vote = Vote(voteSender=self.name, blockSender=blockSender)
        self.broadcast('VoteTag', vote)

    def broadcastReady(self, hash, blockSender):
        partialSig = Sign.sign_ts_partial(self.tsPrivateKey, hash)
        ready = Block2(readySender=self.name, blockSender=blockSender, hash=hash, partialSig=partialSig)
        self.broadcast('ReadyTag', ready) """


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
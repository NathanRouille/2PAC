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
        self.com=Com(self.id,self.port,self.peers,self.delay)

        self.block1 = []
        self.block2 = []
        self.coinshare = []
        
        self.blocks1 = {}
        self.qc1 = []
        self.blocks2 = {}
        self.qc2 = []
        self.elect = {}
        self.leader = {}
        self.chain = {}
        
        self.moveRound = 0

        self.qccoin = random.randint(1, 5)
        self.nodeNum = 4
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)

        #self.evaluation = []
        #self.commitTime = []
        

        

    def handleMsgLoop(self):
        def handleMsgLoop(self):
        print("handleMsgLoop")
        msgCh = self.com.recv
        while True:
            msgWithSig = msgCh.get()
            msgAsserted = msgWithSig["data"]
            msg_type = msgWithSig["type"]
            msg_publickey= msgWithSig["public_key"]
            msg_signature= msgWithSig["signature"]
            print(f"Verify msg : {verify_signed(msg_signature)}")
            if not verify_signed(msg_signature):
                self.logger.error(f"fail to verify the {msg_type.lower()}'s signature", "round", msgAsserted.Round, "sender", msgAsserted.Sender)
                continue
            print(f"msg_type : {msg_type}")
            print(f"msgAsserted : {msgAsserted}")
            if msg_type == 'Block1':
                block1=Block1(msgAsserted["sender"],msgAsserted["Block"])
                print(type(block1))
                #threading.Thread(target=self.handleBlock1Msg, args=(msgAsserted,)).start()
            """ elif msg_type == 'Vote1':
                threading.Thread(target=self.handleVote1Msg, args=(msgAsserted,)).start()
            elif msg_type == 'Block2':
                threading.Thread(target=self.handleBlock2Msg, args=(msgAsserted,)).start()
            elif msg_type == 'Vote2':
                threading.Thread(target=self.handleVote2Msg, args=(msgAsserted,)).start()
            elif msg_type == 'Elect':
                threading.Thread(target=self.handleElectMsg, args=(msgAsserted,)).start() """
            


    def handleBlock1Msg(self, block1: Block1):
        if block1.sender not in self.blocks1:
            with self.lock:
                self.storeBlock1Msg(block1)
            threading.Thread(target=self.broadcastVote1, args=(block1.sender)).start()
            self.tryToCommit()

    def handleVote1Msg(self, vote1: Vote1):
        if not self.block2 and vote1.sender not in self.qc1 and vote1.Block_sender == self.id:
            with self.lock:
                self.storeVote1Msg(vote1)
            threading.Thread(target=self.checkIfQuorum, args=(vote1)).start()

    def handleBlock2Msg(self, block2: Block2):#vérifier le qc ?
        if block2.sender not in self.blocks2:
            with self.lock:
                self.storeBlock2Msg(block2)
            threading.Thread(target=self.broadcastVote2, args=(block2.sender)).start()
            self.tryToCommit() #est ce qu'on a besoin de commit là

    def handleVote2Msg(self, vote2: Vote2):
        if not self.coinshare and vote2.sender not in self.qc2 and vote2.qc_sender == self.id:
            with self.lock:
                self.storeVote2Msg(vote2)
            threading.Thread(target=self.checkIfQuorum, args=(vote2)).start()
            #threading.Thread(target=self.tryToNextRound).start() #vérifier si toujours besoin de ça
            self.tryToCommit() #vérifier si toujours besoin de ça (leader dans qc2 ?)

    def handleElectMsg(self, elect: Elect):
        if not self.leader and elect.sender not in self.elect:
            with self.lock:
                self.storeElectMsg(elect)
            threading.Thread(target=self.checkIfQuorum, args=(elect)).start()



    def storeBlock1Msg(self, block1: Block1):
        self.blocks1[block1.sender] = block1

    def storeVote1Msg(self, vote1: Vote1):
        self.qc1.append(vote1.sender)

    def storeBlock2Msg(self, block2: Block2): 
        self.pendingReady[block2.sender] = block2

    def storeVote2Msg(self, done: Vote2):
        self.qc2.append(vote2.sender)
        #self.moveRound += 1 #toujours besoin de ça ?

    def storeElectMsg(self, elect: Elect):
        self.elect[elect.Sender] = elect


    def checkIfQuorum(self, msg):
        if type(msg) == Vote1:
            if len(self.qc1) >= self.quorumNum:
                threading.Thread(target=self.broadcastBlock2).start()

        elif type(msg) == Vote2:
            if len(self.qc2) >= self.quorumNum:
                threading.Thread(target=self.broadcastElect).start()

        elif type(msg) == Elect:
            if len(self.elect) >= self.quorumNum:
                threading.Thread(target=self.broadcastLeader).start()



    def tryToCommit(self):
        if self.leader and self.leader in self.qc2 and self.leader in self.blocks1: #leader dans qc2 = leader done avant
            leader_block = self.blocks1[self.leader]
            leader_hash = leader_block.get_hash_as_string()
            self.chain[leader_hash] = leader_block
            #self.logger.info("commit the leader block", node=self.name, round=round, block_proposer=block.Sender)
            #commit_time = time.time_ns()
            #latency = commit_time - block.TimeStamp
            #self.evaluation.append(latency)
            #self.commitTime.append(commit_time)


    def BroadcastLeader(self):
        self.leader[1] = self.qccoin
        #broadcast

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
            self.block1.append(block)

            self.block2.append(block)
            self.coinshare.append(coinsharesig)
            

    """ def broadcastVote(self, blockSender):
        vote = Vote(voteSender=self.name, blockSender=blockSender)
        self.broadcast('VoteTag', vote)

    def broadcastBlock2(self, hash, blockSender):
        partialSig = Sign.sign_ts_partial(self.tsPrivateKey, hash)
        ready = Block2(readySender=self.name, blockSender=blockSender, hash=hash, partialSig=partialSig)
        self.broadcast('ReadyTag', ready) """


    def returnBlockChan(self):
        return self.blockCh

    def returnDoneChan(self):
        return self.doneCh
    

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

    def NewBlock(self):
        timestamp = time.time_ns()
        return Block(self.name,timestamp)
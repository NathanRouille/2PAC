import math
import threading
import time
import random
import inspect
import copy

#Importer d'autres fichier
from sign import verify_signed, Sign
from data_struct import *  
from tools import *
from com import Com

random.seed(7777)


class Node:
    def __init__(self, id : int, host : str, port : int, peers : list, publickey, privatekey, isDelayed: bool,start_time):

        # attributs propres au Node
        self.id = id #de 1 à 4
        self.host = host
        self.port = port
        self.peers = peers
        self.publickey = publickey
        self.privatekey = privatekey
        self.delay = isDelayed           #A rajouter
        self.lock = threading.RLock()
        self.com=Com(self.id,self.port,self.peers,self.delay)

        #attributs pour stocker les blocks et coinshare du Node
        self.sentBlock1 = False
        self.sentBlock2 = False
        self.sentCoinShare = False

        self.block1 = [] #ajouter Block1 à blocks1 plutôt
        self.block2 = [] #ajouter Block2 à blocks2 plutôt
        self.coinshare = [] #vérifier si on adapte ou non avec un sentCoinshare
        
        #attributs pour stocker les messages des autres Nodes
        self.blocks1 = {}
        self.qc1 = {self.id:[self.id]}
        self.blocks2 = {}
        self.qc2 = {self.id:[self.id]}
        self.elect = {}
        self.leader = 0 #leader par défaut 0
        self.chain = []
        
        self.moveRound = 0 #à enlever / adapter pour views

        #attributs propres au réseau de Nodes
        self.qccoin = random.randint(1, 5)
        self.nodeNum = 4
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)

        self.starter_time = start_time

        self.flag_vote1 = False
        self.flag_vote2 = False
        self.flag_elect = False
        self.flag_block1 = False
        self.flag_block2 = False
        self.flag_leader = False

        self.times = {}

        #attributs de test de performances
        #self.evaluation = []
        #self.commitTime = []
           
    
    def logger(self):
        # Obtenez le cadre de pile actuel
        current_frame = inspect.currentframe()
        # Obtenez le cadre de pile de l'appelant (le cadre parent)
        caller_frame = current_frame.f_back
        # Obtenez le nom de la fonction appelante
        function_name = caller_frame.f_code.co_name

        if function_name == "handleBlock1Msg":
            if not self.flag_block1:
                delta = time.time()-self.starter_time
                print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
                self.times['block1'] = delta
                self.flag_block1 = True
            else:
                pass
        elif function_name == "handleBlock2Msg":
            if not self.flag_block2:
                delta = time.time()-self.starter_time
                print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
                self.times['block2'] = delta
                self.flag_block2 = True
            else:
                pass
        elif function_name == "handleVote2Msg":
            if not self.flag_vote2:
                delta = time.time()-self.starter_time
                print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
                self.times['vote2'] = delta
                self.flag_vote2 = True
            else:
                pass
        elif function_name == "handleVote1Msg":
            if not self.flag_vote1:
                delta = time.time()-self.starter_time
                print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
                self.times['vote1'] = delta
                self.flag_vote1 = True
            else:
                pass 
        elif function_name == "handleElectMsg":
            if not self.flag_elect:
                delta = time.time()-self.starter_time
                print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
                self.times['elect'] = delta                
                self.flag_elect = True
            else:
                pass
        elif function_name == "handleLeaderMsg":
            if not self.flag_leader:
                delta = time.time()-self.starter_time
                print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
                self.times['leader'] = delta               
                self.flag_leader = True
            else:
                pass
        else:                   
            print(f"secondary fonction: {function_name} reached by node: {self.id}")


   
    def handleMsgLoop(self):
        ''' Fonction pour gérer les messages reçus par le Node'''

        self.logger()
        msgCh = self.com.recv
        while True:
            msgWithSig = msgCh.get()
            msgAsserted = msgWithSig["data"]
            msg_type = msgWithSig["type"]
            msg_publickey= msgWithSig["public_key"]
            msg_signature= msgWithSig["signature"]
            """ print(f"Verify msg : {verify_signed(msg_signature)}") """
            if not verify_signed(msg_signature):
                self.logger.error(f"fail to verify the {msg_type.lower()}'s signature", "round", msgAsserted.Round, "sender", msgAsserted.Sender)
                continue
            if msg_type == 'Block1':
                #print(f"msgAsserted de Block1 : {msgAsserted} pour id= {self.id}")
                block1=Block1(msgAsserted["sender"])
                threading.Thread(target=self.handleBlock1Msg, args=(block1,)).start()
            
            elif msg_type == 'Vote1':
                #print(f"msgAsserted de Vote1 : {msgAsserted} pour id= {self.id}")
                vote1=Vote1(msgAsserted["sender"],msgAsserted["Block_sender"])
                threading.Thread(target=self.handleVote1Msg, args=(vote1,)).start()
            
            elif msg_type == 'Block2':
                #print(f"msgAsserted de Block2 : {msgAsserted} pour id= {self.id}")
                #print(f"Bla self.blocks1 : {self.blocks1}")
                block2=Block2(msgAsserted["sender"],msgAsserted["qc"])
                threading.Thread(target=self.handleBlock2Msg, args=(block2,)).start()
            
            elif msg_type == 'Vote2':
                #print(f"msgAsserted de Vote2 : {msgAsserted} pour id= {self.id}")
                vote2=Vote2(msgAsserted["sender"],msgAsserted["QC_sender"])
                threading.Thread(target=self.handleVote2Msg, args=(vote2,)).start()
            
            elif msg_type == 'Elect':
                #print(f"msgAsserted de Elect : {msgAsserted} pour id= {self.id}")
                elect=Elect(msgAsserted["sender"])
                threading.Thread(target=self.handleElectMsg, args=(elect,)).start()
            elif msg_type == 'Leader':
                #print(f"msgAsserted de Leader : {msgAsserted} pour id= {self.id}")
                leader=Leader(msgAsserted["sender"],msgAsserted["id_leader"])
                threading.Thread(target=self.handleLeaderMsg, args=(leader,)).start()
            

#############       Handle de Message       #############
#########################################################
    def handleBlock1Msg(self, block1: Block1):
        ''' Fonction pour gérer les messages de type Block1 puis broadcast d'un message de type Vote1'''
        self.logger()
        if block1.sender not in self.blocks1:
            with self.lock:
                self.storeBlock1Msg(block1)
            threading.Thread(target=self.broadcastVote1, args=(block1.sender,)).start()
            self.tryToCommit()
    

    def handleVote1Msg(self, vote1: Vote1):
        ''' Fonction pour gérer les messages de type Vote1 puis check du Quorum'''
        self.logger()
        with self.lock:
            if vote1.block_sender in self.qc1 and vote1.sender not in self.qc1[vote1.block_sender]:
                self.storeVote1Msg(vote1)
                self.checkIfQuorum(vote1)
                self.tryToCommit()

    def handleBlock2Msg(self, block2: Block2):#vérifier le qc ?
        ''' Fonction pour gérer les messages de type Block2 puis broadcast d'un message de type Vote2'''
        self.logger()
        if block2.sender not in self.blocks2:
            with self.lock:
                self.storeBlock2Msg(block2)
            if block2.sender in self.qc1 and len(self.qc1[block2.sender]) >= self.quorumNum:
                #alors send vote2 (et edit la variable de vote2 attention à l'accès simultané des threads avec lock)
                threading.Thread(target=self.broadcastVote2, args=(block2.sender,)).start()
                self.tryToCommit()

    def handleVote2Msg(self, vote2: Vote2):
        ''' Fonction pour gérer les messages de type Vote2 puis check du Quorum'''
        self.logger()
        with self.lock:
            if vote2.block_sender in self.qc2 and vote2.sender not in self.qc2[vote2.block_sender]:   #not self.sentCoinShare and 
                self.storeVote2Msg(vote2)
                self.checkIfQuorum(vote2)
                self.tryToCommit()

    def handleElectMsg(self, elect: Elect):
        ''' Fonction pour gérer les messages de type Elect puis check du Quorum'''
        self.logger()
        with self.lock:
            if not self.leader and elect.sender not in self.elect:
                self.storeElectMsg(elect)
                self.checkIfQuorum(elect)
                self.tryToCommit()
    
    def handleLeaderMsg(self, leader: Leader):
        ''' Fonction pour gérer les messages de type Leader puis tryToCommit'''
        self.logger()
        with self.lock:
            if not self.leader:
                print(f"Commit pour id= {self.id}")
                self.leader = leader.id_leader
                self.tryToCommit()
    


##############       Fonction Store       ###############
#########################################################
    def storeBlock1Msg(self, block1: Block1):
        self.logger()
        self.blocks1[block1.sender] = block1

    def storeVote1Msg(self, vote1: Vote1):
        self.logger()
        if vote1.block_sender not in self.qc1:
            self.qc1[vote1.block_sender]=[]
        self.qc1[vote1.block_sender].append(vote1.sender)

    def storeBlock2Msg(self, block2: Block2): 
        self.logger()
        self.blocks2[block2.sender] = block2
        if block2.sender not in self.qc1: #au cas où on reçoit un block2 étendant un block1 avant d'avoir reçu le moindre vote1 sur ce block1, on initialise le qc1 pour ce proposeur
            self.qc1[block2.sender] = []
        if block2.qc != None and len(self.qc1[block2.sender]) < self.quorumNum: #on suppose que la vérification de la validité de block2.qc a été faite
            self.qc1[block2.sender] = copy.deepcopy(block2.qc)

    def storeVote2Msg(self, vote2: Vote2):
        self.logger()
        if vote2.block_sender not in self.qc2:
            self.qc2[vote2.block_sender]=[]
        self.qc2[vote2.block_sender].append(vote2.sender)

    def storeElectMsg(self, elect: Elect):
        self.logger()
        self.elect[elect.sender] = elect

##############       Check du Quorum       ##############
#########################################################
    def checkIfQuorum(self, msg):
        self.logger()
        if type(msg) == Vote1:
            with self.lock:
                if len(self.qc1[msg.block_sender]) >= self.quorumNum:
                    if msg.block_sender == self.id: #et pas déjà envoyé de block2 (attention threads)
                        self.block2.append(True) ####A modifier###
                        self.sentBlock2 = True
                        threading.Thread(target=self.broadcastBlock2, args=(self.qc1[self.id],)).start()
                    elif msg.block_sender in self.blocks2: #et si pas encore voté pour le Block2 
                        #alors send vote2 (et edit la variable de vote2 attention à l'accès simultané des threads avec lock)
                        #threading.Thread(target=self.broadcastVote2, args=(msg.block_sender,)).start()
                        
        elif type(msg) == Vote2:
            with self.lock:
                if sum(len(qc2) >= self.quorumNum for qc2 in self.qc2.values()) >= self.quorumNum: #et pas déjà envoyé de CoinShare
                    self.coinshare.append(True) ####A modifier###
                    self.sentCoinShare = True
                    threading.Thread(target=self.broadcastElect, args=()).start()

        elif type(msg) == Elect:
            with self.lock:
                if len(self.elect) >= self.quorumNum:
                    self.leader = self.qccoin
                    threading.Thread(target=self.broadcastLeader, args=()).start()


##################       Commit       ###################
#########################################################
    def tryToCommit(self):
        self.logger()
        if not self.leader or self.leader not in self.qc1 or self.leader not in self.qc2:
            return
        elif len(self.qc1[self.leader]) >= self.quorumNum and len(self.qc2[self.leader]) >= self.quorumNum and self.leader in self.blocks1:
            leader_block = self.blocks1[self.leader]
            self.chain.append(leader_block)
            print(f"Chain {self.chain[0].sender} pour id= {self.id}")
            #self.logger.info("commit the leader block", node=self.name, round=round, block_proposer=block.Sender)
            #commit_time = time.time_ns()
            #latency = commit_time - block.TimeStamp
            #self.evaluation.append(latency)
            #self.commitTime.append(commit_time)

#################       Broadcast       #################
#########################################################
    def broadcastLeader(self):
        self.logger()
        print(f"Le Leader est {self.leader} pour id= {self.id}")
        message=Leader(self.id,self.leader)
        broadcast(self.com, to_json(message, self))

    def broadcastBlock1(self, block):
        self.logger()
        with self.lock:
            self.block1.append(block)
        print(f"broadcastBlock1 de id= {self.id}")
        broadcast(self.com, to_json(block, self))
        
    def broadcastVote1(self, blockSender):
        self.logger()
        message=Vote1(self.id,blockSender)
        broadcast(self.com, to_json(message, self))
        
    def broadcastBlock2(self, qc):
        self.logger()
        message=Block2(self.id,qc)
        broadcast(self.com, to_json(message, self))

    def broadcastVote2(self, qc_sender):
        self.logger()
        message=Vote2(self.id,qc_sender)
        broadcast(self.com, to_json(message, self))

    def broadcastElect(self):
        self.logger()
        message=Elect(self.id)
        broadcast(self.com, to_json(message, self))
        

    
    '''
    def RunLoop(self): # à quoi sert RunLoop (quand est-ce que c'est appelé)
        #start = time.time_ns()
        #créer block1 et block2
        self.broadcastBlock1(block1)
        self.broadcastBlock2(block2)
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
        self.logger.info("the total commit", block_number=blockNum, time=pastTime)'''
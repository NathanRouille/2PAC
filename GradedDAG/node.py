import math
import threading
import time
import random
import inspect
import queue
import os

#Imports de fichiers locaux
from sign import verify_signed, Sign
from data_struct import *  
from tools import *
from com import Com



class Node:
    def __init__(self, id : int, host : str, port : int, peers : list, publickey, privatekey, isDelayed: bool,start_time, seed: int):

        #Attributs propres au Node
        self.id = id                                            #de 1 à 4
        self.host = host                                        #localhost
        self.port = port
        self.peers = peers                                      #liste de tuples comprenant les ports et le host des autres Nodes
        self.publickey = publickey                              #clé publique du Node
        self.privatekey = privatekey                            #clé privée du Node
        self.delay = isDelayed                                  #booléen pour savoir si le Node est delayed ou non
        self.lock = threading.RLock()                           #verrou pour éviter les conflits d'accès aux ressources partagées
        self.com=Com(self.id,self.port,self.peers,self.delay)   #classe de communication du Node
        self.succes = False                                     #booléen pour savoir si le Node a réussi à commit un block
        self.echec = False                                      #booléen pour savoir si le Node a échoué à commit un block
        self.stop_thread = threading.Event()                    #event pour arrêter le thread handleMsgLoop

        #Attributs pour stocker les blocks et coinshare du Node
        self.sentReady = []                                     #liste des Nodes à qui on a envoyé un ready
        self.sentCoinShare = False                              #booléen pour savoir si le Node a envoyé son coinshare

        
        #Attributs pour stocker les messages des autres Nodes
        self.blocks = {}                                        #dictionnaire des blocks que l'on reçoit
        self.grade1 = []                                        #dictionnaire des id de Nodes dont le Block est grade1 (qui a un qc de echo)
        self.qc1 = {self.id:[self.id]}                          #dictionnaire des id de Nodes dont on a reçu un echo qui vote pour le block du premier Node
        self.qc2 = {self.id:[self.id]}                          #dictionnaire des id de Nodes dont on a reçu un ready qui vote pour le block du premier Node
        self.elect = {}                                         #dictionnaire du message d'élection contenant sa coinshare (ici on abstrait la coinshare)
        self.leader = 0                                         #leader par défaut 0 (aucun leader élu)
        self.chain = []                                         #blockchain qui contient le block commit

        #Attributs propres au réseau de Nodes
        random.seed(seed)
        self.qccoin = random.randint(1, 4)                      #qccoin choisi de manière déterministe mais change à chaque exécution, valeur commune à tous les nodes grâce à une seed d'aléatoire
        self.nodeNum = 4                                        #nombre de Nodes
        self.quorumNum = math.ceil(2 * self.nodeNum / 3.0)      #nombre de Nodes pour le quorum
        self.thirdNum = math.ceil(self.nodeNum / 3.0)           

        #Logger
        self.starter_time = start_time                          #temps de départ (le même pour tous les Nodes)
        self.datas_block = {1: None, 2: None, 3: None, 4: None}
        self.datas_echo = {"block 1": {1: None, 2: None, 3: None, 4: None}, "block 2": {1: None, 2: None, 3: None, 4: None}, "block 3": {1: None, 2: None, 3: None, 4: None}, "block 4": {1: None, 2: None, 3: None, 4: None}}
        self.datas_ready = {"qc sender 1": {1: None, 2: None, 3: None, 4: None}, "qc sender 2": {1: None, 2: None, 3: None, 4: None}, "qc sender 3": {1: None, 2: None, 3: None, 4: None}, "qc sender 4": {1: None, 2: None, 3: None, 4: None}}
        self.datas_elect = {1: None, 2: None, 3: None, 4: None}
        self.datas_leader = {1: None, 2: None, 3: None, 4: None, "id leader": 0}
        self.log_data={'Receptions Block':{},'Receptions Echo':{},'Receptions Ready':{},'Receptions Elect':{},'Receptions Leader':{},'Commit': None}

        #Fichier log
        self.log_file_path = os.path.join('log', f'node_{self.id}.json')
        if not os.path.exists('log'):                           #on crée le dossier log s'il n'existe pas
            os.makedirs('log')
        self.initialize_log_file()                              # on initialise les logs avec des json vides

   
    def handleMsgLoop(self):
        ''' Fonction pour gérer les messages reçus par le Node'''
        self.logger()
        msgCh = self.com.recv
        while True:
            try:
                msgWithSig = msgCh.get(timeout=1)               # Utiliser un timeout pour éviter de bloquer indéfiniment
            except queue.Empty:
                continue
            msgAsserted = msgWithSig["data"]
            msg_type = msgWithSig["type"]
            msg_signature= msgWithSig["signature"]
            if not verify_signed(msg_signature):                #on vérifie la signature du message
                self.logger.error(f"fail to verify the {msg_type.lower()}'s signature", "round", msgAsserted.Round, "sender", msgAsserted.Sender)
                continue
            if msg_type == 'Block':
                block=Block(msgAsserted["sender"])
                threading.Thread(target=self.handleBlockMsg, args=(block,)).start()
            
            elif msg_type == 'Echo':
                echo=Echo(msgAsserted["sender"],msgAsserted["Block_sender"])
                threading.Thread(target=self.handleEchoMsg, args=(echo,)).start()
            
            elif msg_type == 'Ready':
                ready=Ready(msgAsserted["sender"],msgAsserted["Block_sender"])
                threading.Thread(target=self.handleReadyMsg, args=(ready,)).start()
            
            elif msg_type == 'Elect':
                elect=Elect(msgAsserted["sender"])
                threading.Thread(target=self.handleElectMsg, args=(elect,)).start()

            elif msg_type == 'Leader':
                leader=Leader(msgAsserted["sender"],msgAsserted["id_leader"])
                threading.Thread(target=self.handleLeaderMsg, args=(leader,)).start()
            

#############       Handle Messages       #############
#########################################################
    def handleBlockMsg(self, block: Block):
        ''' Fonction pour gérer les messages de type Block puis broadcast d'un message de type Echo'''
        self.logger(block)
        if block.sender not in self.blocks:
            if self.sentCoinShare and block.sender not in self.grade1:                  #Les nouveaux blocks qui ne sont pas de grade 1 ne sont pas pris un compte après avoir envoyé sa coinshare
                return
            with self.lock:
                self.storeBlockMsg(block)
            if block.sender not in self.qc1:
                self.qc1[block.sender] = []
            self.qc1[block.sender].append(self.id)
            threading.Thread(target=self.broadcastEcho, args=(block.sender,)).start()   #La vérification du contenu du block avant de le voter est abstraite
            self.tryToCommit()
    

    def handleEchoMsg(self, echo: Echo):
        ''' Fonction pour gérer les messages de type Echo puis check du Quorum'''
        self.logger(echo)
        with self.lock:
            if self.sentCoinShare and echo.block_sender not in self.grade1:             #Les echo pour un block qui n'est pas grade 1 (non reçeption d'un qc de echo) ne sont pas pris en compte après avoir envoyé son coinshare
                return
            if echo.block_sender not in self.qc1:
                self.qc1[echo.block_sender] = []
            if echo.sender not in self.qc1[echo.block_sender]:
                self.storeEchoMsg(echo)
                self.checkIfQuorum(echo)


    def handleReadyMsg(self, ready: Ready):
        ''' Fonction pour gérer les messages de type Ready puis check du Quorum'''
        self.logger(ready)
        with self.lock:
            if self.sentCoinShare and ready.block_sender not in self.grade1:            #on ne prend les ready pour un block qui n'est pas grade 1 (dont on a pas reçu de qc de echo) après avoir envoyé son coinshare
                return
            if ready.block_sender not in self.qc2:
                self.qc2[ready.block_sender] = []
            if ready.sender not in self.qc2[ready.block_sender]:
                self.storeReadyMsg(ready)
                self.checkIfQuorum(ready)
                self.tryToCommit()

    def handleElectMsg(self, elect: Elect):
        ''' Fonction pour gérer les messages de type Elect puis check du Quorum'''
        self.logger(elect)
        with self.lock:
            if not self.leader and elect.sender not in self.elect:
                self.storeElectMsg(elect)
                self.checkIfQuorum(elect)
                self.tryToCommit()
    
    def handleLeaderMsg(self, leader: Leader):
        ''' Fonction pour gérer les messages de type Leader puis tryToCommit'''
        self.logger(leader)
        with self.lock:
            if not self.leader:
                self.leader = leader.id_leader
                self.tryToCommit()
    


##############       Fonctions Store       ###############
#########################################################
    def storeBlockMsg(self, block: Block):
        self.logger()
        self.blocks[block.sender] = block

    def storeEchoMsg(self, echo: Echo):
        self.logger()
        self.qc1[echo.block_sender].append(echo.sender)

    def storeReadyMsg(self, ready: Ready):
        self.logger()
        self.qc2[ready.block_sender].append(ready.sender)

    def storeElectMsg(self, elect: Elect):
        self.logger()
        self.elect[elect.sender] = elect

##############       Check du Quorum Certificate      ##############
#########################################################
    def checkIfQuorum(self, msg):
        self.logger()
        if type(msg) == Echo:
            with self.lock:
                if len(self.qc1[msg.block_sender]) >= self.quorumNum and msg.block_sender not in self.sentReady:
                    self.sentReady.append(msg.block_sender)
                    self.grade1.append(msg.block_sender)
                    if msg.block_sender not in self.qc2:
                        self.qc2[msg.block_sender] = []
                    self.qc1[msg.block_sender].append(self.id)
                    threading.Thread(target=self.broadcastReady, args=(msg.block_sender,)).start()
                        
        elif type(msg) == Ready:
            with self.lock:
                if len(self.qc2[msg.block_sender]) >= self.thirdNum and msg.block_sender not in self.sentReady:
                    self.sentReady.append(msg.block_sender)
                    self.grade1.append(msg.block_sender)
                    if msg.block_sender not in self.qc2:
                        self.qc2[msg.block_sender] = []
                    self.qc1[msg.block_sender].append(self.id)
                    threading.Thread(target=self.broadcastReady, args=(msg.block_sender,)).start()
                if sum(len(qc2) >= self.quorumNum for qc2 in self.qc2.values()) >= self.quorumNum and not self.sentCoinShare:
                    self.sentCoinShare = True
                    self.elect[self.id] = Elect(self.id)
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
        if self.leader: 
            if self.leader not in self.qc2:
                self.echec = True # échec
            elif len(self.qc2[self.leader]) >= self.quorumNum and self.leader in self.blocks: #on vérifie uniquement que le block du leader est grade2 car il est a fortiori grade1
                leader_block = self.blocks[self.leader]
                self.chain.append(leader_block)
                self.succes = True # succès
            else:
                self.echec = True # échec
        

#################       Broadcast       #################
#########################################################
    def broadcastLeader(self):
        self.logger()
        message=Leader(self.id,self.leader)
        broadcast(self.com, to_json(message, self))

    def broadcastBlock(self, block):
        self.logger()
        self.blocks[self.id]= block #on stock son propre Block pour pouvoir le commit si on est élu comme leader
        broadcast(self.com, to_json(block, self))
        self.broadcastEcho(self.id)
        
    def broadcastEcho(self, blockSender):
        self.logger()
        message=Echo(self.id,blockSender)
        broadcast(self.com, to_json(message, self))

    def broadcastReady(self, block_sender):
        self.logger()
        message=Ready(self.id,block_sender)
        broadcast(self.com, to_json(message, self))

    def broadcastElect(self):
        self.logger()
        message=Elect(self.id)
        broadcast(self.com, to_json(message, self))



##############       Gestion des logs       #############
#########################################################

    def initialize_log_file(self):
            with open(self.log_file_path, 'w') as log_file:
                json.dump({}, log_file, indent=4)
    
    def write_log(self, log_data):
        with open(self.log_file_path, 'w') as log_file:
            # Write the provided dictionary to the log file in JSON format
            json.dump(log_data, log_file, indent=4)
    
    def logger(self,data=None):
        # Obtenez le cadre de pile actuel
        current_frame = inspect.currentframe()
        # Obtenez le cadre de pile de l'appelant (le cadre parent)
        caller_frame = current_frame.f_back
        # Obtenez le nom de la fonction appelante
        function_name = caller_frame.f_code.co_name

        if function_name == "handleBlockMsg":
            delta = time.time()-self.starter_time
            #print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
            self.datas_block[data.sender] = delta
        
        elif function_name == "handleEchoMsg":
            delta = time.time()-self.starter_time
            #print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
            self.datas_echo[f"block {data.block_sender}"][data.sender] = delta

        elif function_name == "handleReadyMsg":
            delta = time.time()-self.starter_time
            #print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
            self.datas_ready[f"qc sender {data.block_sender}"][data.sender] = delta
        
        elif function_name == "handleElectMsg":
            delta = time.time()-self.starter_time
            #print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
            self.datas_elect[data.sender] = delta
                            
        elif function_name == "handleLeaderMsg":
            delta = time.time()-self.starter_time
            #print(f"node: {self.id} reached fonction_name: {function_name} for the first with delta : {delta}s")
            self.datas_leader[data.sender] = delta 
            self.datas_leader["id leader"] = self.leader              
          
        else:                   
            #print(f"secondary fonction: {function_name} reached by node: {self.id}")
            pass
    
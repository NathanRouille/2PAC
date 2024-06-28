from tools import broadcast, to_json
import random
from node import Node
from sign import Sign
from data_struct import *
import threading
import time

list_ports = random.sample(range(1000, 9000), 4)
ports = {
    "node1": list_ports[0],
    "node2": list_ports[1],
    "node3": list_ports[2],
    "node4": list_ports[3],
}

block1 = Block1(1)
block2 = Block1(2)
block3 = Block1(3)
block4 = Block1(4)


def setup_nodes(start_time):
    #seed = random.randint(1,1000) #on génère une seed random pour avoir un qccoin déterministe identique pour chaque Node mais qui change à chaque exécution
    seed = 7777
    privatekey4, publickey4 = Sign.generate_keypair()
    privatekey1, publickey1 = Sign.generate_keypair()
    privatekey2, publickey2 = Sign.generate_keypair()
    privatekey3, publickey3 = Sign.generate_keypair()
    node1 = Node(1,'localhost', ports["node1"], [('localhost', ports["node2"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey1, privatekey1,False,start_time,seed)
    node2 = Node(2,'localhost', ports["node2"], [('localhost', ports["node1"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey2, privatekey2,True,start_time,seed)
    node3 = Node(3,'localhost', ports["node3"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node4"])], publickey3, privatekey3,False,start_time,seed)
    node4 = Node(4,'localhost', ports["node4"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], publickey4, privatekey4,False,start_time,seed)
    Nodes = [node1, node2, node3, node4]
    return Nodes

def start_coms(Nodes):
    coms = []
    for node in Nodes:
        com = node.com.start()
        coms.append(com)
    return coms

def write_result(node):
    node.log_data['Receptions Block1']=node.datas_block1
    node.log_data['Receptions Vote1']=node.datas_vote1
    node.log_data['Receptions Block2']=node.datas_block2
    node.log_data['Receptions Vote2']=node.datas_vote2
    node.log_data['Receptions Elect']=node.datas_elect
    node.log_data['Receptions Leader']=node.datas_leader
    node.log_data['Commit']=f"Block1 du node : {node.chain[0].sender}"
    node.write_log(node.log_data)

def wait_and_write(node,duration):
    time.sleep(duration)
    print(f"Writing result for node : {node.id}")
    try:
        write_result(node)
    except:
        print(False)


    

if __name__ == "__main__":
    start_time = time.time()
    Nodes = setup_nodes(start_time)
    coms = start_coms(Nodes)
    threads = [
        threading.Thread(target=Nodes[0].handleMsgLoop),
        threading.Thread(target=Nodes[1].handleMsgLoop),
        threading.Thread(target=Nodes[2].handleMsgLoop),
        threading.Thread(target=Nodes[3].handleMsgLoop),
    ]

    for thread in threads:
        thread.start()

    _2PAC_pire_cas = False #variable pour choisir si on se place dans le pire cas de 2PAC et donc si chaque node attent d'avoir crée un qc sur son propre Block1 avant de créer le Block2 qui l'étend

    Nodes[0].broadcastBlock1(block1)
    Nodes[1].broadcastBlock1(block2)
    Nodes[2].broadcastBlock1(block3)
    Nodes[3].broadcastBlock1(block4)
    if not _2PAC_pire_cas:
        Nodes[0].sentBlock2 = True
        Nodes[1].sentBlock2 = True
        Nodes[2].sentBlock2 = True
        Nodes[3].sentBlock2 = True
        Nodes[0].broadcastBlock2(None)
        Nodes[1].broadcastBlock2(None)
        Nodes[2].broadcastBlock2(None)
        Nodes[3].broadcastBlock2(None)

    
    for node in Nodes:
        threading.Thread(target = wait_and_write, args=(node,15,)).start() 

    for thread in threads:
        thread.join()
                                                    
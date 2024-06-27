from tools import broadcast, to_json
import random
from node import Node
from sign import Sign
from data_struct import *
import threading
import time

list_ports = [random.randint(1000, 9000) for i in range(4)]
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


vote = Vote2(0,1)

def setup_nodes(start_time):
    privatekey4, publickey4 = Sign.generate_keypair()
    privatekey1, publickey1 = Sign.generate_keypair()
    privatekey2, publickey2 = Sign.generate_keypair()
    privatekey3, publickey3 = Sign.generate_keypair()
    node1 = Node(1,'localhost', ports["node1"], [('localhost', ports["node2"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey1, privatekey1,False,start_time)
    node2 = Node(2,'localhost', ports["node2"], [('localhost', ports["node1"]), ('localhost', ports["node3"]), ('localhost', ports["node4"])], publickey2, privatekey2,False,start_time)
    node3 = Node(3,'localhost', ports["node3"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node4"])], publickey3, privatekey3,False,start_time)
    node4 = Node(4,'localhost', ports["node4"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], publickey4, privatekey4,True,start_time)
    Nodes = [node1, node2, node3, node4]
    return Nodes

def start_coms(Nodes):
    coms = []
    for node in Nodes:
        com = node.com.start()
        coms.append(com)
    return coms

def show_result(node):
    print(f"time_list of node: {node.id}: {node.times}")

def wait_and_show(node,duration):
    time.sleep(duration)
    show_result(node)

    

if __name__ == "__main__":
    start_time = time.time()
    Nodes = setup_nodes(start_time)
    coms = start_coms(Nodes)
    print("Nodes and coms setup")
    threading.Thread(target=Nodes[0].handleMsgLoop).start()
    threading.Thread(target=Nodes[1].handleMsgLoop).start()
    threading.Thread(target=Nodes[2].handleMsgLoop).start()
    threading.Thread(target=Nodes[3].handleMsgLoop).start()

    broadcast(coms[0], to_json(block1, Nodes[0]))
    Nodes[0].block1.append(block1)
    broadcast(coms[1], to_json(block2, Nodes[1]))
    Nodes[1].block1.append(block2)
    broadcast(coms[2], to_json(block3, Nodes[2]))
    Nodes[2].block1.append(block3)
    broadcast(coms[3], to_json(block4, Nodes[3]))
    Nodes[3].block1.append(block4) 
    

    for node in Nodes:
        threading.Thread(target = wait_and_show, args=(node,10,)).start()



                                                                                        
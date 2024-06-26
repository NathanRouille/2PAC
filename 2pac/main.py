from tools import broadcast, to_json
import random
from node import Node
from sign import Sign
from data_struct import *
import threading

list_ports = [random.randint(1000, 9000) for i in range(4)]
ports = {
    "node0": list_ports[0],
    "node1": list_ports[1],
    "node2": list_ports[2],
    "node3": list_ports[3],
}

block = Block2(0, "block",'lol')

vote = Vote2(0,1)

def setup_nodes():
    privatekey0, publickey0 = Sign.generate_keypair()
    privatekey1, publickey1 = Sign.generate_keypair()
    privatekey2, publickey2 = Sign.generate_keypair()
    privatekey3, publickey3 = Sign.generate_keypair()
    node0 = Node(0,'localhost', ports["node0"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], 0, publickey0, privatekey0,True)
    node1 = Node(1,'localhost', ports["node1"], [('localhost', ports["node0"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], 0, publickey1, privatekey1,False)
    node2 = Node(2,'localhost', ports["node2"], [('localhost', ports["node0"]), ('localhost', ports["node1"]), ('localhost', ports["node3"])], 0, publickey2, privatekey2,False)
    node3 = Node(3,'localhost', ports["node3"], [('localhost', ports["node0"]), ('localhost', ports["node1"]), ('localhost', ports["node2"])], 0, publickey3, privatekey3,False)
    Nodes = [node0, node1, node2, node3]
    return Nodes

def start_coms(Nodes):
    coms = []
    for node in Nodes:
        com = node.com.start()
        coms.append(com)
    return coms

if __name__ == "__main__":
    Nodes = setup_nodes()
    coms = start_coms(Nodes)
    print("Nodes and coms setup")
    threading.Thread(target=Nodes[1].handleMsgLoop).start()
    print("Node 1 started")
    broadcast(coms[2], to_json(block, Nodes[2]))
    broadcast(coms[0], to_json(vote, Nodes[0]))

                                                                                        
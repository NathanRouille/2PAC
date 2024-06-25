from tools import *
import random
from tools import broadcast


list_ports = [random.randint(1000, 9000) for i in range(4)]
ports = {
    "node0": list_ports[0],
    "node1": list_ports[1],
    "node2": list_ports[2],
    "node3": list_ports[3],
}

block = Block1(0, "block")

vote = Vote(1)

def setup_nodes():
    node0 = Node(0,'localhost', ports["node0"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], 0, None, None)
    node1 = Node(1,'localhost', ports["node1"], [('localhost', ports["node0"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], 0, None, None)
    node2 = Node(2,'localhost', ports["node2"], [('localhost', ports["node0"]), ('localhost', ports["node1"]), ('localhost', ports["node3"])], 0, None, None)
    node3 = Node(3,'localhost', ports["node3"], [('localhost', ports["node0"]), ('localhost', ports["node1"]), ('localhost', ports["node2"])], 0, None, None)
    Nodes = [node0, node1, node2, node3]
    return Nodes

def start_coms(Nodes):
    coms = []
    for node in Nodes:
        com = start_com(node)
        coms.append(com)
    return coms

if __name__ == "__main__":
    Nodes = setup_nodes()
    coms = start_coms(Nodes)
    print("Nodes and coms setup")
    broadcast(coms[0], block)
                                                                                        
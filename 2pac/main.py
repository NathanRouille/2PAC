from tools import *
import random


list_ports = [random.randint(1000, 9000) for i in range(4)]
ports = {
    "node0": list_ports[0],
    "node1": list_ports[1],
    "node2": list_ports[2],
    "node3": list_ports[3],
}

def setup_nodes():
    node0 = Node(0, ports["node0"], [('localhost', ports["node1"]), ('localhost', ports["node2"]), ('localhost', ports["node3"])], 0, None, None)
    node1 = Node(1, ports["node1"], [('localhost', ports["node0"]), ('localhost', ports["node2']), ('localhost', ports["node3'])], 0, None, None)
                                                                                        
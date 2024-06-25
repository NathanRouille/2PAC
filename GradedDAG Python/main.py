##############         IMPORTS         ##############
#####################################################
# Importer les bibliothèques nécessaires
from nacl import signing, encoding
import time
import re
import gmpy2
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import random

#Import d'autres fichier
from node import *
from config import *
from network import *
from sign import *

##############         CLASSES         ##############
#####################################################


#############         VARIABLES         #############
#####################################################

# Define cluster addresses
cluster_addr = {
    "node0": "127.0.0.1",
    "node1": "127.0.0.1",
    "node2": "127.0.0.1",
    "node3": "127.0.0.1",
}

# Define cluster ports
cluster_port = {
    "node0": 8000,
    "node1": 8010,
    "node2": 8020,
    "node3": 8030,
}


#############         FUNCTIONS         #############
#####################################################
# Fonction pour configurer les nœuds
def setup_nodes( batch_size, round):
    # Initialisation des noms et des adresses avec ports
    names = [None] * 4
    cluster_addr_with_ports = {}

    for name, addr in cluster_addr.items():
        i = int(name[4:])  # Extraction de l'index numérique du nom
        names[i] = name
        cluster_addr_with_ports[f"{addr}:{cluster_port[name]}"] = i

    # Création des clés privées et publiques
    priv_keys = [None] * 4
    pub_keys = [None] * 4
    for i in range(4):
        priv_keys[i], pub_keys[i] = Sign.generate_keypair()

    pub_key_map = {names[i]: pub_keys[i] for i in range(4)}

    # Création des clés de seuil
    shares, pub_poly = gen_ts_keys(3, 4)    # Seuil: 3  (2f+1), Nombre total de parts: 4  (3f+1)

    # Configuration des nœuds
    confs = [None] * 4
    nodes = [None] * 4
    for i in range(4):
        confs[i] = Config(names[i], 10, cluster_addr, cluster_port, None, cluster_addr_with_ports, None, pub_key_map, priv_keys[i], pub_poly, shares[i], False, batch_size, round)
        nodes[i] = NewNode(confs[i])
        if not nodes[i].network.start_p2p_listen():
            raise Exception("Failed to start P2P listener")
        nodes[i].init_cbc(confs[i])

    for i in range(4):
        nodes[i].establish_p2p_conns()

    time.sleep(1)
    return nodes


##############         EXEMPLES         #############
#####################################################

# Example 1
# Exemple d'utilisation de la classe Sign
def exemple1():
   
    # Generate key pair
    private_key, public_key = Sign.generate_keypair()
    print(f"Public Key: {public_key.encode(encoder=encoding.HexEncoder).decode('utf-8')}")

    # Sign a message
    message = "Hello, World!"
    signed_message = Sign.sign_message(private_key, message)
    print(f"Signed Message: {signed_message}")

    # Verify the signature
    is_valid = Sign.verify_signature(public_key, signed_message)
    print(f"Signature valid: {is_valid}")

    # Simulate some delay
    time.sleep(1)


################         MAIN         ###############
#####################################################

if __name__ == "__main__":
    log_level = 1
    batch_size = 10
    round = 1
    nodes = setup_nodes(log_level, batch_size, round)
    for node in nodes:
        print(f"Node Name: {node.name}, Address: {node.address}, Port: {node.port}")

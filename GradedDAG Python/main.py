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

##############         CLASSES         ##############
#####################################################

class Sign:
    @staticmethod
    def generate_keypair():
        private_key = signing.SigningKey.generate()
        public_key = private_key.verify_key
        return private_key, public_key

    @staticmethod
    def sign_message(private_key, message):
        signed = private_key.sign(message.encode('utf-8'))
        return signed

    @staticmethod
    def verify_signature(public_key, signed_message):
        try:
            public_key.verify(signed_message)
            return True
        except:
            return False
        
class PubPoly:
    def __init__(self, coeffs):
        self.coeffs = coeffs

class Share:
    def __init__(self, index, value):
        self.index = index
        self.value = value


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
# Fonction pour générer un scalaire aléatoire
def generate_random_scalar(curve):
    # Utiliser la taille de la clé pour déterminer un scalaire aléatoire approprié
    return gmpy2.mpz(random.SystemRandom().getrandbits(curve.key_size))

# Fonction pour générer les thresold keys
def gen_ts_keys(t, n):
    # Utiliser la courbe SECP256R1 pour la cryptographie à courbe elliptique
    curve = ec.SECP256R1()
    backend = default_backend()

    # On suppose que l'ordre du groupe est 2^256, ce qui est une approximation
    group_order = 2**256

    secret = generate_random_scalar(curve)

    # Générer les coefficients du polynôme privé
    pri_coeffs = [secret] + [generate_random_scalar(curve) for _ in range(t - 1)]

    # Générer les coefficients du polynôme public
    pub_coeffs = [ec.derive_private_key(int(c), curve, backend).public_key() for c in pri_coeffs]

    # Générer les parts (shares)
    shares = []
    for i in range(1, n + 1):
        x = gmpy2.mpz(i)
        share_value = sum([coeff * (x ** idx) % group_order for idx, coeff in enumerate(pri_coeffs)]) % group_order
        shares.append(Share(i, share_value))

    pub_poly = PubPoly(pub_coeffs)
    return shares, pub_poly

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

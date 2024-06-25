##############         IMPORTS         ##############
#####################################################
# Importer les bibliothèques nécessaires
from cryptography.hazmat.primitives import hashes
from nacl import signing, encoding
import re
import gmpy2
import random
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import time

#Importer d'autres fichier

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
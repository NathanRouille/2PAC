import time
import json
from data_struct import *
from nacl import signing, encoding
import base64


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
    def verify_signature(public_key_hex, signed_message_dict):
        try:
            # Convertir la clé publique de hex en bytes
            public_key_bytes = bytes.fromhex(public_key_hex)
            #print("Public Key Bytes:", public_key_bytes)
            verify_key = signing.VerifyKey(public_key_bytes)
            
            # Convertir le message signé de hex en bytes
            signature_bytes = bytes.fromhex(signed_message_dict['signature'])
            #print("Signature Bytes:", signature_bytes)
            message_bytes = bytes.fromhex(signed_message_dict['message'])
            #print("Message Bytes:", message_bytes)
            
            # Recréer l'objet SignedMessage en combinant signature et message
            signed_message_combined = signature_bytes + message_bytes
            #print("Signed Message Combined:", signed_message_combined)
            
            # Vérifier la signature
            verify_key.verify(signed_message_combined)
            return True
        except Exception as e:
            print("Verification failed:", e)
            return False
        
def exemple1():
    # Generate key pair
    private_key, public_key = Sign.generate_keypair()
    print(f"Public Key: {public_key.encode(encoder=encoding.HexEncoder).decode('utf-8')}")

    # Create a JSON message
    message = {
        "greeting": "Hello, World!",
        "timestamp": time.time()
    }
    json_message = json.dumps(message)
    print(f"JSON Message: {json_message}")

    # Sign the JSON message
    signed_message = Sign.sign_message(private_key, json_message)
    print(f"Signed Message: {signed_message}")

    # Verify the signature
    is_valid = Sign.verify_signature(public_key, signed_message)
    print(f"Signature valid: {is_valid}")

    # Simulate some delay
    time.sleep(1)

def send_signed(data,private_key):
    # Convertir les données en JSON
    data_json = json.dumps(data).encode('utf-8')

    # Signer le message avec la clé privée
    signing_key = signing.SigningKey(private_key.encode())
    signed = signing_key.sign(data_json)

    # Convertir le message signé et la signature en hexadécimal
    message_hex = signed.message.hex()
    signature_hex = signed.signature.hex()
    public_key_hex = signing_key.verify_key.encode().hex()

    # Créer un dictionnaire avec ces valeurs
    signed_message_dict = {
        'message': message_hex,
        'signature': signature_hex,
        'public_key': public_key_hex
    }

    # Sérialiser en JSON
    return json.dumps(signed_message_dict)

def verify_signed(signed_message_json):
    signed_message_dict = json.loads(signed_message_json)
    return Sign.verify_signature(signed_message_dict['public_key'], signed_message_dict)  

def find_publickey(message):
    return base64.b64decode(json.loads(message)["public_key"])
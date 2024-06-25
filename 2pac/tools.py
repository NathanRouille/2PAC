import socket
import threading
import time
import json
from com import Com
from data_struct import *
from nacl import signing, encoding

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

def handlemessage(message):
    pass


def start_com(node):
    com = Com(node)
    com.start()
    return com

def broadcast(com, message):
    com.broadcast_message(message)

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
    

    

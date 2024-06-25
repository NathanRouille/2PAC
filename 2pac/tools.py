import socket
import threading
import time
import json
from com import Com
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
    


    
def to_json(obj,node):
    base64_representation = base64.b64encode(node.publickey.encode()).decode('utf-8')
    if isinstance(obj, Block1):
        data = {
            'sender': obj.vote_sender,
            'Block_sender': obj.block_sender
        }
        signed = Sign.sign_message(node.privatekey, json.dumps(data))
        return json.dumps({
            'type': 'Block1',
            'data': data,
            'signature': signed,
            'public_key': base64_representation
        })
    elif isinstance(obj, Block2):
        data = {
            'sender': obj.vote_sender,
            'Block_sender': obj.block_sender,
            'QC_sender': obj.qc_sender
        }
        signed = Sign.sign_message(node.privatekey, json.dumps(data))
        return json.dumps({
            'type': 'Block2',
            'data': data,
            'signature': signed,
            'public_key': base64_representation
        })
    elif isinstance(obj, Vote1):
        data = {
            'sender': obj.vote_sender,
            'Block_sender': obj.block_sender
        }
        signed = Sign.sign_message(node.privatekey, json.dumps(data))
        return json.dumps({
            'type': 'Vote1',
            'data': data,
            #'signature': signed,
            'public_key': base64_representation
        })
    elif isinstance(obj, Vote2):
        data = {
            'sender': obj.vote_sender,
            'QC_sender': obj.qc_sender
        }
        signed = Sign.sign_message(node.privatekey, json.dumps(data))
        return json.dumps({
            'type': 'Vote2',
            'data': data,
            'signature': signed,
            'public_key': base64_representation
        })
    else :
        return json.dumps(obj.__dict__)
    

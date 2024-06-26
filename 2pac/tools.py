import socket
import threading
import time
import json
from com import Com
from data_struct import *
import base64
from sign import *

def handlemessage(message):
    pass

def start_com(node):
    com = Com(node)
    com.start()
    return com

def broadcast(com, message):
    com.broadcast_message(message)

    
def to_json(obj,node):
    base64_representation = base64.b64encode(node.publickey.encode()).decode('utf-8')
    if isinstance(obj, Block1):
        data = {
            'sender': obj.sender,
            'Block_sender': obj.block
        }
        return json.dumps({
            'type': 'Block1',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    elif isinstance(obj, Block2):
        data = {
            'sender': obj.sender,
            'Block_sender': obj.block,  
            'qc': obj.qc
        }
        return json.dumps({
            'type': 'Block2',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    elif isinstance(obj, Vote1):
        data = {
            'sender': obj.vote_sender,
            'Block_sender': obj.block_sender
        }
        return json.dumps({
            'type': 'Vote1',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    elif isinstance(obj, Vote2):
        data = {
            'sender': obj.vote_sender,
            'QC_sender': obj.qc_sender
        }
        return json.dumps({
            'type': 'Vote2',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    else :
        return json.dumps(obj.__dict__)
    

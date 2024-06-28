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

""" def start_com(node):
    com = Com(node.port, node.peers)
    com.start()
    return com """

def broadcast(com, message):
    com.broadcast_message(message)
    
def to_json(obj,node):
    base64_representation = base64.b64encode(node.publickey.encode()).decode('utf-8')
    if isinstance(obj, Block):
        data = {
            'sender': obj.sender,
        }
        return json.dumps({
            'type': 'Block',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    
    elif isinstance(obj, Echo):
        data = {
            'sender': obj.sender,
            'Block_sender': obj.block_sender
        }
        return json.dumps({
            'type': 'Echo',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    
    elif isinstance(obj, Ready):
        data = {
            'sender': obj.sender,
            'Block_sender': obj.block_sender
        }
        return json.dumps({
            'type': 'Ready',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    
    elif isinstance(obj, Elect):
        data = {
            'sender': obj.sender,
        }
        return json.dumps({
            'type': 'Elect',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    
    elif isinstance(obj, Leader):
        data = {
            'sender': obj.sender,
            'id_leader': obj.id_leader
        }
        return json.dumps({
            'type': 'Leader',
            'data': data,
            'signature': send_signed(data,node.privatekey),
            'public_key': base64_representation
        })
    else :
        return json.dumps(obj.__dict__)
    

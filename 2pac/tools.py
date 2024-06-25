import socket
import threading
import time
import json
from com import Com
from data_struct import *

def broadcast(message):
    pass


def handlemessage(message):
    pass


def start_com(node):
    com = Com(node)
    com.start()
    return com

def broadcast(com, message):
    if isinstance(message, Vote):
        com.broadcast_vote(message)
    elif isinstance(message, Block):
        com.broadcast_block(message)
    else:
        com.broadcast(message)
    

    

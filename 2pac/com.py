##fichier de communication
import socket
import threading
from data_struct import Node
from sign import *
import queue
import json

class Com:
    def __init__(self,node: Node , host = None, port = None, peers = None):
        #print("Node class initialized")
        self.host = 'localhost'
        self.port = node.port
        self.peers = node.peers
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.threads = []
        self.recv = queue.Queue()

    def start(self):
        #print(f"Node started at {self.host}:{self.port}")
        self.start_server()
        self.connect_to_peers()

    def start_server(self):
        #print(f"Server started at {self.host}:{self.port}")
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.start()
        self.threads.append(server_thread)

    def listen_for_connections(self):
        #print("Listening for connections...")
        self.sock.listen(5)
        while True:
            client_sock, _ = self.sock.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_sock,))
            client_thread.start()
            self.threads.append(client_thread)

    def connect_to_peers(self):
        #print("Connecting to peers...")
        for peer in self.peers:
            peer_thread = threading.Thread(target=self.connect_to_peer, args=(peer,))
            peer_thread.start()
            self.threads.append(peer_thread)

    def connect_to_peer(self, peer):
        #print(f"Connecting to peer {peer}")
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_sock.connect(peer)
            self.handle_client(peer_sock)
        except ConnectionRefusedError:
            print(f"Unable to connect to peer {peer}")

    def handle_client(self, client_sock):
        #print(f"Handling client {client_sock.getpeername()}")
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                
                message = json.loads(message)
                #self.show_message(message)
                self.recv.put(message)
                print(verify_signed(self.recv.get()["signature"]))
                print(f'recv of {self.port} :: {type(self.recv.get())}')
            except Exception as e:
                print(f"Error handling client: {e}")
                break

    def show_message(self, message):
        print(f"{self.port} :: Received message: {message}")

    def send_message(self, message, peer):
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_sock.connect(peer)
            peer_sock.sendall(message.encode('utf-8'))
            peer_sock.close()
        except ConnectionRefusedError:
            print(f"Unable to send message to peer {peer}")

    def broadcast_message(self, message):
        for peer in self.peers:
            self.send_message(message, peer)

    def stop(self):
        #print("Stopping node...")
        for thread in self.threads:
            thread.join()
        self.sock.close()




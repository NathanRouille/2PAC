import socket
import threading
import time
##from machin import Node 

class Node:
    def __init__(self, host, port, peers):
        #print("Node class initialized")
        self.host = host
        self.port = port
        self.peers = peers
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.threads = []

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
                self.handle_message(message)
            except Exception as e:
                print(f"Error handling client: {e}")
                break

    def handle_message(self, message):
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

# Example usage:

#peers = [('localhost', 5001), ('localhost', 5002), ('localhost', 5003)]
node_0 = Node('localhost', 5000, [('localhost', 5001), ('localhost', 5002), ('localhost', 5003)])
node_1 = Node('localhost', 5001, [('localhost', 5000), ('localhost', 5002), ('localhost', 5003)])
node_2 = Node('localhost', 5002, [('localhost', 5001), ('localhost', 5000), ('localhost', 5003)])
node_3 = Node('localhost', 5003, [('localhost', 5001), ('localhost', 5002), ('localhost', 5000)])
node_0.start()
node_1.start()
node_2.start()
node_3.start()

""" # To send a message to a peer:
node_0.broadcast_message("Hello, world!")

def wait_and_send():
    time.sleep(5)
    node_1.send_message("Hello again!", node_1.peers[0])
    node_0.stop()
    node_1.stop()
    node_2.stop()
    node_3.stop()

wait_and_send() """
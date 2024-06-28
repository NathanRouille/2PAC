##fichier de communication
import socket
import threading
from sign import *
import queue
import json
import time


class Com:
    """structure Com qui implémentera les fonctions de communication entre les noeuds du réseau"""
    def __init__(self,id = None, port = None, peers = None, delay = False):
        """initialisation de la classe Com"""
        #print("Node class initialized")
        self.id = id        #id du noeud
        self.host = 'localhost'     #adresse du noeud
        self.port = port        #port du noeud
        self.peers = peers      #pairs du noeud (adresses des noeuds avec qui il peut communiquer)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       #socket du noeud (utilisé pour la communication)
        self.sock.bind((self.host, self.port))      #liaison du socket à l'adresse et au port du noeud
        self.threads = []       #liste des threads du noeud
        self.recv = queue.Queue()       #file d'attente des messages reçus par le noeud
        self.delay = delay      #délai d'envoi des messages (booléen)

    def start(self):
        """fonction de démarrage du noeud"""
        #print(f"Node started at {self.host}:{self.port}")
        self.start_server()
        self.connect_to_peers()
        return self

    def start_server(self):
        """"fonction de démarrage du serveur du noeud"""
        #print(f"Server started at {self.host}:{self.port}")
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.start()
        self.threads.append(server_thread)

    def listen_for_connections(self):
        """fonction d'écoute des connexions entrantes"""
        #print("Listening for connections...")
        self.sock.listen(5)     # le socket peut gérer jusqu'à 5 connexions en attente simultanément avant de refuser ou de mettre en attente les connexions supplémentaires
        while True:     #boucle d'attente des connexions lorsqu'elles arrivent on crée un thread pour gérer le client
            client_sock, _ = self.sock.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_sock,))
            client_thread.start()
            self.threads.append(client_thread)

    def connect_to_peers(self):
        """fonction de connexion aux pairs du noeud"""
        #print("Connecting to peers...")
        for peer in self.peers:     #pour chaque pair du noeud on crée un thread pour se connecter à ce pair
            peer_thread = threading.Thread(target=self.connect_to_peer, args=(peer,))
            peer_thread.start()
            self.threads.append(peer_thread)

    def connect_to_peer(self, peer):
        """fonction de connexion à un pair du noeud"""
        #print(f"Connecting to peer {peer}")
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
        try:
            peer_sock.connect(peer)
            self.handle_client(peer_sock)
        except ConnectionRefusedError:
            print(f"Unable to connect to peer {peer}")

    def handle_client(self, client_sock):
        """fonction de gestion des clients connectés au noeud"""
        #print(f"Handling client {client_sock.getpeername()}")
        while True:
            try:    #on essaie de recevoir les données envoyées par le client et de les décoder
                data = client_sock.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                
                message = json.loads(message)
                #self.show_message(message)
                self.recv.put(message)
                """ print(f"id : {self.id}")
                print(f"recv: {self.recv}")
                print(verify_signed(self.recv.get()["signature"]))
                print(f'recv of {self.port} :: {type(self.recv.get())}') """
            except Exception as e:
                print(f"Error handling client: {e}")
                break

    def show_message(self, message):
        """fonction d'affichage des messages reçus par le noeud"""
        print(f"{self.port} :: Received message: {message}")

    def send_message(self, message, peer):
        """fonction d'envoi de message à un pair du noeud"""
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_sock.connect(peer)
            peer_sock.sendall(message.encode('utf-8'))
            peer_sock.close()
        except ConnectionRefusedError:
            print(f"Unable to send message to peer {peer}")

    def wait(self,message, duration):
        """fonction de temporisation de l'envoi de message à un pair du noeud"""
        time.sleep(duration)
        for peer in self.peers:
                self.send_message(message, peer)

    def broadcast_message(self, message):
        """fonction d'envoi de message à tous les pairs du noeud"""
        if not self.delay:
            delaying_thread = threading.Thread(target=self.wait, args=(message,0.4,)) #on crée un thread d'attente pour chaque pair du noeud
            delaying_thread.start()
        else:
            delaying_thread = threading.Thread(target=self.wait, args=(message,0.9,)) #on crée un thread d'attente pour chaque pair du noeud (délai plus élevé)
            delaying_thread.start()


    def stop(self):
        """fonction d'arrêt du noeud"""
        for thread in self.threads:
            thread.join()
        self.sock.close()




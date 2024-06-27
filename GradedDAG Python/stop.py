import socket
import threading

class Node:
    def __init__(self, host, port, peers):
        # Initialisation de la classe Node avec l'hôte, le port et les pairs
        self.host = host
        self.port = port
        self.peers = peers
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.threads = []

    def start(self):
        # Démarre le nœud en lançant le serveur et en se connectant aux pairs
        self.start_server()
        self.connect_to_peers()

    def start_server(self):
        # Démarre le serveur en écoutant les connexions entrantes
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.start()
        self.threads.append(server_thread)

    def listen_for_connections(self):
        # Écoute les connexions entrantes et crée un thread pour chaque client
        self.sock.listen(5)
        while True:
            client_sock, _ = self.sock.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_sock,))
            client_thread.start()
            self.threads.append(client_thread)

    def connect_to_peers(self):
        # Se connecte aux pairs en créant un thread pour chaque pair
        for peer in self.peers:
            peer_thread = threading.Thread(target=self.connect_to_peer, args=(peer,))
            peer_thread.start()
            self.threads.append(peer_thread)

    def connect_to_peer(self, peer):
        # Se connecte à un pair spécifique
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_sock.connect(peer)
            self.handle_client(peer_sock)
        except ConnectionRefusedError:
            print(f"Impossible de se connecter au pair {peer}")

    def handle_client(self, client_sock):
        # Gère les messages reçus d'un client spécifique
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                self.handle_message(message)
            except Exception as e:
                print(f"Erreur lors de la gestion du client : {e}")
                break

    def handle_message(self, message):
        # Gère un message reçu
        print(f"Message reçu : {message}")

    def send_message(self, message, peer):
        # Envoie un message à un pair spécifique
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_sock.connect(peer)
            peer_sock.sendall(message.encode('utf-8'))
            peer_sock.close()
        except ConnectionRefusedError:
            print(f"Impossible d'envoyer le message au pair {peer}")

    def stop(self):
        # Arrête le nœud en attendant la fin de tous les threads et en fermant la socket
        for thread in self.threads:
            thread.join()
        self.sock.close()

# Exemple d'utilisation :

# Définition des pairs
#peers = [('localhost', 5001), ('localhost', 5002), ('localhost', 5003)]

# Création des nœuds
node_0 = Node('localhost', 5000, [('localhost', 5001), ('localhost', 5002), ('localhost', 5003)])
node_1 = Node('localhost', 5001, [('localhost', 5000), ('localhost', 5002), ('localhost', 5003)])
node_2 = Node('localhost', 5002, [('localhost', 5001), ('localhost', 5000), ('localhost', 5003)])
node_3 = Node('localhost', 5003, [('localhost', 5001), ('localhost', 5002), ('localhost', 5000)])

# Démarrage des nœuds
""" node_0.start()
node_1.start()
node_2.start()
node_3.start()
 """

# Pour envoyer un message à un pair :
""" node_0.send_message("Bonjour, monde !", ('localhost', 5001)) """

# Arrêt des nœuds
node_0.stop()
node_1.stop()
node_2.stop()
node_3.stop()

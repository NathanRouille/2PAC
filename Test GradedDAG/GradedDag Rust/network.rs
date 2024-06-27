use std::io;
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use crate::node::{Node, Transport};

pub struct Transport {
    pub listener: TcpListener,
    pub connections: Vec<TcpStream>,
}

impl Node {
    /// Démarre l'écoute P2P sur le port spécifié dans le cluster.
    /// Cette fonction lie le listener TCP à l'adresse IP "0.0.0.0" et au port spécifié.
    /// Elle configure également le listener en mode non bloquant.
    /// Enfin, elle crée une instance de la structure `Transport` et la stocke dans le champ `trans` de `Node`.
    ///
    /// # Erreurs
    ///
    /// Cette fonction peut renvoyer une erreur si le port spécifié n'est pas trouvé dans le cluster.
    ///
    /// # Exemple
    ///
    /// ```
    /// # use std::io;
    /// # use std::net::TcpListener;
    /// # use std::sync::{Arc, Mutex};
    /// # use crate::node::{Node, Transport};
    /// let mut node = Node::new();
    /// node.StartP2PListen().unwrap();
    /// ```
    pub fn StartP2PListen(&mut self) -> io::Result<()> {
        let port = *self.cluster_port.get(&self.name).ok_or(io::Error::new(io::ErrorKind::Other, "Port not found"))?;
        let addr = format!("0.0.0.0:{}", port);
        let listener = TcpListener::bind(&addr)?;
        listener.set_nonblocking(true)?;
        
        self.trans = Some(Arc::new(Mutex::new(Transport {
            listener,
            connections: Vec::new(),
        })));
        
        Ok(())
    }
    
    /// Établit des connexions P2P avec tous les nœuds du cluster.
    /// Cette fonction itère sur tous les adresses IP et ports du cluster et établit une connexion TCP avec chaque nœud.
    /// Elle configure également un délai de lecture de 30 secondes pour chaque connexion.
    /// Enfin, elle stocke chaque connexion dans le champ `connections` de la structure `Transport`.
    ///
    /// # Erreurs
    ///
    /// Cette fonction peut renvoyer une erreur si `networkTransport` n'a pas été créé.
    ///
    /// # Exemple
    ///
    /// ```
    /// # use std::io;
    /// # use std::net::TcpStream;
    /// # use std::sync::{Arc, Mutex};
    /// # use std::time::Duration;
    /// # use crate::node::{Node, Transport};
    /// let mut node = Node::new();
    /// node.EstablishP2PConns().unwrap();
    /// ```
    pub fn EstablishP2PConns(&mut self) -> io::Result<()> {
        let trans = self.trans.as_ref().ok_or(io::Error::new(io::ErrorKind::Other, "networkTransport has not been created"))?.clone();
        
        for addr_with_port in &self.cluster_addr_with_ports {
            let stream = TcpStream::connect(addr_with_port.0)?;
            stream.set_read_timeout(Some(Duration::new(30, 0)))?;
            let trans_clone = Arc::clone(&trans);
            trans_clone.lock().unwrap().connections.push(stream.try_clone()?);
            self.logger.debug("connection has been established", &self.name, addr_with_port.0);
        }
        
        Ok(())
    }
}

fn main() {
    println!("Hello, world!");
}
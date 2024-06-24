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

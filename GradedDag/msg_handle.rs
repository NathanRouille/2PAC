
use std::sync::mpsc::{channel, Receiver};
use std::thread;
use std::sync::{Arc, Mutex};
use crossbeam_channel::{unbounded, Sender, Receiver};

impl Node {
    pub fn handle_msg_loop(&self) {
        let msg_ch = self.trans.msg_chan();
        loop {
            let msg_with_sig = match msg_ch.recv() {
                Ok(msg) => msg,
                Err(_) => continue,
            };
            if self.is_faulty {
                continue;
            }
            match msg_with_sig.msg {
                Message::Block(msg_asserted) => {
                    if !self.verify_sig_ed25519(&msg_asserted.sender, &msg_with_sig.msg, &msg_with_sig.sig) {
                        eprintln!("Erreur de vérification de la signature du bloc");
                        continue;
                    }
                    self.cbc.handle_block_msg(&msg_asserted);
                },
                Message::Elect(msg_asserted) => {
                    if !self.verify_sig_ed25519(&msg_asserted.sender, &msg_with_sig.msg, &msg_with_sig.sig) {
                        eprintln!("Erreur de vérification de la signature de l'élu");
                        continue;
                    }
                    self.handle_elect_msg(&msg_asserted);
                },
                Message::Ready(msg_asserted) => {
                    if !self.verify_sig_ed25519(&msg_asserted.ready_sender, &msg_with_sig.msg, &msg_with_sig.sig) {
                        eprintln!("Erreur de vérification de la signature du prêt");
                        continue;
                    }
                    self.cbc.handle_ready_msg(&msg_asserted);
                }, 
                Message::Done(msg_asserted) => {
                    if !self.verify_sig_ed25519(&msg_asserted.done_sender, &msg_with_sig.msg, &msg_with_sig.sig) {
                        eprintln!("Erreur de vérification de la signature du fait");
                        continue;
                    }
                    self.handle_done_msg(&msg_asserted);
                },
                Message::Vote(msg_asserted) => {
                    if !self.verify_sig_ed25519(&msg_asserted.vote_sender, &msg_with_sig.msg, &msg_with_sig.sig) {
                        eprintln!("Erreur de vérification de la signature du vote");
                        continue;
                    }
                    self.cbc.handle_vote_msg(&msg_asserted);
                },
            }                           
        }
    }
}

impl Node {
    pub fn handleCBCBlock(&self, block: Block) {
        let node_clone = self.clone();
        std::thread::spawn(move || {
            node_clone.tryToUpdateDAG(block);
        });
    }
}




impl Node {
    fn handle_cbc_block(&self, block: Arc<Block>) {
        let n = Arc::clone(self);
        thread::spawn(move || {
            n.try_to_update_dag(&block);
        });
    }

    fn handle_elect_msg(&self, elect: Arc<Elect>) {
        let _guard = self.lock.lock().unwrap();
        self.store_elect_msg(&elect);
        self.try_to_elect_leader(elect.round);
    }

    fn handle_done_msg(&self, done: Arc<Done>) {
        let _guard = self.lock.lock().unwrap();
        self.store_done(&done);
        let n = Arc::clone(self);
        thread::spawn(move || {
            n.try_to_next_round(done.round);
        });
        self.try_to_commit_leader(done.round);
    }

    fn cbc_output_block_loop(&self) {
        let (tx, rx) = unbounded::<Arc<Block>>();
        self.cbc.block_chan = tx;
        let n = Arc::clone(self);
        for block in rx {
            let logger = Arc::clone(&n.logger);
            let n = Arc::clone(&n);
            thread::spawn(move || {
                logger.debug(&format!("Block is received by from CBC, node: {}, round: {}, proposer: {}", n.name, block.round, block.sender));
                n.handle_cbc_block(block);
            });
        }
    }
    fn done_output_loop(&self) {
        let (tx, rx) = unbounded::<Arc<Done>>();
        self.cbc.done_chan = tx;
        let n = Arc::clone(self);
        for done in rx {
            let n = Arc::clone(&n);
            thread::spawn(move || {
                n.handle_done_msg(done);
            });
        }
    }
}

impl CBC {
    fn new() -> Self {
        let (block_tx, _block_rx) = unbounded::<Arc<Block>>();
        let (done_tx, _done_rx) = unbounded::<Arc<Done>>();
        CBC {
            block_chan: block_tx,
            done_chan: done_tx,
        }
    }
}

impl Logger {
    fn debug(&self, msg: &str) {
        println!("{}", msg);
    }
}
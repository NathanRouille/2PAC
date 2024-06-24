use ed25519_dalek::PrivateKey as Ed25519PrivateKey;
use std::collections::HashMap;
use std::sync::{RwLock, mpsc::Sender};
use threshold_crypto::{PublicKey as TcPublicKey, SecretKey as TcSecretKey};


use crate::data_struc::{Block, Done};

struct CBC {
    name: String,
    clusterAddrWithPorts: HashMap<String, u8>,
    connPool: NetworkTransport, // Assuming NetworkTransport is defined elsewhere
    nodeNum: i32,
    quorumNum: i32,
    pendingBlocks: HashMap<u64, HashMap<String, Block>>,
    pendingVote: HashMap<u64, HashMap<String, i32>>,
    pendingReady: HashMap<u64, HashMap<String, HashMap<String, Vec<u8>>>>,
    privateKey: Ed25519PrivateKey,
    tsPublicKey: TcPublicKey,
    tsPrivateKey: TcSecretKey,
    lock: RwLock<()>, // Using RwLock for thread-safe mutable access
    blockCh: Sender<Block>, // Assuming a channel for Block
    doneCh: Sender<Done>, // Assuming a channel for Done
    blockOutput: HashMap<u64, HashMap<String, bool>>,
    doneOutput: HashMap<u64, HashMap<String, bool>>,
    blockSend: HashMap<u64, bool>,
}

impl CBC {
    pub fn return_block_chan(&self) -> &Sender<Block> {
        &self.blockCh
    }

    pub fn return_done_chan(&self) -> &Sender<Done> {
        &self.doneCh
    }

    pub fn NewCBCer(
        name: String,
        cluster_addr_with_ports: HashMap<String, u8>,
        conn_pool: NetworkTransport, // Assuming NetworkTransport is a type defined elsewhere
        q: i32,
        n: i32,
        private_key: Ed25519PrivateKey, // Assuming Ed25519PrivateKey is a type defined elsewhere
        ts_public_key: TcPublicKey,
        ts_private_key: TcSecretKey,
    ) -> CBC {
        CBC {
            name,
            clusterAddrWithPorts: cluster_addr_with_ports,
            connPool: conn_pool,
            nodeNum: n,
            quorumNum: q,
            pendingBlocks: HashMap::new(),
            pendingVote: HashMap::new(),
            pendingReady: HashMap::new(),
            privateKey: private_key,
            tsPublicKey: ts_public_key,
            tsPrivateKey: ts_private_key,
            lock: RwLock::new(()), // Assuming RwLock is imported and () indicates a lock without a particular data type
            blockCh: channel::<Block>().0, // Assuming channel function is defined elsewhere and returns a tuple where .0 is the Sender
            doneCh: channel::<Done>().0, // Similar assumption as blockCh
            blockOutput: HashMap::new(),
            doneOutput: HashMap::new(),
            blockSend: HashMap::new(),
        }
    }

    pub fn BroadcastBlock(&self, block: &Block) {
        if let Err(err) = self.broadcast(ProposalTag, block) {
            panic!("{}", err);
        }
        let mut block_send = self.blockSend.write().unwrap(); // Assuming blockSend is wrapped in a RwLock
        block_send.insert(block.round, true);
    }

    pub fn BroadcastVote(&self, block_sender: String, round: u64) {
        let vote = Vote {
            vote_sender: self.name.clone(),
            block_sender,
            round,
        };
        if let Err(err) = self.broadcast(VoteTag, &vote) {
            panic!("{}", err);
        }
    }

    pub fn BroadcastReady(&self, round: u64, hash: Vec<u8>, block_sender: String) {
        let partial_sig = sign_ts_partial(&self.tsPrivateKey, &hash); // Assuming `sign_ts_partial` is a function that signs the hash with the threshold signature private key
        let ready = Ready {
            ready_sender: self.name.clone(),
            block_sender,
            round,
            hash,
            partial_sig,
        };
        if let Err(err) = self.broadcast(ReadyTag, &ready) {
            panic!("{}", err);
        }
    }

    pub fn HandleBlockMsg(&self, block: &Block) {
        {
            let _lock = self.lock.write().unwrap(); // Lock is acquired and automatically released at the end of the scope
            self.store_block_msg(block);
        } // Lock is released here due to the drop of _lock

        // Spawning asynchronous tasks for broadcasting vote and checking quorum
        let self_clone = self.clone();
        let block_clone = block.clone();
        std::thread::spawn(move || {
            self_clone.broadcast_vote(block_clone.sender.clone(), block_clone.round);
        });

        let self_clone = self.clone();
        let block_sender = block.sender.clone();
        let round = block.round;
        std::thread::spawn(move || {
            self_clone.check_if_quorum_vote(round, block_sender);
        });
    }

    pub fn HandleVoteMsg(&self, vote: &Vote) {
        {
            let _lock = self.lock.write().unwrap(); // Lock is acquired and automatically released at the end of the scope
            self.store_vote_msg(vote);
        } // Lock is released here

        // Spawning an asynchronous task for checking quorum vote
        let self_clone = self.clone();
        let vote_clone = vote.clone();
        std::thread::spawn(move || {
            self_clone.check_if_quorum_vote(vote_clone.round, vote_clone.block_sender.clone());
        });
    }

    pub fn handleReadyMsg(&self, ready: &Ready) {
        {
            let _lock = self.lock.write().unwrap(); // Lock is acquired and automatically released at the end of the scope
            self.store_ready_msg(ready);
        } // Lock is released here

        // Spawning an asynchronous task for checking quorum ready
        let self_clone = self.clone();
        let ready_clone = ready.clone();
        std::thread::spawn(move || {
            self_clone.check_if_quorum_ready(&ready_clone);
        });
    }

    pub fn storeBlockMsg(&self, block: &Block) {
        let mut pending_blocks = self.pendingBlocks.write().unwrap();
        pending_blocks.entry(block.round)
            .or_insert_with(HashMap::new)
            .insert(block.sender.clone(), block.clone());
    }

    pub fn storeVoteMsg(&self, vote: &Vote) {
        let mut pending_vote = self.pendingVote.write().unwrap();
        *pending_vote.entry(vote.round)
            .or_insert_with(HashMap::new)
            .entry(vote.block_sender.clone())
            .or_insert(0) += 1;
    }

    pub fn storeReadyMsg(&self, ready: &Ready) {
        let mut pending_ready = self.pendingReady.write().unwrap();
        pending_ready.entry(ready.round)
            .or_insert_with(HashMap::new)
            .entry(ready.block_sender.clone())
            .or_insert_with(HashMap::new)
            .insert(ready.ready_sender.clone(), ready.partial_sig.clone());
    }

    pub fn checkIfQuorumVote(&self, round: u64, block_sender: String) {
        let pending_vote = self.pendingVote.read().unwrap();
        if let Some(votes) = pending_vote.get(&round) {
            if let Some(&vote_count) = votes.get(&block_sender) {
                if vote_count >= self.quorumNum {
                    let self_clone = self.clone();
                    let block_sender_clone = block_sender.clone();
                    std::thread::spawn(move || {
                        self_clone.try_to_output_blocks(round, block_sender_clone);
                    });
                }
            }
        }
    }

    pub fn checkIfQuorumReady(&self, ready: &Ready) {
        let mut pending_ready = self.pendingReady.write().unwrap();
        let readies = pending_ready.get(&ready.round)
            .and_then(|sender_map| sender_map.get(&ready.block_sender))
            .cloned()
            .unwrap_or_default();

        let mut done_output = self.doneOutput.write().unwrap();
        if !done_output.entry(ready.round).or_insert_with(HashMap::new).contains_key(&ready.block_sender) && readies.len() >= self.quorumNum {
            done_output.get_mut(&ready.round).unwrap().insert(ready.block_sender.clone(), true);
            let partial_sig: Vec<Vec<u8>> = readies.values().cloned().collect();

            // Assuming `assemble_intact_ts_partial` is a function that assembles the partial signatures
            // let done = assemble_intact_ts_partial(&partial_sig, &self.tsPublicKey, &ready.hash, self.quorumNum, self.nodeNum);

            let done_msg = Done {
                done_sender: self.name.clone(),
                block_sender: ready.block_sender.clone(),
                done: partial_sig,
                hash: ready.hash.clone(),
                round: ready.round,
            };
            self.doneCh.send(done_msg).unwrap();
        }
    }

    pub fn tryToOutputBlocks(&self, round: u64, sender: String) {
        let mut block_output = self.blockOutput.write().unwrap();
        if block_output.entry(round).or_insert_with(HashMap::new).contains_key(&sender) {
            return;
        }

        let pending_blocks = self.pendingBlocks.read().unwrap();
        if let Some(block) = pending_blocks.get(&round).and_then(|sender_map| sender_map.get(&sender)) {
            block_output.get_mut(&round).unwrap().insert(sender.clone(), true);

            // Only send ready for odd blocks and not for slow blocks
            if round % 2 == 1 && !self.blockSend.read().unwrap().contains_key(&(round + 1)) {
                let hash = block.get_hash().unwrap(); // Assuming `get_hash` is a method that computes the hash of the block
                let self_clone = self.clone();
                let block_sender = block.sender.clone();
                std::thread::spawn(move || {
                    self_clone.broadcast_ready(round, hash, block_sender);
                });
            }
            self.blockCh.send(block.clone()).unwrap();
        }
    }

    pub fn broadcast(&self, msg_type: u8, msg: &impl Serialize) -> Result<(), Box<dyn Error>> {
        let msg_as_bytes = bincode::serialize(msg)?;
        let sig = self.sign_ed25519(&msg_as_bytes); // Assuming `sign_ed25519` is a method that signs the message

        for addr_with_port in &self.clusterAddrWithPorts {
            let mut net_conn = self.connPool.get_conn(addr_with_port)?; // Assuming `get_conn` is a method that retrieves a connection from the pool
            conn::send_msg(&mut net_conn, msg_type, &msg_as_bytes, &sig)?; // Assuming `send_msg` is a function that sends the message

            self.connPool.return_conn(net_conn)?; // Assuming `return_conn` is a method that returns the connection to the pool
        }
        Ok(())
    }
}
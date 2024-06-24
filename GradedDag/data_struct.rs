package gradeddag

use std::collections::HashMap;

pub struct Block {
    sender: String,
    round: u64,
    previous_hash: HashMap<String, Vec<u8>>, // au moins 2f+1 bloc au dernier tour, map de l'expéditeur à hash
    txs: Vec<Vec<u8>>,
    timestamp: i64,
}

pub struct Chain {
    round: u64,
    blocks: HashMap<String, Block>, // map de hash à bloc
}

pub struct Vote {
    vote_sender: String,
    block_sender: String,
    round: u64,
}

pub struct Ready {
    ready_sender: String,
    block_sender: String,
    round: u64,
    hash: Vec<u8>, // the block hash
    partial_sig: Vec<u8>,
}

pub struct Done {
    done_sender: String,
    block_sender: String,
    done: Vec<Vec<u8>>,
    hash: Vec<u8>,
    round: u64,
}

pub struct Elect {
    sender: String,
    round: u64,
    partial_sig: Vec<u8>,
}


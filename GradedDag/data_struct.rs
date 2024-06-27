package gradeddag

use std::collections::HashMap;

// Structure représentant un bloc
pub struct Block {
    sender: String, // L'expéditeur du bloc
    round: u64, // Le tour auquel le bloc appartient
    previous_hash: HashMap<String, Vec<u8>>, // Au moins 2f+1 blocs au dernier tour, map de l'expéditeur à hash
    txs: Vec<Vec<u8>>, // Les transactions contenues dans le bloc
    timestamp: i64, // Le timestamp du bloc
}

// Structure représentant une chaîne de blocs
pub struct Chain {
    round: u64,
    blocks: HashMap<String, Block>, // map de hash à bloc
}

// Structure représentant un vote
pub struct Vote {
    vote_sender: String, // L'expéditeur du vote
    block_sender: String, // L'expéditeur du bloc associé
    round: u64, // Le tour auquel le vote est envoyé
}

// Structure représentant un message "Ready"
pub struct Ready {
    ready_sender: String, // L'expéditeur du message "Ready"
    block_sender: String, // L'expéditeur du bloc associé
    round: u64, // Le tour auquel le message "Ready" est envoyé
    hash: Vec<u8>, // Le hash du bloc associé
    partial_sig: Vec<u8>, // La signature partielle du bloc
}

// Structure représentant un message
pub enum Message {
    Block(Block), // Un bloc
    Vote(Vote), // Un vote
    Ready(Ready), // Un message "Ready"
    Done(Done), // Un message "Done"
    Elect(Elect), // Un message "Elect"
}

// Structure représentant un message "Done"
pub struct Done {
    done_sender: String, // L'expéditeur du message "Done"
    block_sender: String, // L'expéditeur du bloc associé
    done: Vec<Vec<u8>>, // Les données du message "Done"
    hash: Vec<u8>, // Le hash du bloc associé
    round: u64, // Le tour auquel le message "Done" est envoyé
}

// Structure représentant un message "Elect"
pub struct Elect {
    sender: String, // L'expéditeur du message "Elect"
    round: u64, // Le tour auquel le message "Elect" est envoyé
    partial_sig: Vec<u8>, // La signature partielle du bloc
}

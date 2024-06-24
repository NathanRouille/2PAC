//ajouter ligne pour importer la structure node
//ajouter ligne pour importer la structure done et elect
use crate::conn::{SendMsg, TCPTransport};
use crate::sign::{AssembleIntactTSPartial, SignEd25519, SignTSPartial};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;

impl Node {
    pub fn broadcast_block(&mut self, round: u64) {
        let previous_hash = self.select_previous_blocks(round - 1);
        let block = self.new_block(round, previous_hash);
        self.cbc.broadcast_block(block);
    }

    pub fn broadcast_elect(&mut self, round: u64) {
        let data = round.to_be_bytes().to_vec();
        let partial_sig = SignTSPartial(&self.ts_private_key, &data);
        let elect = Elect {
            sender: self.name.clone(),
            round,
            partial_sig,
        };
        let err = self.broadcast(ElectTag, elect);
        if let Err(e) = err {
            panic!("{}", e);
        }
    }

    pub fn broadcast_done(&mut self, done: Done) {
        let done_msg = Done {
            done_sender: self.name.clone(),
            block_sender: done.block_sender,
            done: done.done,
            hash: vec![],
            round: done.round,
        };
        let err = self.broadcast(DoneTag, done_msg);
        if let Err(e) = err {
            panic!("{}", e);
        }
    }

    pub fn broadcast<T: Serialize>(&mut self, msg_type: u8, msg: T) -> Result<(), Box<dyn std::error::Error>> {
        let msg_as_bytes = bincode::serialize(&msg)?;
        let sig = SignEd25519(&self.private_key, &msg_as_bytes);
        for addr_with_port in self.cluster_addr_with_ports.values() {
            let net_conn = self.trans.as_mut().unwrap().get_conn(addr_with_port)?;
            SendMsg(net_conn, msg_type, msg, sig)?;
            self.trans.as_mut().unwrap().return_conn(net_conn)?;
        }
        Ok(())
    }
}


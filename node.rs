use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::time::SystemTime;

struct Node {
    name: String,
    dag: Arc<RwLock<HashMap<u64, HashMap<String, Block>>>>,
    pending_blocks: Arc<RwLock<HashMap<u64, HashMap<String, Block>>>>,
    chain: Chain,
    leader: Arc<RwLock<HashMap<u64, String>>>,
    done: Arc<RwLock<HashMap<u64, HashMap<String, Done>>>>,
    elect: Arc<RwLock<HashMap<u64, HashMap<String, Vec<u8>>>>>,
    round: u64,
    move_round: Arc<RwLock<HashMap<u64, i32>>>,
    logger: Logger,

    node_num: usize,
    quorum_num: usize,

    cluster_addr: HashMap<String, String>,
    cluster_port: HashMap<String, i32>,
    cluster_addr_with_ports: HashMap<String, u8>,
    is_faulty: bool,

    max_pool: usize,
    trans: NetworkTransport,
    batch_size: usize,
    round_number: u64,

    public_key_map: HashMap<String, ed25519_dalek::PublicKey>,
    private_key: ed25519_dalek::Keypair,

    ts_public_key: Option<share::PubPoly>,
    ts_private_key: Option<share::PriShare>,

    next_round: Arc<RwLock<Option<u64>>>,
    leader_elect: Arc<RwLock<HashMap<u64, bool>>>,

    evaluation: Arc<RwLock<Vec<i64>>>,
    commit_time: Arc<RwLock<Vec<i64>>>,
    cbc: Option<CBC>,
}

impl Node {
    // Crée une nouvelle instance de Node
    fn new(conf: &Config) -> Self {
        let chain = Chain {
            round: 0,
            blocks: HashMap::new(),
        };

        let mut block = Block {
            sender: "zhang".to_string(),
            round: 0,
            previous_hash: None,
            txs: None,
            timestamp: 0,
        };

        let hash = block.get_hash_as_string().unwrap();
        chain.blocks.insert(hash.clone(), block);

        let logger = Logger::new("GradedDAG-node", conf.log_level);

        Self {
            name: conf.name.clone(),
            dag: Arc::new(RwLock::new(HashMap::new())),
            pending_blocks: Arc::new(RwLock::new(HashMap::new())),
            chain,
            leader: Arc::new(RwLock::new(HashMap::new())),
            done: Arc::new(RwLock::new(HashMap::new())),
            elect: Arc::new(RwLock::new(HashMap::new())),
            round: 1,
            move_round: Arc::new(RwLock::new(HashMap::new())),
            logger,

            node_num: conf.cluster_addr.len(),
            quorum_num: ((2 * conf.cluster_addr.len() as f64) / 3.0).ceil() as usize,

            cluster_addr: conf.cluster_addr.clone(),
            cluster_port: conf.cluster_port.clone(),
            cluster_addr_with_ports: conf.cluster_addr_with_ports.clone(),
            is_faulty: conf.is_faulty,

            max_pool: conf.max_pool,
            trans: NetworkTransport::new(),
            batch_size: conf.batch_size,
            round_number: conf.round,

            public_key_map: conf.public_key_map.clone(),
            private_key: conf.private_key.clone(),

            ts_public_key: conf.ts_public_key.clone(),
            ts_private_key: conf.ts_private_key.clone(),

            next_round: Arc::new(RwLock::new(None)),
            leader_elect: Arc::new(RwLock::new(HashMap::new())),

            evaluation: Arc::new(RwLock::new(Vec::new())),
            commit_time: Arc::new(RwLock::new(Vec::new())),
            cbc: None,
        }
    }

    // Exécute la boucle principale du Node
    fn run_loop(&self) {
        let mut current_round = 1;
        let start = SystemTime::now();

        while current_round <= self.round_number {
            self.broadcast_block(current_round);
            if current_round % 2 == 0 {
                self.broadcast_elect(current_round);
            }

            let next_round = self.next_round.write().unwrap();
            if let Some(round) = *next_round {
                current_round = round;
            }
        }

        std::thread::sleep(std::time::Duration::from_secs(5));

        let end = self.commit_time.read().unwrap().last().cloned().unwrap_or_default();
        let past_time = (end - start.elapsed().unwrap().as_nanos() as i64) as f64 / 1e9;
        let block_num = self.evaluation.read().unwrap().len();
        let throughput = (block_num * self.batch_size) as f64 / past_time;

        let total_time: i64 = self.evaluation.read().unwrap().iter().sum();
        let latency = total_time as f64 / 1e9 / block_num as f64;

        self.logger.info("the average", latency, throughput);
        self.logger.info("the total commit", block_num, past_time);
    }

    // Initialise le CBC
    fn init_cbc(&mut self, conf: &Config) {
        self.cbc = Some(CBC::new(
            &self.name,
            &conf.cluster_addr_with_ports,
            &self.trans,
            self.quorum_num,
            self.node_num,
            &self.private_key,
            self.ts_public_key.clone().unwrap(),
            self.ts_private_key.clone().unwrap(),
        ));
    }

    // Sélectionne les blocs précédents pour un certain round
    fn select_previous_blocks(&self, round: u64) -> Option<HashMap<String, Vec<u8>>> {
        let mut dag = self.dag.write().unwrap();
        if round == 0 {
            return None;
        }
        let mut previous_hash = HashMap::new();
        if let Some(blocks) = dag.get(&round) {
            for (sender, block) in blocks {
                if let Ok(hash) = block.get_hash() {
                    previous_hash.insert(sender.clone(), hash);
                }
            }
        }
        Some(previous_hash)
    }

    // Stocke un bloc terminé
    fn store_done(&self, done: Done) {
        let mut done_map = self.done.write().unwrap();
        let round_done = done_map.entry(done.round).or_insert_with(HashMap::new);
        if round_done.insert(done.block_sender.clone(), done).is_none() {
            let mut move_round = self.move_round.write().unwrap();
            *move_round.entry(done.round).or_insert(0) += 1;
        }
    }

    // Stocke un message d'élection de leader
    fn store_elect_msg(&self, elect: Elect) {
        let mut elect_map = self.elect.write().unwrap();
        let round_elect = elect_map.entry(elect.round).or_insert_with(HashMap::new);
        round_elect.insert(elect.sender.clone(), elect.partial_sig);
    }

    // Stocke des blocs en attente
    fn store_pending_blocks(&self, block: Block) {
        let mut pending_blocks = self.pending_blocks.write().unwrap();
        let round_blocks = pending_blocks.entry(block.round).or_insert_with(HashMap::new);
        round_blocks.insert(block.sender.clone(), block);
    }

    // Tente d'élire un leader
    fn try_to_elect_leader(&self, round: u64) {
        let elect = self.elect.read().unwrap();
        if let Some(elect_map) = elect.get(&round) {
            if elect_map.len() >= self.quorum_num && !self.leader_elect.read().unwrap().contains_key(&round) {
                let mut leader_elect = self.leader_elect.write().unwrap();
                leader_elect.insert(round, true);
                drop(leader_elect);

                let partial_sigs: Vec<Vec<u8>> = elect_map.values().cloned().collect();
                let data = encode(&round).expect("Failed to encode round");

                let qc = sign::assemble_intact_ts_partial(&partial_sigs, self.ts_public_key.clone().unwrap(), &data, self.quorum_num, self.node_num);
                let qc_as_int = u32::from_be_bytes([qc[0], qc[1], qc[2], qc[3]]);
                let leader_id = (qc_as_int as usize) % self.node_num;
                let leader_name = format!("node{}", leader_id);

                let mut leader = self.leader.write().unwrap();
                leader.insert(round - 1, leader_name);
                drop(leader);

                self.try_to_commit_leader(round - 1);
            }
        }
    }

    // Tente de passer au prochain round
    fn try_to_next_round(&self, round: u64) {
        let mut round_lock = self.round.write().unwrap();
        if round != *round_lock {
            return;
        }
        let count = *self.move_round.read().unwrap().get(&round).unwrap_or(&0);
        if count >= self.quorum_num {
            *round_lock += 1;
            drop(round_lock);
            let next_round = self.next_round.clone();
            std::thread::spawn(move || {
                let mut next_round_lock = next_round.write().unwrap();
                *next_round_lock = Some(round + 1);
            });
            self.try_to_next_round(round + 1);
        }
    }

    // Tente de valider et de commettre un leader
    fn try_to_commit_leader(&self, round: u64) {
        if round <= self.chain.read().unwrap().round {
            return;
        }
        if let Some(leader) = self.leader.read().unwrap().get(&round) {
            if let Some(done_map) = self.done.read().unwrap().get(&round) {
                if done_map.contains_key(leader) {
                    if let Some(block) = self.dag.read().unwrap().get(&round).and_then(|r| r.get(leader)) {
                        self.try_to_commit_ancestor_leader(round);
                        let hash = block.get_hash_as_string().unwrap();
                        let mut chain = self.chain.write().unwrap();
                        chain.round = round;
                        chain.blocks.insert(hash.clone(), block.clone());
                        drop(chain);
                        self.logger.info("commit the leader block", &self.name, round, &block.sender);
                        let commit_time = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap().as_nanos() as i64;
                        let latency = commit_time - block.timestamp;
                        self.evaluation.write().unwrap().push(latency);
                        self.commit_ancestor_blocks(round);
                        self.commit_time.write().unwrap().push(commit_time);
                    }
                }
            }
        }
    }

    // Tente de valider et de commettre un leader ancêtre
    fn try_to_commit_ancestor_leader(&self, round: u64) {
        if round < 2 || round - 2 <= self.chain.read().unwrap().round {
            return;
        }
        let valid_leader = self.find_valid_leader(round);
        for i in (1..round).step_by(2) {
            if let Some(leader) = valid_leader.get(&i) {
                if let Some(block) = self.dag.read().unwrap().get(&i).and_then(|r| r.get(leader)) {
                    let hash = block.get_hash_as_string().unwrap();
                    let mut chain = self.chain.write().unwrap();
                    chain.round = i;
                    chain.blocks.insert(hash.clone(), block.clone());
                    drop(chain);
                    self.logger.info("commit the ancestor leader block", &self.name, i, &block.sender);
                    let commit_time = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap().as_nanos() as i64;
                    let latency = commit_time - block.timestamp;
                    self.evaluation.write().unwrap().push(latency);
                    self.commit_ancestor_blocks(i);
                }
            }
        }
    }

    // Trouve un leader valide pour un certain round
    fn find_valid_leader(&self, round: u64) -> HashMap<u64, String> {
        let mut temple_blocks: HashMap<u64, HashMap<String, Block>> = HashMap::new();
        let block = self.dag.read().unwrap().get(&round).and_then(|r| r.get(&self.leader.read().unwrap()[&round])).unwrap().clone();
        let hash = block.get_hash_as_string().unwrap();
        temple_blocks.entry(round).or_insert_with(HashMap::new).insert(hash.clone(), block.clone());

        let mut valid_leader = HashMap::new();
        let mut r = round;

        while r > 0 {
            let prev_round_blocks = temple_blocks.entry(r - 1).or_insert_with(HashMap::new);
            for block in temple_blocks[&r].values() {
                if block.round % 2 == 1 && block.sender == self.leader.read().unwrap()[&block.round] {
                    valid_leader.insert(block.round, block.sender.clone());
                }
                for sender in block.previous_hash.keys() {
                    let link_block = self.dag.read().unwrap().get(&(r - 1)).and_then(|round_blocks| round_blocks.get(sender)).unwrap().clone();
                    let link_hash = link_block.get_hash_as_string().unwrap();
                    prev_round_blocks.insert(link_hash, link_block);
                }
            }
            r -= 1;
            if r == 0 || r == self.chain.read().unwrap().round {
                break;
            }
        }
        valid_leader
    }

    // Commit les blocs ancêtres
    fn commit_ancestor_blocks(&self, round: u64) {
        let mut temple_blocks: HashMap<u64, HashMap<String, Block>> = HashMap::new();
        let block = self.dag.read().unwrap()
            .get(&round)
            .and_then(|r| r.get(&self.leader.read().unwrap()[&round]))
            .unwrap().clone();
        let hash = block.get_hash_as_string().unwrap();
        temple_blocks.entry(round).or_insert_with(HashMap::new).insert(hash.clone(), block.clone());

        let mut r = round;
        while r > 0 {
            let prev_round_blocks = temple_blocks.entry(r - 1).or_insert_with(HashMap::new);
            for (hash, block) in temple_blocks[&r].iter() {
                if !self.chain.read().unwrap().blocks.contains_key(hash) {
                    self.chain.write().unwrap().blocks.insert(hash.clone(), block.clone());
                    let commit_time = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap().as_nanos() as i64;
                    let latency = commit_time - block.timestamp;
                    self.evaluation.write().unwrap().push(latency);
                }
                for sender in block.previous_hash.keys() {
                    if let Some(link_block) = self.dag.read().unwrap()
                        .get(&(r - 1))
                        .and_then(|round_blocks| round_blocks.get(sender))
                    {
                        let link_hash = link_block.get_hash_as_string().unwrap();
                        if !self.chain.read().unwrap().blocks.contains_key(&link_hash) {
                            prev_round_blocks.insert(link_hash, link_block.clone());
                        }
                    }
                }
            }
            if prev_round_blocks.is_empty() {
                break;
            }
            r -= 1;
        }
    }

    // Vérifie la signature ED25519
    fn verify_sig_ed25519(&self, peer: &str, data: &impl Serialize, sig: &[u8]) -> bool {
        if let Some(pub_key) = self.public_key_map.get(peer) {
            match bincode::serialize(data) {
                Ok(data_as_bytes) => {
                    match ed25519_dalek::Signature::from_bytes(sig) {
                        Ok(signature) => pub_key.verify(&data_as_bytes, &signature).is_ok(),
                        Err(_) => {
                            self.logger.error("fail to verify the ED25519 signature");
                            false
                        }
                    }
                }
                Err(_) => {
                    self.logger.error("fail to encode the data");
                    false
                }
            }
        } else {
            self.logger.error("node is unknown", peer);
            false
        }
    }

    // Vérifie si le Node est défectueux
    fn is_faulty_node(&self) -> bool {
        self.is_faulty
    }

    // Crée un nouveau bloc
    fn new_block(&self, round: u64, previous_hash: HashMap<String, Vec<u8>>) -> Block {
        let mut batch = Vec::new();
        let tx = generate_tx(20);
        for _ in 0..self.batch_size {
            batch.push(tx.clone());
        }
        let timestamp = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).unwrap().as_nanos() as i64;
        Block {
            sender: self.name.clone(),
            round,
            previous_hash,
            txs: batch,
            timestamp,
        }
    }

    // Vérifie si un bloc peut être ajouté au DAG
    fn check_whether_can_add_to_dag(&self, block: &Block) -> bool {
        let dag = self.dag.read().unwrap();
        let link_hash = &block.previous_hash;
        for sender in link_hash.keys() {
            if !dag.contains_key(&(block.round - 1)) || !dag[&(block.round - 1)].contains_key(sender) {
                return false;
            }
        }
        true
    }

    // Tente de mettre à jour le DAG avec un bloc donné
    fn try_to_update_dag(&self, block: Block) {
        let can_add = self.check_whether_can_add_to_dag(&block);
        if can_add {
            {
                let mut dag = self.dag.write().unwrap();
                let round_blocks = dag.entry(block.round).or_insert_with(HashMap::new);
                round_blocks.insert(block.sender.clone(), block.clone());
            }

            if block.round % 2 == 0 {
                let mut move_round = self.move_round.write().unwrap();
                *move_round.entry(block.round).or_insert(0) += 1;
                drop(move_round);
                self.try_to_next_round(block.round);
            } else {
                self.try_to_commit_leader(block.round);
            }

            self.try_to_update_dag_from_pending(block.round + 1);
        } else {
            self.store_pending_blocks(block);
        }
    }

    // Tente de mettre à jour le DAG à partir des blocs en attente
    fn try_to_update_dag_from_pending(&self, round: u64) {
        let mut pending_blocks = self.pending_blocks.write().unwrap();
        if let Some(round_blocks) = pending_blocks.get(&round) {
            let blocks_to_update: Vec<Block> = round_blocks.values().cloned().collect();
            drop(pending_blocks);

            for block in blocks_to_update {
                self.try_to_update_dag(block);
            }
        }
    }
}


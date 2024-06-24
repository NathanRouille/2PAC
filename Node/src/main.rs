use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use log::{info, warn};
use ed25519::{PublicKey, PrivateKey};
use kyber::share::{PubPoly, PriShare};
use reflect::Type;
use tokio::sync::mpsc;
use crate::conn::NetworkTransport;
use crate::sign;
use crate::config;

struct Node {
    name: String,
    lock: Arc<RwLock<()>>,
    dag: HashMap<u64, HashMap<String, Block>>,
    pending_blocks: HashMap<u64, HashMap<String, Block>>,
    chain: Chain,
    leader: HashMap<u64, String>,
    done: HashMap<u64, HashMap<String, Done>>,
    elect: HashMap<u64, HashMap<String, Vec<u8>>>,
    round: u64,
    move_round: HashMap<u64, i32>,
    logger: Logger,
    node_num: usize,
    quorum_num: usize,
    cluster_addr: HashMap<String, String>,
    cluster_port: HashMap<String, i32>,
    cluster_addr_with_ports: HashMap<String, u8>,
    is_faulty: bool,
    max_pool: usize,
    trans: Arc<NetworkTransport>,
    batch_size: usize,
    round_number: u64,
    public_key_map: HashMap<String, PublicKey>,
    private_key: PrivateKey,
    ts_public_key: PubPoly,
    ts_private_key: PriShare,
    reflected_types_map: HashMap<u8, Type>,
    next_round: mpsc::Sender<u64>,
    leader_elect: HashMap<u64, bool>,
    evaluation: Vec<i64>,
    commit_time: Vec<i64>,
    cbc: CBC,
}

fn new_node(conf: &config::Config) -> Node {
    let mut n = Node {
        name: conf.name.clone(),
        lock: Arc::new(RwLock::new(())),
        dag: HashMap::new(),
        pending_blocks: HashMap::new(),
        chain: Chain::new(),
        leader: HashMap::new(),
        done: HashMap::new(),
        elect: HashMap::new(),
        round: 1,
        move_round: HashMap::new(),
        logger: Logger::new("GradedDAG-node".to_string()),
        node_num: conf.node_num,
        quorum_num: conf.quorum_num,
        cluster_addr: conf.cluster_addr.clone(),
        cluster_port: conf.cluster_port.clone(),
        cluster_addr_with_ports: conf.cluster_addr_with_ports.clone(),
        is_faulty: conf.is_faulty,
        max_pool: conf.max_pool,
        trans: Arc::new(NetworkTransport::new(conf.network_config.clone())),
        batch_size: conf.batch_size,
        round_number: conf.round_number,
        public_key_map: conf.public_key_map.clone(),
        private_key: conf.private_key.clone(),
        ts_public_key: conf.ts_public_key.clone(),
        ts_private_key: conf.ts_private_key.clone(),
        reflected_types_map: reflected_types_map(),
        next_round: mpsc::channel(1).0,
        leader_elect: HashMap::new(),
        evaluation: Vec::new(),
        commit_time: Vec::new(),
        cbc: CBC::new(conf.cbc_config.clone()),
    };

    // Initialise la chaîne avec le bloc genèse
    let genesis_block = Block::new(
        "zhang".to_string(),
        0,
        vec![],
        vec![],
        0,
    );
    let genesis_hash = genesis_block.get_hash_as_string();
    n.chain.blocks.insert(genesis_hash.clone(), genesis_block);

    // Initialise les autres champs de la structure Node
    n.leader = HashMap::new();
    n.done = HashMap::new();
    n.elect = HashMap::new();
    n.move_round = HashMap::new();
    n.cluster_addr = conf.cluster_addr.clone();
    n.cluster_port = conf.cluster_port.clone();
    n.cluster_addr_with_ports = conf.cluster_addr_with_ports.clone();
    n.node_num = n.cluster_addr.len();
    n.quorum_num = (2 * n.node_num + 1) / 3;
    n.is_faulty = conf.is_faulty;
    n.max_pool = conf.max_pool;
    n.batch_size = conf.batch_size;
    n.round_number = conf.round as u64;
    n.public_key_map = conf.public_key_map.clone();
    n.private_key = conf.private_key.clone();
    n.ts_private_key = conf.ts_private_key.clone();
    n.ts_public_key = conf.ts_public_key.clone();
    n.reflected_types_map = reflected_types_map();
    n.next_round = mpsc::channel(1).0;
    n.leader_elect = HashMap::new();

    return n;
}

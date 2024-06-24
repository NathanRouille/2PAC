use sha2::{Digest, Sha256};
use serde::{Serialize, Deserialize};
use serde_json;
use rand::Rng;

fn main(){

}

// Calcule le hash SHA-256 d'un vecteur de bytes
fn gen_msg_hash_sum(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().to_vec()
}

// Encode les données en JSON
fn encode<T: Serialize>(data: T) -> Result<Vec<u8>, serde_json::Error> {
    serde_json::to_vec(&data)
}

// Décode les données JSON en une structure de données Rust
use serde::de::DeserializeOwned;

fn decode<T: DeserializeOwned>(s: Vec<u8>) -> Result<T, serde_json::Error> {
    serde_json::from_slice(&s).map_err(|e| e.into())
}


// Structure de bloc
#[derive(Serialize, Deserialize)]
struct Block {
    // ...
}

impl Block {
    // Calcule le hash du bloc
    fn get_hash(&self) -> Result<Vec<u8>, serde_json::Error> {
        let encoded_block = encode(self)?;
        Ok(gen_msg_hash_sum(&encoded_block))
    }

    // Calcule le hash du bloc et le retourne sous forme de chaîne hexadécimale
    fn get_hash_as_string(&self) -> Result<String, serde_json::Error> {
        let hash = self.get_hash()?;
        Ok(hex::encode(hash))
    }
}

// Génère une transaction aléatoire de taille s
fn generate_tx(s: usize) -> Vec<u8> {
    let mut rng = rand::thread_rng();
    (0..s).map(|_| rng.gen_range(0..200)).collect()
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gen_msg_hash_sum() {
        let data = b"hello world";
        let hash = gen_msg_hash_sum(data);
        let expected_hash = hex::decode("b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9").unwrap();
        assert_eq!(hash, expected_hash);
    }

    #[test]
    fn test_encode_decode() {
        let data = vec![1, 2, 3, 4, 5];
        let encoded = encode(data.clone()).unwrap();
        let decoded: Vec<u8> = decode(encoded).unwrap();
        assert_eq!(data, decoded);
    }

    #[test]
    fn test_block_get_hash() {
        let block = Block { /* ... */ };
        let hash = block.get_hash().unwrap();
        let expected_hash = hex::decode("...").unwrap();
        assert_eq!(hash, expected_hash);
    }

    #[test]
    fn test_block_get_hash_as_string() {
        let block = Block { /* ... */ };
        let hash_str = block.get_hash_as_string().unwrap();
        let expected_hash_str = "...";
        assert_eq!(hash_str, expected_hash_str);
    }

    #[test]
    fn test_generate_tx() {
        let tx = generate_tx(10);
        assert_eq!(tx.len(), 10);
        for byte in tx {
            assert!(byte < 200);
        }
    }
}

import hashlib
import json
import random
import time
import binascii
from data_struct import *

def gen_msg_hash_sum(data):
    try:
        msg_hash = hashlib.sha256()
        msg_hash.update(data)
        return msg_hash.digest(), None
    except Exception as e:
        return None, e


def encode(data):
    try:
        return json.dumps(data).encode(), None
    except Exception as e:
        return None, e


def decode(data, data_type):
    try:
        return json.loads(data, object_hook=lambda d: data_type(**d)), None
    except Exception as e:
        return None, e


class Block:
    def __init__(self, sender, round, previous_hash, txs, timestamp):
        self.sender = sender
        self.round = round
        self.previous_hash = previous_hash
        self.txs = txs
        self.timestamp = timestamp

    def to_serializable(self):
        # Convert bytes objects to hex strings for JSON serialization
        serializable_dict = {
            "sender": self.sender,
            "round": self.round,
            "previous_hash": {k: v.hex() for k, v in self.previous_hash.items()},
            "txs": [tx.hex() for tx in self.txs],
            "timestamp": self.timestamp
        }
        return serializable_dict

    def get_hash(self):
        encoded_block, err = encode(self.to_serializable())
        if err is not None:
            return None, err
        return gen_msg_hash_sum(encoded_block)

    def get_hash_as_string(self):
        hash_value, err = self.get_hash()
        if err is not None:
            return "", err
        return binascii.hexlify(hash_value).decode(), None


def generate_tx(s):
    random.seed(time.time())
    return bytes(random.randint(0, 199) for _ in range(s))


# Tests
def test_gen_msg_hash_sum():
    data = b"test data"
    hash_sum, err = gen_msg_hash_sum(data)
    assert err is None, f"Error: {err}"
    assert hash_sum is not None, "Hash sum is None"
    print("test_gen_msg_hash_sum passed")


def test_encode_decode():
    data = {"key": "value"}
    encoded_data, err = encode(data)
    assert err is None, f"Error: {err}"
    assert encoded_data is not None, "Encoded data is None"

    decoded_data, err = decode(encoded_data, dict)
    assert err is None, f"Error: {err}"
    assert decoded_data == data, "Decoded data does not match original"
    print("test_encode_decode passed")


def test_block():
    sender = "Alice"
    round = 1
    previous_hash = {"Bob": b"previous_hash"}
    txs = [generate_tx(10) for _ in range(5)]
    timestamp = int(time.time())

    block = Block(sender, round, previous_hash, txs, timestamp)

    hash_as_string, err = block.get_hash_as_string()
    assert err is None, f"Error: {err}"
    assert hash_as_string is not None, "Hash as string is None"
    print("test_block passed")


def test_generate_tx():
    tx = generate_tx(10)
    assert len(tx) == 10, "Transaction length does not match"
    print("test_generate_tx passed")


if __name__ == "__main__":
    test_gen_msg_hash_sum()
    test_encode_decode()
    test_block()
    test_generate_tx()

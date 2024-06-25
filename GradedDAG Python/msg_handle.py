##############         IMPORTS         ##############
#####################################################
# Importer les bibliothèques nécessaires

import asyncio
from asyncio import Queue
from threading import Lock
##############         CLASSES         ##############
#####################################################
class Node:
    def __init__(self, trans, cbc, logger, name):
        self.trans = trans
        self.cbc = cbc
        self.logger = logger
        self.name = name
        self.is_faulty = False
        self.lock = Lock()
    
    async def handle_msg_loop(self):
        msg_ch = self.trans.msg_chan()
        while True:
            msg_with_sig = await msg_ch.get()
            if self.is_faulty:
                continue
            
            msg_asserted = msg_with_sig['msg']
            if isinstance(msg_asserted, Block):
                if not self.verify_sig_ed25519(msg_asserted.sender, msg_with_sig['msg'], msg_with_sig['sig']):
                    self.logger.error("fail to verify the block's signature", round=msg_asserted.round, sender=msg_asserted.sender)
                    continue
                asyncio.create_task(self.cbc.handle_block_msg(msg_asserted))
            
            elif isinstance(msg_asserted, Elect):
                if not self.verify_sig_ed25519(msg_asserted.sender, msg_with_sig['msg'], msg_with_sig['sig']):
                    self.logger.error("fail to verify the echo's signature", round=msg_asserted.round, sender=msg_asserted.sender)
                    continue
                asyncio.create_task(self.handle_elect_msg(msg_asserted))
            
            elif isinstance(msg_asserted, Ready):
                if not self.verify_sig_ed25519(msg_asserted.ready_sender, msg_with_sig['msg'], msg_with_sig['sig']):
                    self.logger.error("fail to verify the ready's signature", round=msg_asserted.round, sender=msg_asserted.ready_sender, block_sender=msg_asserted.block_sender)
                    continue
                asyncio.create_task(self.cbc.handle_ready_msg(msg_asserted))
            
            elif isinstance(msg_asserted, Done):
                if not self.verify_sig_ed25519(msg_asserted.done_sender, msg_with_sig['msg'], msg_with_sig['sig']):
                    self.logger.error("fail to verify the done's signature", round=msg_asserted.round, sender=msg_asserted.done_sender, block_sender=msg_asserted.block_sender)
                    continue
                asyncio.create_task(self.handle_done_msg(msg_asserted))
            
            elif isinstance(msg_asserted, Vote):
                if not self.verify_sig_ed25519(msg_asserted.vote_sender, msg_with_sig['msg'], msg_with_sig['sig']):
                    self.logger.error("fail to verify the vote's signature", round=msg_asserted.round, sender=msg_asserted.vote_sender, block_sender=msg_asserted.block_sender)
                    continue
                asyncio.create_task(self.cbc.handle_vote_msg(msg_asserted))
    
    async def handle_cbc_block(self, block):
        asyncio.create_task(self.try_to_update_dag(block))
    
    async def handle_elect_msg(self, elect):
        with self.lock:
            self.store_elect_msg(elect)
            self.try_to_elect_leader(elect.round)
    
    async def handle_done_msg(self, done):
        with self.lock:
            self.store_done(done)
        asyncio.create_task(self.try_to_next_round(done.round))
        self.try_to_commit_leader(done.round)
    
    async def cbc_output_block_loop(self):
        data_ch = self.cbc.return_block_chan()
        while True:
            block = await data_ch.get()
            self.logger.debug("Block is received by from CBC", node=self.name, round=block.round, proposer=block.sender)
            asyncio.create_task(self.handle_cbc_block(block))
    
    async def done_output_loop(self):
        data_ch = self.cbc.return_done_chan()
        while True:
            done = await data_ch.get()
            asyncio.create_task(self.handle_done_msg(done))
            # make sure every node can get 2f+1 done
            await asyncio.sleep(1)
            
import json


class Node:
    def __init__(self, block_chain):
        self.version = len(block_chain)
        self.block_chain = block_chain
        self.tx_pool = []

    def read_command(self, encode_message):
        message = self.decode(encode_message)
        if 'command' not in message.keys():
            return
        command = message['command']
        payload = message['payload']
        if command == 0x00:
            self.compare_version(payload)
            return
        if command == 0x01:
            self.complete_hashes(payload)
            return
        if command == 0x02:
            self.complete_block_chain(payload)
            return
        if command == 0x03:
            self.send_data(payload)
            return
        if command == 0x04:
            self.add_block(payload)
            return
        if command == 0x05:
            self.add_new_tx(payload)
            return
        if command == 0x06:
            self.add_new_block(payload)
            return

    # Logic functions for commands
    def compare_version(self, version):
        if version <= self.version:
            return
        else:
            return self.send_hashes()

    def complete_block_chain(self, miss_hashes):
        for hash_block in miss_hashes:
            self.get_data(hash_block)
        return

    def add_block(self, block):
        self.block_chain.append(block)
        self.version = len(self.block_chain)
        return

    def add_new_tx(self, tx):
        self.tx_pool.append(tx)
        return

    def add_new_block(self, block):
        self.block_chain.append(block)
        self.tx_pool = []
        self.version = len(self.block_chain)
        return

    # Set messages types
    def send_version(self):
        return self.create_msg(0x00, self.version)

    def send_hashes(self):
        hashes = []
        for block in self.block_chain:
            hashes.append(hash(str(block)))
        return self.create_msg(0x01, hashes)

    def complete_hashes(self, hashes):
        miss_hashes = []
        for block in self.block_chain:
            if hash(str(block)) not in hashes:
                miss_hashes.append(hash(str(block)))
        return self.create_msg(0x02, miss_hashes)

    def get_data(self, hash_data):
        return self.create_msg(0x03, hash_data)

    def send_data(self, hash_data):
        search_block = None
        for block in self.block_chain:
            if hash(str(block)) == hash_data:
                search_block = block
        return self.create_msg(0x04, search_block)

    def create_tx(self, value):
        tx = {
            'type': 'transaction',
            'id': '',
            'value': value
        }
        tx['id'] = hash(str(tx))
        self.tx_pool.append(tx)
        return self.create_msg(0x05, tx)

    def create_block(self):
        if len(self.block_chain) == 0:
            block = {
                'type': 'block',
                'prev_block': '',
                'transactions': self.tx_pool
            }
        else:
            prev_block = self.block_chain[-1]
            block = {
                'type': 'block',
                'prev_block': hash(str(prev_block)),
                'transactions': self.tx_pool
            }
        self.tx_pool = []
        self.block_chain.append(block)
        self.version = len(self.block_chain)
        return self.create_msg(0x06, block)

    def verify_block_chain(self):
        if len(self.block_chain) < 2:
            return
        first_block = self.block_chain[0]
        for block in self.block_chain[1:]:
            if block['prev_block'] == hash(str(first_block)):
                print('True')
            first_block = block

    # Message Format
    def create_msg(self, command, payload):
        message = {'command': command, 'payload': payload}
        return self.encode(message)

    # Function for bytes communication
    @staticmethod
    def decode(data):
        return json.loads(data.decode(encoding='utf-8'))

    @staticmethod
    def encode(data):
        return bytes(json.dumps(data), encoding='utf-8')


if __name__ == "__main__":
    # TODO socket communication
    n = Node([])

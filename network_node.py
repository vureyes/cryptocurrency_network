import sys
import asyncio
import json
import hashlib
from aioconsole import ainput


def hash_256(data):
    return hashlib.sha256(bytes(json.dumps(data), encoding='utf-8')).digest().hex()


class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')


def node_print(msg):  # Beauty printing
    print("\r"+msg + "\n<:3)~ ", end="")


class Node:
    def __init__(self, host, port):
        # Host y Port en donde va a correr el servidor
        self.host = host
        self.port = port
        # Host y Port del nodo al que se quiere conectar
        self.ref_host = None
        self.ref_port = None

        self.server = None
        self.connections = []  # Informacion de los nodos que se encuentran conectados a este

        self.version = 1
        genesis_block = {
            'type': 'block',
            'prev_block': '',
            'transactions': []
        }
        self.block_chain = [genesis_block]  # En el blockchain se referencia al ultimo
        self.tx_pool = []  # Un pool de transacciones conocidas que no se encuentran en el blockchain
        self.miss_hashes = []

        self.sync_lock = False
        self.last_message = ''

    def run(self):
        # Obtener el loop de funciones asincornas
        loop = asyncio.get_event_loop()
        # Crear el task que se encarga de el servidor
        server_task = loop.create_task(self.server_init(self.host, self.port))
        # Inicia la interfaz de interaccion con el nodo
        prompt_task = loop.create_task(self.prompt_init())
        # It never ends
        loop.run_forever()

    def set_reference(self, host, port):  # Setea los datos del nodo al que se va a conectar / Delete
        self.ref_host = host
        self.ref_port = port

    def save_connection(self, reader, writer):  # Genera el objeto de conexion para cada nodo conectado
        new_connection = Connection(reader, writer)
        self.connections.append(new_connection)
        node_print(f'Connected to {new_connection.address!r}')
        new_connection.writer.write(self.send_version())

    async def spread_message(self, msg, addr):
        node_print(f"Spread: {msg!r}")
        for conn in self.connections:
            node_print(f"Trying to spread to {conn.address!r}")
            if conn.address != addr:
                node_print(f"Spreading to {conn.address!r}")
                conn.writer.write(msg.encode())
                await conn.writer.drain()

    async def spread_signal(self, msg, addr):
        for conn in self.connections:
            # node_print(f"Trying to spread to {conn.address!r}")
            if conn.address != addr:
                # node_print(f"Spreading to {conn.address!r}")
                conn.writer.write(msg)
                await conn.writer.drain()

    async def server_init(self, host, port):  # Inicia el servidor que acepta conexiones de nuevos nodos
        # Se inicia el servidor en la direccion (host,port)
        # Ejecuta la funcion handle_conection cuando recibe una nueva conexion
        self.server = await asyncio.start_server(self.handle_connection, host, port) 

        # Mostar que se inicio el servidor correctamente
        addr = self.server.sockets[0].getsockname()
        node_print(f'Serving on {addr}')

    async def handle_connection(self, reader, writer):
        # Guardar conexiones para ser usadas
        self.save_connection(reader, writer)
        addr = writer.get_extra_info('peername')
        # Mantenerse escuchando
        while True:
            data = await reader.read(2048)
            message = data.decode()
            if message == "":
                break
            await self.read_command(data)
            # Enviar mensaje a todos los otros nodos que estan conectados
            # await self.spread_message(message, addr)

        node_print(f"Closed connection from {addr!r}")
        writer.close()

    async def new_connection(self, host, port):  # Inicia la conexion que le permite entrar a la red
        reader, writer = await asyncio.open_connection(host, port)
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.handle_connection(reader, writer))
    
    async def prompt_init(self):
        while True:
            prompt = await ainput("\r<:3)~ ")  # Input que no bloquea el resto de la ejecucion
            cmd = prompt.strip().split(' ')
            if cmd[0] == 'show':
                print(f'MSG: {self.last_message!r}')
            elif cmd[0] == 's':
                print(self.version)
                print(self.block_chain)
                print(self.tx_pool)
            elif cmd[0] == 'c':
                if len(cmd) == 3:
                    host = cmd[1]
                    port = int(cmd[2])
                    await self.new_connection(host, port)
                else:
                    print("For new connection use command: c <host> <port>")
                
            elif cmd[0] == 't':
                value = cmd[1]
                await self.spread_signal(self.create_tx(value), None)
                print("Creating transaction")
            elif cmd[0] == 'b':
                await self.spread_signal(self.create_block(), None)
                print("Creating block")
            else:
                await self.spread_message(prompt, None)

    async def read_command(self, encode_message):
        print(encode_message)
        message = self.decode(encode_message)
        if 'command' not in message.keys():
            return
        command = message['command']
        payload = message['payload']
        # print(message)
        if command == 0x00:
            await self.compare_version(payload)
            return
        if command == 0x01:
            await self.spread_signal(self.complete_hashes(payload), None)
            return
        if command == 0x02:
            await self.complete_block_chain(payload)
            return
        if command == 0x03:
            await self.spread_signal(self.send_data(payload), None)
            return
        if command == 0x04:
            await self.add_block(payload)
            return
        if command == 0x05:
            self.add_new_tx(payload)
            return
        if command == 0x06:
            self.add_new_block(payload)
            return

    # Logic functions for commands
    async def compare_version(self, version):
        if version <= self.version:
            return
        else:
            await self.spread_signal(self.send_hashes(), None)

    async def complete_block_chain(self, miss_hashes):
        if len(miss_hashes) > 0:
            self.miss_hashes = miss_hashes
            next_hash = self.miss_hashes.pop(0)
            await self.spread_signal(self.get_data(next_hash), None)
        return

    async def add_block(self, block):
        self.block_chain.append(block)
        self.version = len(self.block_chain)
        if len(self.miss_hashes) > 0:
            next_hash = self.miss_hashes.pop(0)
            await self.spread_signal(self.get_data(next_hash), None)
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
            hashes.append(hash_256(block))
        return self.create_msg(0x01, hashes)

    def complete_hashes(self, hashes):
        miss_hashes = []
        for block in self.block_chain:
            if hash_256(block) not in hashes:
                miss_hashes.append(hash_256(block))
        return self.create_msg(0x02, miss_hashes)

    def get_data(self, hash_data):
        return self.create_msg(0x03, hash_data)

    def send_data(self, hash_data):
        search_block = None
        for block in self.block_chain:
            if hash_256(block) == hash_data:
                search_block = block
        return self.create_msg(0x04, search_block)

    def create_tx(self, value):
        tx = {
            'type': 'transaction',
            'id': '',
            'value': value
        }
        tx['id'] = hash_256(tx)
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
                'prev_block': hash_256(prev_block),
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
            if block['prev_block'] == hash_256(first_block):
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


if __name__ == '__main__':
    argv = sys.argv
    try:
        if len(argv) == 3:
            host_param = argv[1]
            port_param = int(argv[2])
        else:
            host_param = 'localhost'
            port_param = 8888
        node = Node(host_param, port_param)
        node.run()
    except ValueError:
        print("Valid host and port were not provided, node will run in (localhost,8888)")
        node = Node('localhost', 8888)
        node.run()

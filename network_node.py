import sys
import asyncio
from aioconsole import ainput


class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')
    
def node_print(msg): # Beauty printing
    print("\r"+msg + "\n<:3)~ ",end="")

class Node:
    def __init__(self, host, port):
        # Host y Port en donde va a correr el servidor
        self.host = host
        self.port = port
        # Host y Port del nodo al que se quiere conectar
        self.ref_host = None
        self.ref_port = None

        self.server = None
        self.connections = [] # Informacion de los nodos que se encuentran conectados a este
        self.blockchain = None # En el blockchain se referencia al ultimo
        self.new_transactions = [] # Un pool de transacciones conocidas que no se encuentran en el blockchain

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

    def set_reference(self, host, port): # Setea los datos del nodo al que se va a conectar / Se borra en siguiente version
        self.ref_host = host
        self.ref_port = port

    def save_connection(self, reader, writer): # Genera el objeto de conexion para cada nodo conectado
        new_connection = Connection(reader, writer)
        self.connections.append(new_connection)
        node_print(f'Connected to {new_connection.address!r}')

    async def spread_message(self, msg, addr):
        node_print(f"Spread: {msg!r}")
        for conn in self.connections:
            node_print(f"Trying to spread to {conn.address!r}")
            if conn.address != addr:
                node_print(f"Spreading to {conn.address!r}")
                conn.writer.write(msg.encode())
                await conn.writer.drain()

    async def server_init(self, host, port): # Inicia el servidor que acepta conexiones de nuevos nodos
        # Se inicia el servidor en la direccion (host,port)
        # Ejecuta la funcion handle_conection cuando recibe una nueva conexion
        self.server = await asyncio.start_server(self.handle_connection, host, port) 

        # Mostar que se inicio el servidor correctamente
        addr = self.server.sockets[0].getsockname()
        node_print(f'Serving on {addr}')

    async def handle_connection(self, reader, writer):
        # Guardar conexiones para ser usadas
        self.save_connection(reader,writer)
        addr = writer.get_extra_info('peername')
        # Mantenerse escuchando
        while True:
            data = await reader.read(100)
            message = data.decode()
            self.last_message = message
            if message == "":
                break
            node_print(f"Received {message!r} from {addr!r}")
            # Enviar mensaje a todos los otros nodos que estan conectados
            await self.spread_message(message, addr)

        node_print(f"Closed connection from {addr!r}")
        writer.close()

    async def new_connection(self, host, port): # Inicia la conexion que le permite entrar a la red
        reader, writer = await asyncio.open_connection(host, port)
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.handle_connection(reader, writer))
    
    async def prompt_init(self):
        while True:
            prompt = await ainput("\r<:3)~ ") # Input que no bloquea el resto de la ejecucion
            cmd = prompt.strip().split(' ')
            if cmd[0] == 'show':
                print(f'MSG: {self.last_message!r}')
            elif cmd[0] == 'c':
                if len(cmd) == 3:
                    host = cmd[1]
                    port = int(cmd[2])
                    await self.new_connection(host,port)
                else:
                    print("For new connection use command: c <host> <port>")
                
            elif cmd[0] == 't':
                print("Creating transaction")
            elif cmd[0] == 'b':
                print("Creating block")
            else:
                await self.spread_message(prompt, None)



if __name__ == '__main__':
    argv = sys.argv
    try:
        if len(argv) == 3:
            host = argv[1]
            port = int(argv[2])
        else:
            host = 'localhost'
            port = 8888
        node = Node(host, port)
        node.run()
    except ValueError:
        print("Valid host and port were not provided, node will run in (localhost,8888)")
        node = Node('localhost', 8888)
        node.run()

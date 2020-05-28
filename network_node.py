import asyncio
from aioconsole import ainput

class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')

class Node:
    def __init__(self, host, port):
        # Host y Port en donde va a correr el servidor
        self.host = host
        self.port = port
        # Host y Port del nodo al que se quiere conectar
        self.ref_host = None
        self.ref_port = None

        self.connections = [] # Informacion de los nodos que se encuentran conectados a este
        self.blockchain = None # En el blockchain se referencia al ultimo
        self.new_transactions = [] # Un pool de transacciones conocidas que no se encuentran en el blockchain

        self.sync_lock = False
        self.last_message = ''


    def run(self):
        # Obtener el loop de funciones asincornas
        loop = asyncio.get_event_loop()
        # Crear el task que se encarga de el servidor
        loop.create_task(self.server_init(self.host, self.port))
        # Si se entrega una referencia conectarse al nodo mediante el 'cliente'
        if self.ref_host and self.ref_port:
            loop.create_task(self.client_init(self.ref_host, self.ref_port))
        # It never ends
        loop.run_forever()

    def set_reference(self, host, port): # Setea los datos del nodo al que se va a conectar
        self.ref_host = host
        self.ref_port = port

    def save_connection(self, reader, writer): # Genera el objeto de conexion para cada nodo conectado
        self.connections.append(Connection(reader, writer))

    async def spread_message(self, msg, addr):
        print(f"Spread: {msg!r}")
        for conn in self.connections:
            print(f"Trying to spread to {conn.address!r}")
            if conn.address != addr:
                print(f"Spreading to {conn.address!r}")
                conn.writer.write(msg.encode())
                await conn.writer.drain()

    async def server_init(self, host, port): # Inicia el servidor que acepta conexiones de nuevos nodos
        # Se inicia el servidor en la direccion (host,port)
        # Ejecuta la funcion handle_conection cuando recibe una nueva conexion
        server = await asyncio.start_server(self.handle_connection, host, port) 

        # Mostar que se inicio el servidor correctamente
        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

    async def handle_connection(self, reader, writer):
        # Guardar conexiones para ser usadas
        self.save_connection(reader,writer)
        # Mantenerse escuchando
        while True:
            data = await reader.read(100)
            message = data.decode()
            self.last_message = message
            addr = writer.get_extra_info('peername')

            print(f"Received {message!r} from {addr!r}")
            # Enviar mensaje a todos los otros nodos que estan conectados
            await self.spread_message(message, addr)
            # print(f": {message!r}")
            # writer.write(data)
            # await writer.drain()

        print("Close the connection")
        writer.close()

    async def client_init(self, host, port): # Inicia la conexion que le permite entrar a la red
        reader, writer = await asyncio.open_connection(host, port)
        # self.connections.append(Connection(reader,writer))
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.handle_connection(reader,writer))
        while True:
            message = await ainput("msg> ") # Input que no bloquea el resto de la ejecucion
            if message == 'show':
                print(f'MSG: {self.last_message!r}')
            else:
                await self.spread_message(message,None)

            # data = await reader.read(100)
            # print(f'Received: {data.decode()!r}')
        print('Close the connection')
        writer.close()

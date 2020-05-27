import asyncio

class Node:
    def __init__(self, host, port, reference=None):
        self.host = host
        self.port = port
        self.ref_host = None
        self.ref_port = None


    def run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.server_init(self.host, self.port))
        if self.ref_host and self.ref_port:
            loop.create_task(self.client_init(self.ref_host, self.ref_port))
        loop.run_forever()

    def set_reference(self, host, port):
        self.ref_host = host
        self.ref_port = port

    async def server_init(self, host, port):
        server = await asyncio.start_server(self.handle_connection, host, port)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

    async def handle_connection(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()

        print("Close the connection")
        writer.close()

    async def client_init(self, host, port):
        reader, writer = await asyncio.open_connection(
        host, port)
        message = "Hola nodo servidor"
        print(f'Send: {message!r}')
        writer.write(message.encode())
        await writer.drain()

        data = await reader.read(100)
        print(f'Received: {data.decode()!r}')

        print('Close the connection')
        writer.close()

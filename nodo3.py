from network_node import Node

nodo3 = Node('localhost', 8890)
nodo3.set_reference('localhost', 8888)
nodo3.run()
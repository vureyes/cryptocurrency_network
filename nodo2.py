from network_node import Node

nodo2 = Node('localhost', 8889)
nodo2.set_reference('localhost', 8888)
nodo2.run()

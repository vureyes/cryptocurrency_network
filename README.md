# Cryptocurrency Network

## Señales
    
 - 0x00 : Version
 - 0x01 : Current Blockchain Hash
 - 0x02 : Missing Blocks Hash
 - 0x03 : Get Block
 - 0x04 : Send Block
 - 0x05 : Propagate Tx
 - 0x06 : Propagate New Block
    
 ### 0x00
 
 - Mensaje enviado al recibir una conexión
 - Contiene la versión (largo) del Blockchain actual del nodo
 
 ### 0x01
 
 - Mensaje enviado al verificar que el largo del Blockchain difiere
 - Contiene la lista de Hashes del Blockchain que posee el nodo
 
 ### 0x02
 
 - Mensaje enviado para sincronizar un Blockchain de una versión anterior 
 - Contiene la lista de Hashes de los bloques que faltan para actualizar una versión anterior del Blockchain
 
 ### 0x03
 
 - Mensaje enviado para consultar por un bloque del Blockchain con cierto hash
 - Contiene el hash de un bloque en el Blockchain
 
 ### 0x04
 
 - Mensaje envido para enviar un bloque del Blockchain
 - Contiene el bloque del Blockchain que se desea enviar
 
 ### 0x05
 
 - Mensaje enviado para publicar una nueva transacción en la red
 - Contiene la transacción que se quiere agregar al pool de transacciones
 
 ### 0x06
 
 - Mensaje enviado para publicar un nuevo bloque del Blockchain en la red
 - Contiene el nuevo bloque que se quiere agragar a la nueva versón del Blockchain


## Comandos
 - __c \<_host_> \<_port_>__ : Conectar con un nodo de la red identificado por el par (_host_, _port_)
 - __t \<_value_>__ : Crear una nueva transaccion con el valor _value_
 - __b__ : Crear un nuevo bloque
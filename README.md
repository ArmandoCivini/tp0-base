## Parte 3: Repaso de Concurrencia

### Ejercicio N°8:
Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo.
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

En caso de que el alumno implemente el servidor Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Implementación
Para lograr concurrencia en el servidor se usaron los multiprocesos de python. El programa genera un proceso por cada conexión a un cliente. Cada uno de estos procesos se comunica con su cliente, procesa los batches recibidos y los coloca en la cola `bet_q`. Además hay un proceso adicional, `bet_loader` que se encarga solamente de sacar batches de esta cola para guardarlos con `store_bets`. 
<br />
<br />
Si un proceso de cliente termina de procesar batches, éste lo avisa por la cola `bet_q`. Gracias a esto, cuando el `bet_loader` detecta que todos los procesos an terminado enviando batches. Este finaliza.
<br />
<br />
Al finalizar `bet_loader`, el proceso principal despertará y comenzara a procesar ganadores. Al encontrar un ganador, el proceso principal lo enviará atravez de la cola `winner_q` al proceso del cliente correspondiente. Los procesos de clientes desde haber terminado de procesar apuestas estuvieron esperando sobre esta cola los ganadores para enviarselos al cliente.
<br />
<br />
Una vez terminado los ganadores, el proceso principal avisa a los procesos clientes mediante la `winner_q` de cada uno y ellos envian el mensaje de finalización al cliente y terminan. Al finalizar todos los procesos clientes, el proceso principal también finalizará.


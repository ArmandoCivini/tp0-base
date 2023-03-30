## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base al código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°7:
Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo, no podrá responder consultas por la lista de ganadores.
Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

## Protocolo

### Batches

Lo primero que hace el cliente al conectarse al servidor es empezar a mandar batches. Para esto tiene una forma especifica de mandar los mensajes.
<Br/>
<Br/>
El primer byte que envia indica el tipo de mensaje, de ser un mensaje de batches de apuestas, este byte estará seteado en 1. El siguiente byte marcará el tamaño de un batch, lo cual le dirá al servidor cuantas apuestas leer del socket. Despues de esto se adjuntan todas las apuestas del batch. Las apuestas usan un sistema mixto, los números se manejan con bloques fijos mientras que las string llevan un byte adelante para demarcar su largo. Los campos que se envian en una apuesta y sus tipos son los siguientes:
<Br/>
Nombre[string]
Apellido[string]
Documento[int32]
Año de nacimiento[int16]
Mes de nacimiento[int8]
Día de nacimiento[int8]
Número[int32]
<Br/>
<Br/>
Por cada uno de estos batches enviados se va a esperar la confirmación del servidor que responderá con un byte. Al finalizar el envío de todos los bytes, el cliente le manda un byte el 2 para avisarle al servidor que termino con los batches.

### Ganadores

Al finalizar de enviar los batches el cliente se queda aguardando los ganadores. Por cada apuesta ganadora de ese cliente el servidor le enviará un mensaje con el primer byte en 5 y 4 bytes más representanto el documento del ganador.
<Br/>
<Br/>
Además el servidor envía un mensaje adicional para avisar que se terminaron de enviar los ganadores.


# ReservaU - PSet 2

## 1. Tabla de patrones

| Patrón | Requerimiento que lo justifica | Problema que resuelve | Clases y métodos |
| Factory Method | RF-02, RF-07 a RF-09; RNF-02 | Crear una reserva regular o de equipo con su política de cancelación asignada. | `CreadorReserva.crear_reserva()`, `CreadorRegular`, `CreadorEquipo` y `elegir_creador()` |
| Abstract Factory | RF-22; RNF-07 | Usar el validador y el notificador de la misma sede. | `FabricaNorte`, `FabricaSur`, `crear_validador()`, `crear_notificador()` y `ServiciosSede` |
| Builder | RF-13, RF-16 | Construir la solicitud recurrente con datos obligatorios y opciones de semanas, equipo y notas. | `ReservaRecurrenteBuilder.semanas()`, `.equipo()`, `.notas()` y `.build()` |
| Prototype | RF-19, RF-20 | Clonar bloqueos para distintas canchas y fechas sin compartir la lista de equipo. | `Bloqueo.clonar(cancha, fecha)` |
| Singleton | RF-24 | Mantener los valores de las reglas en una configuración compartida. | `ConfiguracionReglas.obtener_instancia()` |
| Strategy | RF-03, RF-07 a RF-09; RNF-02 | Aplicar distintas reglas de prioridad y cancelación sin preguntar en Reserva quién la creó. | `PrioridadRegular`, `PrioridadCapitan`, `tiene_prioridad()`, `CancelacionEstudiante`, `CancelacionCapitan`, `AnulacionSinPenalidad`, `evaluar()` y `Reserva.cancelar()` |
| Facade | RF-02, RF-06, RF-13 a RF-15, RF-21, RF-23 | Coordinar disponibilidad, calendario, sede, no-shows y notificaciones desde un punto de entrada. | `ReservaUFacade.reservar()`, `.reservar_recurrente()`, `.cancelar()` y `.bloquear()` |
| Concurrencia: locking pesimista | RNF-05, RNF-06 | Evitar dos confirmaciones para la misma cancha y franja, y proteger el registro completo de una serie. | `Cancha.lock`, `Estudiante.lock` y las secciones críticas de `ReservaUFacade`; `Barrier` y `Thread` en la simulación |

## 2. Justificación de Prototype

En `Bloqueo.clonar()` se usa `copy.copy(self)` para crear otro bloqueo y `copy.deepcopy(self.equipo)` para darle su propia lista de equipo. Así, agregar elementos a un clon no cambia la plantilla ni los otros clones. Después se ajustan la fecha y la cancha de destino.

Usar solo una copia superficial dejaría la lista compartida. Copiar todo el bloqueo profundamente tampoco conviene: la cancha de destino debe seguir siendo la misma entidad del sistema, con su calendario y su lock.

## 3. Justificación de Singleton

Singleton permite que prioridad, cancelación y suspensión consulten los mismos valores, definidos en un solo lugar. Se obtiene mediante `ConfiguracionReglas.obtener_instancia()`, como en el Singleton del laboratorio de semana 05. Su costo es el estado compartido: cambiar una regla afecta a todos sus consumidores, por lo que cualquier cambio durante una prueba debe restaurarse después. La creación de la instancia está protegida con un lock para evitar que dos hilos creen configuraciones distintas.

## 4. Justificación de concurrencia

Se eligió locking pesimista por cancha porque la verificación y el registro son operaciones breves en memoria. Durante los picos de reservas al inicio del semestre, el lock hace que una solicitud termine de comprobar y registrar antes de que otra pueda reservar esa misma franja.

Como hay más consultas de disponibilidad que reservas, se mantiene el bloqueo por el menor tiempo posible. Las consultas también toman el lock de su cancha y pueden esperar durante una escritura, pero las operaciones sobre otras canchas pueden continuar. Este es el costo aceptado frente a una solución optimista, que exigiría controlar versiones y reintentar operaciones cuando hubiera conflictos.

En una reserva recurrente, el lock se conserva desde la validación de la primera semana hasta el registro de toda la serie. La simulación sincroniza dos hilos con `Barrier` y comprueba que solo uno obtenga confirmación para una cancha y franja libres.

## 5. Trazabilidad de los tres no-shows

| Parte del recorrido | Ubicación |
| Requerimientos | RF-17 define el recuento por mes calendario y evita duplicar eventos. RF-18 establece la suspensión de 7 días al tercer no-show. |
| Caso de uso | CU2, alternativa 3a, registra el no-show y aplica la suspensión. CU1 y CU5, alternativa 2a, rechazan nuevas reservas mientras esté vigente. |
| Diagramas | Robustez conecta la Facade con Estudiante. La máquina de estados muestra el efecto del tercer no-show. Secuencia incluye el rechazo por suspensión y actividad contempla el rechazo de una serie. |
| Patrón y coordinación | Strategy clasifica la cancelación como `NoShow`. La Facade llama a `Estudiante.registrar_no_show(reserva, ahora)`. |
| Entidad y métodos | Estudiante conserva los eventos, los cuenta con `contar_no_shows(anio, mes)` y aplica la suspensión con `suspender(ahora)`. |
| Configuración | Obtiene `ConfiguracionReglas.obtener_instancia()` y consulta `.limite_no_shows`, cuyo valor es 3, y `.dias_suspension`, cuyo valor es 7. |
| Simulación | En el escenario 5 de `simulacion.py`, el solicitante acumula tres no-shows y luego intenta reservar. En `otros/SALIDA_SIMULACION.txt`, la línea 155 muestra el tercer evento, la 156 indica el vencimiento y la 162 muestra el rechazo por suspensión. |

## 6. Qué ocurriría sin cada patrón

- **Factory Method:** la selección del tipo de reserva y su política se repetiría en la reserva individual y en la recurrente.
- **Abstract Factory:** el cliente elegiría por separado validador y notificador, con el riesgo de combinar servicios de sedes distintas.
- **Builder:** cada cliente tendría que manejar todos los parámetros y repetir la validación de las opciones de la serie.
- **Prototype:** habría que reconstruir cada bloqueo a mano y cuidar en cada copia que el equipo no quedara compartido.
- **Singleton:** los valores de las reglas podrían repetirse o diferir entre prioridad, cancelación y suspensión.
- **Strategy:** Reserva necesitaría condicionales para distinguir estudiantes, capitanes y anulaciones administrativas al cancelar.
- **Facade:** la simulación tendría que coordinar directamente los subsistemas y conocer el orden de cada operación.
- **Control de concurrencia:** dos solicitudes podrían consultar la misma franja libre y confirmar ambas, o interferir con el registro de una serie.

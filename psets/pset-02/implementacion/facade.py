"""Coordinacion de casos de uso y secciones criticas por cancha."""
from threading import RLock

from modelos import Administrador, Estudiante, Cancha
from creacion import elegir_creador, ReservaRecurrenteBuilder, Sede


class Resultado:
    def __init__(self, exito, motivo='', reserva=None, serie=None, clones=None):
        self.exito = exito
        self.motivo = motivo
        self.reserva = reserva
        self.serie = serie
        if clones is None:
            self.clones = []
        else:
            self.clones = clones


class ReservaUFacade:
    def __init__(self, canchas=(), emitir=print):
        self._canchas = {}
        for cancha in canchas:
            if cancha.codigo in self._canchas:
                raise ValueError('Codigos de cancha duplicados.')
            self._canchas[cancha.codigo] = cancha
        self._reservas = {}
        self._registro_lock = RLock()
        self._salida_lock = RLock()
        self._salida = emitir

    def emitir(self, mensaje):
        with self._salida_lock:
            self._salida(mensaje)

    def _cancha(self, codigo):
        if codigo not in self._canchas:
            raise ValueError('Cancha desconocida.')
        return self._canchas[codigo]

    def _validar(self, solicitante, cancha, intervalo, ahora, verificar_habilitacion=True):
        if not isinstance(solicitante, Estudiante):
            raise ValueError('Solicitante invalido.')
        if solicitante.esta_suspendido(ahora):
            raise ValueError('Solicitante suspendido.')
        intervalo.validar()
        if intervalo.inicio <= ahora:
            raise ValueError('El intervalo debe ser futuro.')
        cancha.sede.validar_horario(intervalo)
        if verificar_habilitacion and not cancha.habilitada:
            raise ValueError('Cancha no disponible: deshabilitada.')

    def _evento(self, reserva, ahora):
        reserva.cancha.calendario.historial.append({
            'fecha': ahora, 'id': reserva.id, 'solicitante': reserva.solicitante.codigo,
            'estado': reserva.estado, 'motivo': reserva.motivo})

    def _notificar(self, reserva):
        mensaje = f'{reserva.id} {reserva.estado}: destinatario {reserva.solicitante.codigo}'
        if reserva.motivo:
            mensaje += f'; motivo: {reserva.motivo}'
        reserva.cancha.sede.notificar(mensaje, self.emitir)

    def _rechazar(self, error):
        self.emitir(f'Rechazo: {error}')
        return Resultado(False, str(error))

    def reservar(self, solicitante, codigo_cancha, intervalo, ahora):
        self.emitir(f'CU1 1. Solicitar reserva individual: {solicitante.codigo}')
        try:
            cancha = self._cancha(codigo_cancha)
            # Orden de locks consistente: solicitante, luego cancha.
            with solicitante.lock, cancha.lock:
                self.emitir('CU1 2. Validar solicitante y suspension')
                if solicitante.esta_suspendido(ahora):
                    raise ValueError('Solicitante suspendido.')
                self.emitir('CU1 3. Validar intervalo y horario de sede')
                self._validar(solicitante, cancha, intervalo, ahora, verificar_habilitacion=False)
                self.emitir('CU1 4. Verificar habilitacion y conflictos bajo lock')
                if not cancha.habilitada:
                    raise ValueError('Cancha no disponible: deshabilitada.')
                desplazadas = cancha.calendario.resolver_prioridad(solicitante, intervalo, ahora)
                if desplazadas:
                    self.emitir('CU1 4b. Preparar desplazamiento de regulares futuras sin penalidad')
                self.emitir('CU1 5. Crear reserva con politica de cancelacion')
                reserva = elegir_creador(solicitante).crear_reserva(solicitante, cancha, intervalo)
                self.emitir('CU1 6. Confirmar y registrar reserva')
                for anterior in desplazadas:
                    anterior.anular('prioridad de equipo oficial')
                    self._evento(anterior, ahora)
                cancha.calendario.registrar(reserva)
                with self._registro_lock:
                    self._reservas[reserva.id] = reserva
                self._evento(reserva, ahora)
            self.emitir('CU1 7. Notificar resultado por sede')
            for anterior in desplazadas:
                self.emitir('CU1 7. Anulacion por prioridad sin penalidad al estudiante afectado')
                self._notificar(anterior)
            self._notificar(reserva)
            return Resultado(True, reserva=reserva)
        except ValueError as error:
            return self._rechazar(error)

    def cancelar(self, id_reserva, actor, ahora, motivo=''):
        self.emitir('CU2 1. Seleccionar reserva y solicitar cancelacion')
        try:
            with self._registro_lock:
                if id_reserva not in self._reservas:
                    raise ValueError('Reserva desconocida.')
                reserva = self._reservas[id_reserva]
            with reserva.solicitante.lock, reserva.cancha.lock:
                self.emitir('CU2 2. Validar autorizacion y estado Confirmada')
                if not isinstance(actor, Administrador) and actor is not reserva.solicitante:
                    raise ValueError('No puede cancelar una reserva ajena.')
                reserva.validar_transicion('Confirmada')
                if isinstance(actor, Administrador) and not motivo.strip():
                    raise ValueError('Anulacion administrativa requiere motivo.')
                self.emitir('CU2 3. Evaluar politica de cancelacion con hora actual')
                if isinstance(actor, Administrador):
                    reserva.anular(motivo)
                    self.emitir('CU2 3b. Anulada sin penalidad')
                else:
                    reserva.cancelar(ahora)
                    if reserva.estado == 'NoShow':
                        reserva.solicitante.registrar_no_show(reserva, ahora)
                        conteo = reserva.solicitante.contar_no_shows(ahora.year, ahora.month)
                        self.emitir(f'CU2 3a. NoShow; eventos del mes: {conteo}')
                        if reserva.solicitante.esta_suspendido(ahora):
                            self.emitir(f'Suspension vigente hasta {reserva.solicitante.suspensiones[-1].fin}')
                    else:
                        self.emitir('CU2 4. Cambiar estado a Cancelada')
                self.emitir('CU2 5. Actualizar ocupacion e historial')
                self._evento(reserva, ahora)
            self.emitir('CU2 6. Notificar resultado por sede')
            self._notificar(reserva)
            return Resultado(True, reserva=reserva)
        except ValueError as error:
            return self._rechazar(error)

    def reservar_recurrente(self, builder, ahora):
        self.emitir('CU5 1. Solicitar serie con datos obligatorios y opcionales')
        try:
            self.emitir('CU5 2. Validar capitan, suspension y Builder (2 a 8 semanas)')
            if not isinstance(builder, ReservaRecurrenteBuilder):
                raise ValueError('Se requiere ReservaRecurrenteBuilder.')
            serie = builder.build()
            cancha = self._cancha(serie.cancha.codigo)
            if cancha is not serie.cancha:
                raise ValueError('Cancha de serie no registrada.')
            with serie.solicitante.lock, cancha.lock:
                if serie.solicitante.esta_suspendido(ahora):
                    raise ValueError('Solicitante suspendido; cero reservas nuevas.')
                self.emitir('CU5 3. Generar intervalos semanales')
                intervalos = serie.generar_intervalos()
                for semana, intervalo in enumerate(intervalos, 1):
                    self.emitir(f'CU5 4. Validar semana {semana}: sede, habilitacion y ocupacion bajo lock; fecha {intervalo.inicio:%Y-%m-%d}')
                    try:
                        self._validar(serie.solicitante, cancha, intervalo, ahora)
                        if cancha.calendario.buscar_conflictos(intervalo):
                            raise ValueError('conflicto de ocupacion')
                    except ValueError as error:
                        raise ValueError(f'Semana {semana} ({intervalo.inicio:%Y-%m-%d}): {error}; cero reservas nuevas.')
                    if semana < serie.semanas:
                        respuesta = 'Si'
                    else:
                        respuesta = 'No'
                    self.emitir('CU5 5. ¿Quedan semanas por validar? ' + respuesta)
                creador = elegir_creador(serie.solicitante)
                reservas = []
                for intervalo in intervalos:
                    reserva = creador.crear_reserva(serie.solicitante, cancha, intervalo)
                    reserva.serie_id = serie.id
                    reserva.equipo_prestado = list(serie.equipo_prestado)
                    reserva.notas = serie.notas
                    reservas.append(reserva)
                self.emitir('CU5 6. Crear y registrar todas las reservas de la serie')
                cancha.calendario.registrar_serie(reservas)
                serie.asociar_reservas(reservas)
                with self._registro_lock:
                    for reserva in reservas:
                        self._reservas[reserva.id] = reserva
                for reserva in reservas:
                    self._evento(reserva, ahora)
            self.emitir('CU5 7. Notificar confirmaciones por sede')
            for reserva in reservas:
                self._notificar(reserva)
            return Resultado(True, serie=serie)
        except ValueError as error:
            return self._rechazar(error)

    def bloquear(self, administrador, plantilla, destinos, ahora):
        self.emitir('CU6 1. Definir plantilla: motivo, franja y equipo')
        try:
            if not isinstance(administrador, Administrador):
                raise ValueError('Solo el administrador puede bloquear.')
            self.emitir('CU6 2. Clonar para canchas y fechas de destino')
            clones = []
            for codigo, fecha in destinos:
                cancha = self._cancha(codigo)
                clones.append(plantilla.clonar(cancha, fecha))
            if not clones:
                raise ValueError('Al menos un destino es obligatorio.')
            self.emitir('CU6 3. Validar todos los clones y horario de sede')
            for clon in clones:
                clon.validar()
                if clon.intervalo.inicio <= ahora:
                    raise ValueError('El bloqueo debe ser futuro.')
            afectadas = {}
            # Tomar las canchas en el mismo orden evita esperas entre dos bloqueos.
            canchas = {}
            for clon in clones:
                canchas[clon.cancha.codigo] = clon.cancha
            canchas_bloqueadas = []
            try:
                for codigo in sorted(canchas):
                    cancha = canchas[codigo]
                    cancha.lock.acquire()
                    canchas_bloqueadas.append(cancha)
                self.emitir('CU6 4. Aplicar bloqueo bajo lock e identificar reservas afectadas')
                for clon in clones:
                    for reserva in clon.cancha.calendario.reservas:
                        if reserva.estado == 'Confirmada' and reserva.intervalo.solapa(clon.intervalo):
                            afectadas[reserva.id] = (reserva, clon.motivo)
                self.emitir('CU6 5. Anular reservas confirmadas solapadas sin penalidad')
                for reserva, motivo in afectadas.values():
                    reserva.anular(motivo)
                    self._evento(reserva, ahora)
                self.emitir('CU6 6. Registrar bloqueos e historial')
                for clon in clones:
                    clon.cancha.calendario.bloqueos.append(clon)
                    clon.cancha.calendario.historial.append({
                        'fecha': ahora, 'estado': 'Bloqueo', 'motivo': clon.motivo,
                        'inicio': clon.intervalo.inicio, 'fin': clon.intervalo.fin})
            finally:
                # Liberar tambien si ocurre un error durante la operacion.
                for cancha in reversed(canchas_bloqueadas):
                    cancha.lock.release()
            self.emitir('CU6 7. Notificar a cada afectado por sede')
            for reserva, _ in afectadas.values():
                self._notificar(reserva)
            return Resultado(True, clones=clones)
        except ValueError as error:
            return self._rechazar(error)

    def consultar_disponibilidad(self, codigo_cancha, intervalo):
        cancha = self._cancha(codigo_cancha)
        cancha.sede.validar_horario(intervalo)
        with cancha.lock:
            return cancha.habilitada and not cancha.calendario.buscar_conflictos(intervalo)

    def consultar_historial(self, administrador, codigo_cancha):
        if not isinstance(administrador, Administrador):
            raise ValueError('Historial reservado al administrador.')
        cancha = self._cancha(codigo_cancha)
        with cancha.lock:
            historial = []
            for evento in cancha.calendario.historial:
                historial.append(dict(evento))
            return historial

    def gestionar_cancha(self, administrador, codigo_cancha, habilitada=True,
                         confirmar=True, deporte=None, sede=None, agregar=False):
        self.emitir('CU3 1. Solicitar gestion y consultar canchas')
        if not isinstance(administrador, Administrador):
            return self._rechazar(ValueError('Administrador requerido.'))
        self.emitir('CU3 2. Seleccionar agregar, modificar o habilitar')
        self.emitir('CU3 3. Ingresar datos y confirmar operacion')
        if not confirmar:
            return self._rechazar(ValueError('Operacion no confirmada; sin cambios.'))
        try:
            self.emitir('CU3 4. Validar codigo, sede y deporte')
            if type(habilitada) is not bool:
                raise ValueError('Habilitacion debe ser booleana.')
            if deporte is not None and (not isinstance(deporte, str) or not deporte.strip()):
                raise ValueError('Deporte obligatorio.')
            if sede is not None and not isinstance(sede, Sede):
                raise ValueError('Sede invalida.')
            if agregar:
                if deporte is None or sede is None:
                    raise ValueError('Alta requiere deporte y sede.')
                nueva = Cancha(codigo_cancha, deporte, sede)
                nueva.habilitada = habilitada
                with self._registro_lock:
                    if codigo_cancha in self._canchas:
                        raise ValueError('Codigo de cancha duplicado.')
                    self.emitir('CU3 5. Aplicar actualizacion administrativa')
                    self._canchas[codigo_cancha] = nueva
            else:
                cancha = self._cancha(codigo_cancha)
                with cancha.lock:
                    # No cambiar de sede si hay reservas o bloqueos historicos:
                    # sus ventanas y canales pertenecen a la sede original.
                    if sede is not None and sede.codigo != cancha.sede.codigo and (
                            cancha.calendario.reservas or cancha.calendario.bloqueos):
                        raise ValueError('Cancha con historial: conservar sede original.')
                    self.emitir('CU3 5. Aplicar actualizacion administrativa')
                    if deporte is not None:
                        cancha.deporte = deporte
                    if sede is not None:
                        cancha.sede = sede
                    if habilitada:
                        cancha.habilitar()
                    else:
                        cancha.deshabilitar()
            self.emitir('CU3 6. Comunicar confirmacion')
            return Resultado(True)
        except ValueError as error:
            return self._rechazar(error)

    def resolver_conflicto(self, administrador, id_reserva, ahora, motivo='', mantener=False, confirmar=True):
        self.emitir('CU4 1. Consultar historial y seleccionar conflicto')
        if not isinstance(administrador, Administrador):
            return self._rechazar(ValueError('Administrador requerido.'))
        try:
            with self._registro_lock:
                if id_reserva not in self._reservas:
                    raise ValueError('Reserva desconocida.')
                reserva = self._reservas[id_reserva]
            self.emitir('CU4 2. Decidir mantener o anular con motivo')
            self.emitir('CU4 3. Confirmar intervencion')
            if not confirmar:
                self.emitir('CU4 3a. Intervencion no confirmada; estado conservado')
                return Resultado(True, reserva=reserva)
            with reserva.solicitante.lock, reserva.cancha.lock:
                self.emitir('CU4 4. Validar reserva Confirmada y autorizacion')
                reserva.validar_transicion('Confirmada')
                if not mantener and not motivo.strip():
                    raise ValueError('Anulacion administrativa requiere motivo.')
                self.emitir('CU4 5. Aplicar resolucion e historial')
                if mantener:
                    self.emitir('CU4 5a. Mantener estado e historial')
                    return Resultado(True, reserva=reserva)
                reserva.anular(motivo)
                self._evento(reserva, ahora)
            self.emitir('CU4 6. Notificar resultado por sede')
            self._notificar(reserva)
            return Resultado(True, reserva=reserva)
        except ValueError as error:
            return self._rechazar(error)

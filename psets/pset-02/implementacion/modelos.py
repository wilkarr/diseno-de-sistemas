from datetime import datetime, timedelta
from threading import Lock, RLock
import copy

from politicas import (ConfiguracionReglas, PrioridadRegular, PrioridadCapitan,
                       AnulacionSinPenalidad)


class Intervalo:
    def __init__(self, inicio, fin):
        self.inicio = inicio
        self.fin = fin

    def validar(self):
        if self.inicio >= self.fin or self.inicio.date() != self.fin.date():
            raise ValueError('Intervalo invalido: inicio < fin en un mismo dia.')

    def solapa(self, otro):
        return self.inicio < otro.fin and otro.inicio < self.fin

    def desplazar_semanas(self, n):
        delta = timedelta(weeks=n)
        return Intervalo(self.inicio + delta, self.fin + delta)


class Suspension:
    def __init__(self, inicio, fin, anio_mes_origen):
        self.inicio = inicio
        self.fin = fin
        self.anio_mes_origen = anio_mes_origen

    def esta_vigente(self, ahora):
        return self.inicio <= ahora < self.fin


class Estudiante:
    def __init__(self, codigo):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError('Codigo de solicitante obligatorio.')
        self.codigo = codigo
        self.politica_prioridad = PrioridadRegular()
        self.no_shows = {}
        self.suspensiones = []
        self.lock = RLock()

    def contar_no_shows(self, anio, mes):
        cantidad = 0
        for fecha in self.no_shows.values():
            if fecha.year == anio and fecha.month == mes:
                cantidad += 1
        return cantidad

    def registrar_no_show(self, reserva, ahora):
        with self.lock:
            if reserva.id in self.no_shows:
                return False
            self.no_shows[reserva.id] = ahora
            reglas = ConfiguracionReglas.obtener_instancia()
            periodo = (ahora.year, ahora.month)
            ya_aplicada = False
            for suspension in self.suspensiones:
                if suspension.anio_mes_origen == periodo:
                    ya_aplicada = True
                    break
            cantidad = self.contar_no_shows(ahora.year, ahora.month)
            if cantidad >= reglas.limite_no_shows and not ya_aplicada:
                self.suspender(ahora)
            return True

    def suspender(self, ahora):
        reglas = ConfiguracionReglas.obtener_instancia()
        fin = ahora + timedelta(days=reglas.dias_suspension)
        periodo = (ahora.year, ahora.month)
        self.suspensiones.append(Suspension(ahora, fin, periodo))

    def esta_suspendido(self, ahora):
        for suspension in self.suspensiones:
            if suspension.esta_vigente(ahora):
                return True
        return False


class EquipoOficial:
    def __init__(self, nombre, deporte):
        self.nombre = nombre
        self.deporte = deporte


class Capitan(Estudiante):
    def __init__(self, codigo, equipo_oficial):
        super().__init__(codigo)
        self.equipo_oficial = equipo_oficial
        self.politica_prioridad = PrioridadCapitan()


class Administrador:
    def __init__(self, codigo):
        self.codigo = codigo


class CalendarioCancha:
    def __init__(self):
        self.reservas = []
        self.bloqueos = []
        self.historial = []

    def buscar_conflictos(self, intervalo):
        conflictos = []
        for reserva in self.reservas:
            if reserva.ocupa(intervalo):
                conflictos.append(reserva)
        for bloqueo in self.bloqueos:
            if bloqueo.intervalo.solapa(intervalo):
                conflictos.append(bloqueo)
        return conflictos

    def resolver_prioridad(self, solicitante, intervalo, ahora):
        conflictos = self.buscar_conflictos(intervalo)
        if not conflictos:
            return []
        if not solicitante.politica_prioridad.tiene_prioridad(intervalo.inicio):
            raise ValueError('Cancha no disponible.')
        # Primero comprobar todos: nunca anular parcialmente por un conflicto mixto.
        for reserva in conflictos:
            if not isinstance(reserva, ReservaRegular):
                raise ValueError('Cancha no disponible: conflictos no desplazables.')
            if reserva.estado != 'Confirmada' or reserva.intervalo.inicio <= ahora:
                raise ValueError('Cancha no disponible: conflictos no desplazables.')
        return conflictos

    def registrar(self, reserva):
        reserva.confirmar()
        self.reservas.append(reserva)

    def registrar_serie(self, reservas):
        # Los objetos se construyen y validan antes de modificar el calendario.
        for reserva in reservas:
            if reserva.estado != 'Pendiente':
                raise ValueError('La serie requiere reservas pendientes.')
        for reserva in reservas:
            reserva.confirmar()
        self.reservas.extend(reservas)


class Cancha:
    def __init__(self, codigo, deporte, sede):
        if not isinstance(codigo, str) or not codigo.strip() or not isinstance(deporte, str) or not deporte.strip():
            raise ValueError('Codigo y deporte obligatorios.')
        self.codigo = codigo
        self.deporte = deporte
        self.sede = sede
        self.habilitada = True
        self.calendario = CalendarioCancha()
        self.lock = RLock()

    def habilitar(self):
        self.habilitada = True

    def deshabilitar(self):
        self.habilitada = False


class Reserva:
    _contador = 0
    _lock_id = Lock()

    def __init__(self, solicitante, cancha, intervalo, politica_cancelacion):
        intervalo.validar()
        # Un numero diferente para cada reserva durante esta ejecucion.
        with Reserva._lock_id:
            Reserva._contador += 1
            self.id = 'RES-' + str(Reserva._contador)
        self.solicitante = solicitante
        self.cancha = cancha
        self.intervalo = intervalo
        self.politica_cancelacion = politica_cancelacion
        self.estado = 'Pendiente'
        self.motivo = ''
        self.serie_id = None
        self.equipo_prestado = []
        self.notas = ''

    def validar_transicion(self, esperado):
        if self.estado != esperado:
            raise ValueError(f'Estado {self.estado}: operacion no permitida.')

    def confirmar(self):
        self.validar_transicion('Pendiente')
        self.estado = 'Confirmada'

    def rechazar(self):
        self.validar_transicion('Pendiente')
        self.estado = 'Rechazada'

    def cancelar(self, ahora):
        self.validar_transicion('Confirmada')
        self.estado = self.politica_cancelacion.evaluar(self.intervalo.inicio, ahora)
        return self.estado

    def anular(self, motivo):
        self.validar_transicion('Confirmada')
        self.estado = AnulacionSinPenalidad().evaluar(self.intervalo.inicio, None)
        self.motivo = motivo

    def ocupa(self, intervalo):
        return self.estado in ('Confirmada', 'NoShow') and self.intervalo.solapa(intervalo)


class ReservaRegular(Reserva):
    pass


class ReservaEquipo(Reserva):
    pass


class ReservaRecurrente:
    _contador = 0
    _lock_id = Lock()

    def __init__(self, solicitante, cancha, intervalo, semanas=2,
                 equipo_prestado=None, notas=''):
        self.solicitante = solicitante
        self.cancha = cancha
        self.intervalo = intervalo
        self.semanas = semanas
        if equipo_prestado is None:
            self.equipo_prestado = []
        else:
            self.equipo_prestado = list(equipo_prestado)
        self.notas = notas
        with ReservaRecurrente._lock_id:
            ReservaRecurrente._contador += 1
            self.id = 'SER-' + str(ReservaRecurrente._contador)
        self.reservas = []

    def generar_intervalos(self):
        intervalos = []
        for semana in range(self.semanas):
            intervalos.append(self.intervalo.desplazar_semanas(semana))
        return intervalos

    def asociar_reservas(self, reservas):
        self.reservas = reservas


class Bloqueo:
    def __init__(self, motivo, intervalo, equipo=None, cancha=None):
        self.motivo = motivo
        self.intervalo = intervalo
        if equipo is None:
            self.equipo = []
        else:
            self.equipo = list(equipo)
        self.cancha = cancha

    def clonar(self, cancha, fecha):
        clon = copy.copy(self)
        clon.equipo = copy.deepcopy(self.equipo)
        clon.cancha = cancha
        clon.intervalo = Intervalo(
            datetime.combine(fecha, self.intervalo.inicio.time()),
            datetime.combine(fecha, self.intervalo.fin.time()))
        return clon

    def validar(self):
        if not self.motivo.strip() or self.cancha is None:
            raise ValueError('Motivo y cancha de bloqueo obligatorios.')
        self.intervalo.validar()
        self.cancha.sede.validar_horario(self.intervalo)

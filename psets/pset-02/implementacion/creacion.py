"""Factory Method, Abstract Factory y Builder."""
from abc import ABC, abstractmethod
from datetime import time
from modelos import ReservaRegular, ReservaEquipo, ReservaRecurrente, Estudiante, Capitan
from politicas import CancelacionEstudiante, CancelacionCapitan


class CreadorReserva(ABC):
    @abstractmethod
    def crear_reserva(self, solicitante, cancha, intervalo):
        pass


class CreadorRegular(CreadorReserva):
    def crear_reserva(self, solicitante, cancha, intervalo):
        return ReservaRegular(solicitante, cancha, intervalo, CancelacionEstudiante())


class CreadorEquipo(CreadorReserva):
    def crear_reserva(self, solicitante, cancha, intervalo):
        return ReservaEquipo(solicitante, cancha, intervalo, CancelacionCapitan())


def elegir_creador(solicitante):
    # La seleccion del creador tiene un unico lugar; comprobar primero el subtipo.
    if isinstance(solicitante, Capitan):
        return CreadorEquipo()
    if isinstance(solicitante, Estudiante):
        return CreadorRegular()
    raise ValueError('Solicitante invalido.')


class ValidadorHorario:
    def __init__(self, sede, apertura, cierre):
        self.sede = sede
        self.apertura = apertura
        self.cierre = cierre

    def validar(self, intervalo):
        intervalo.validar()
        if not self.apertura <= intervalo.inicio.time() < intervalo.fin.time() <= self.cierre:
            raise ValueError(f'Horario fuera de sede {self.sede}.')


class Notificador:
    def __init__(self, sede, canal):
        self.sede = sede
        self.canal = canal

    def notificar(self, mensaje, emitir):
        emitir(f'[{self.sede} / {self.canal}] {mensaje}')


class FabricaSede(ABC):
    @abstractmethod
    def crear_validador(self):
        pass

    @abstractmethod
    def crear_notificador(self):
        pass


class FabricaNorte(FabricaSede):
    def crear_validador(self):
        return ValidadorHorario('Norte', time(6), time(22))

    def crear_notificador(self):
        return Notificador('Norte', 'correo institucional')


class FabricaSur(FabricaSede):
    def crear_validador(self):
        return ValidadorHorario('Sur', time(7), time(23))

    def crear_notificador(self):
        return Notificador('Sur', 'SMS')


class ServiciosSede:
    def __init__(self, fabrica):
        # El cliente aporta una fabrica, nunca productos separados.
        self._validador = fabrica.crear_validador()
        self._notificador = fabrica.crear_notificador()
        if self._validador.sede != self._notificador.sede:
            raise ValueError('Familia de sede incompatible.')

    def validar_horario(self, intervalo):
        self._validador.validar(intervalo)

    def notificar(self, mensaje, emitir):
        self._notificador.notificar(mensaje, emitir)


class Sede:
    def __init__(self, codigo):
        if codigo == 'Norte':
            fabrica = FabricaNorte()
        elif codigo == 'Sur':
            fabrica = FabricaSur()
        else:
            raise ValueError('Sede desconocida.')
        self.codigo = codigo
        self.servicios = ServiciosSede(fabrica)

    def validar_horario(self, intervalo):
        self.servicios.validar_horario(intervalo)

    def notificar(self, mensaje, emitir):
        self.servicios.notificar(mensaje, emitir)


class ReservaRecurrenteBuilder:
    def __init__(self, solicitante, cancha, intervalo):
        self.solicitante = solicitante
        self.cancha = cancha
        self.intervalo = intervalo
        self._semanas = 2
        self._equipo = []
        self._notas = ''

    def semanas(self, numero):
        self._semanas = numero
        return self

    def equipo(self, elementos):
        self._equipo = list(elementos)
        return self

    def notas(self, texto):
        self._notas = texto
        return self

    def build(self):
        if not isinstance(self.solicitante, Capitan):
            raise ValueError('Solo un capitan puede reservar recurrentemente.')
        if type(self._semanas) is not int or not 2 <= self._semanas <= 8:
            raise ValueError('La recurrencia requiere entre 2 y 8 semanas enteras.')
        self.intervalo.validar()
        return ReservaRecurrente(self.solicitante, self.cancha, self.intervalo,
                                self._semanas, list(self._equipo), self._notas)

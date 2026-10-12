"""Singleton y estrategias de negocio de ReservaU."""
from abc import ABC, abstractmethod
from datetime import time, timedelta
from threading import Lock


class ConfiguracionReglas:
    _instancia = None
    _lock = Lock()

    def __init__(self):
        self.limite_prioridad = time(18)
        self.horas_estudiante = 2
        self.horas_capitan = 24
        self.limite_no_shows = 3
        self.dias_suspension = 7

    @staticmethod
    def obtener_instancia():
        # Igual que el Singleton del laboratorio, protegido para usar dos hilos.
        with ConfiguracionReglas._lock:
            if ConfiguracionReglas._instancia is None:
                ConfiguracionReglas._instancia = ConfiguracionReglas()
            return ConfiguracionReglas._instancia


class PoliticaPrioridad(ABC):
    @abstractmethod
    def tiene_prioridad(self, inicio):
        pass


class PrioridadRegular(PoliticaPrioridad):
    def tiene_prioridad(self, inicio):
        return False


class PrioridadCapitan(PoliticaPrioridad):
    def tiene_prioridad(self, inicio):
        reglas = ConfiguracionReglas.obtener_instancia()
        return inicio.time() < reglas.limite_prioridad


class PoliticaCancelacion(ABC):
    @abstractmethod
    def evaluar(self, inicio, ahora):
        pass


class CancelacionEstudiante(PoliticaCancelacion):
    def evaluar(self, inicio, ahora):
        reglas = ConfiguracionReglas.obtener_instancia()
        ventana = timedelta(hours=reglas.horas_estudiante)
        if inicio - ahora < ventana:
            return 'NoShow'
        return 'Cancelada'


class CancelacionCapitan(PoliticaCancelacion):
    def evaluar(self, inicio, ahora):
        reglas = ConfiguracionReglas.obtener_instancia()
        ventana = timedelta(hours=reglas.horas_capitan)
        if inicio - ahora < ventana:
            return 'NoShow'
        return 'Cancelada'


class AnulacionSinPenalidad(PoliticaCancelacion):
    def evaluar(self, inicio, ahora):
        return 'Anulada'

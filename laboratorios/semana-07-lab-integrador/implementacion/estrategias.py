from abc import ABC, abstractmethod
from configuracion import GameConfig


def validarAtaque(ataqueBase):
    if type(ataqueBase) is not int or ataqueBase <= 0:
        raise ValueError('El ataque base debe ser un entero positivo.')


class EstrategiaAtaque(ABC):
    @abstractmethod
    def calcularDano(self, ataqueBase):
        pass


class AtaqueNormal(EstrategiaAtaque):
    def calcularDano(self, ataqueBase):
        validarAtaque(ataqueBase)
        return ataqueBase


class AtaqueFuerte(EstrategiaAtaque):
    def calcularDano(self, ataqueBase):
        validarAtaque(ataqueBase)
        configuracion = GameConfig.obtenerInstancia()
        return ataqueBase * configuracion.multiplicadorFuerte



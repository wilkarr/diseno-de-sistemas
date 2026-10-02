from abc import ABC, abstractmethod
from configuracion import GameConfig
from modelos import Guerrero, Dragon, Soldado, Alien, Mundo, TipoMundo


class FabricaPersonajes:
    def __init__(self):
        self.configuracion = GameConfig.obtenerInstancia()

    def crearPersonaje(self, tipo):
        if tipo not in self.configuracion.personajes:
            raise ValueError('Tipo de personaje desconocido.')
        datos = self.configuracion.personajes[tipo]
        if tipo == 'guerrero':
            return Guerrero(datos.nombre, datos.vida, datos.ataque)
        elif tipo == 'dragon':
            return Dragon(datos.nombre, datos.vida, datos.ataque)
        elif tipo == 'soldado':
            return Soldado(datos.nombre, datos.vida, datos.ataque)
        elif tipo == 'alien':
            return Alien(datos.nombre, datos.vida, datos.ataque)
        raise ValueError('Tipo de personaje desconocido.')


class FabricaMundo(ABC):
    def __init__(self):
        self.fabricaPersonajes = FabricaPersonajes()

    @abstractmethod
    def crearJugador(self):
        pass

    @abstractmethod
    def crearEnemigo(self):
        pass

    def crearMundo(self):
        return Mundo(self.tipo, (self.crearJugador(), self.crearEnemigo()))


class FabricaFantasia(FabricaMundo):
    tipo = TipoMundo.FANTASIA

    def crearJugador(self):
        return self.fabricaPersonajes.crearPersonaje('guerrero')

    def crearEnemigo(self):
        return self.fabricaPersonajes.crearPersonaje('dragon')


class FabricaCienciaFiccion(FabricaMundo):
    tipo = TipoMundo.CIENCIA_FICCION

    def crearJugador(self):
        return self.fabricaPersonajes.crearPersonaje('soldado')

    def crearEnemigo(self):
        return self.fabricaPersonajes.crearPersonaje('alien')


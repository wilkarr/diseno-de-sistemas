from consola import Consola
from fabricas import FabricaFantasia, FabricaCienciaFiccion
from estrategias import AtaqueNormal, AtaqueFuerte
from modelos import Combate, Partida, TipoMundo

class GameFacade:
    def __init__(self, consola=None):
        if consola is None:
            self.consola = Consola()
        else:
            self.consola = consola

    def _leerOpcion(self, mensaje, opciones):
        while True:
            opcion = self.consola.leer(mensaje).strip().lower()
            if opcion in opciones:
                return opcion
            self.consola.mostrar('Opcion invalida. Intenta nuevamente.')

    def seleccionarMundo(self):
        self.consola.mostrar('Mundos: 1. Fantasia | 2. Ciencia ficcion')
        opcion = self._leerOpcion('Elige el mundo: ', ['1', '2'])
        if opcion == '1':
            return TipoMundo.FANTASIA
        else:
            return TipoMundo.CIENCIA_FICCION

    def crearPartida(self, tipo):
        if tipo == TipoMundo.FANTASIA:
            fabrica = FabricaFantasia()
        elif tipo == TipoMundo.CIENCIA_FICCION:
            fabrica = FabricaCienciaFiccion()
        else:
            raise ValueError('Tipo de mundo desconocido.')
        mundo = fabrica.crearMundo()
        jugador, enemigo = mundo.personajes
        return Partida(mundo, Combate(jugador, enemigo))

    def elegirEstrategia(self, jugador):
        self.consola.mostrar('Estrategias: 1. Ataque normal | 2. Ataque fuerte')
        opcion = self._leerOpcion('Elige la estrategia: ', ['1', '2'])
        if opcion == '1':
            estrategia = AtaqueNormal()
            nombre = 'Ataque normal'
        else:
            estrategia = AtaqueFuerte()
            nombre = 'Ataque fuerte'
        jugador.elegirEstrategia(estrategia)
        self.consola.mostrar(f'Estrategia elegida: {nombre}.')

    def jugarPartida(self, partida):
        partida.iniciarPartida()
        jugador, enemigo = partida.mundo.personajes
        self.consola.mostrar(f'Combate: {jugador.nombre} (vida {jugador.vida}, ataque {jugador.ataque}) '
                             f'contra {enemigo.nombre} (vida {enemigo.vida}, ataque {enemigo.ataque}).')
        while partida.estado == 'en_curso':
            cambiar = self._leerOpcion('¿Cambiar estrategia antes del turno? (s/n): ',
                                       ['s', 'n'])
            if cambiar == 's':
                self.elegirEstrategia(jugador)
            resultado = partida.combate.ejecutarTurno()
            self.consola.mostrar(f'Turno {resultado.numero}: {jugador.nombre} causa '
                                 f'{resultado.danoJugador} de dano. Vida de {enemigo.nombre}: '
                                 f'{resultado.vidaEnemigo}.')
            if resultado.danoEnemigo:
                self.consola.mostrar(f'{enemigo.nombre} causa {resultado.danoEnemigo} de dano. '
                                     f'Vida de {jugador.nombre}: {resultado.vidaJugador}.')
            else:
                self.consola.mostrar('El enemigo quedo sin vida y no puede responder.')
            if resultado.ganador is not None:
                self.consola.mostrar(f'Ganador: {resultado.ganador.nombre}.')
                partida.finalizarPartida()
                self.consola.mostrar('Partida finalizada.')
        return partida

    def iniciarJuego(self):
        self.consola.mostrar('LUCHAEA - Juego de combate por turnos')
        tipo = self.seleccionarMundo()
        partida = self.crearPartida(tipo)
        self.elegirEstrategia(partida.combate.jugador)
        return self.jugarPartida(partida)



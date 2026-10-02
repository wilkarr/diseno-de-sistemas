from juego import GameFacade
from modelos import TipoMundo


class ConsolaSimulada:
    def __init__(self, entradas, imprimir=True):
        self.entradas = entradas
        self.posicion = 0
        self.mensajes = []
        self.imprimir = imprimir

    def leer(self, mensaje):
        if self.posicion >= len(self.entradas):
            raise RuntimeError('La simulacion no tiene suficientes entradas.')
        respuesta = self.entradas[self.posicion]
        self.posicion += 1
        self.mostrar(f'{mensaje}{respuesta}')
        return respuesta

    def mostrar(self, mensaje):
        self.mensajes.append(mensaje)
        if self.imprimir:
            print(mensaje)


def simular(imprimir=True):
    escenarios = [
        ('Fantasia y ataque normal', ['1', '1'] + ['n'] * 20),
        ('Fantasia y ataque fuerte', ['1', '2'] + ['n'] * 20),
        ('Ciencia ficcion y cambio de estrategia', ['2', '1', 'n', 's', '2'] + ['n'] * 20),
        ('Entradas invalidas y correccion', ['x', '2', '?', '1', 'quizas', 'n', 's', 'z', '2'] + ['n'] * 20),
    ]
    resultados = []
    for nombre, entradas in escenarios:
        consola = ConsolaSimulada(entradas, imprimir)
        consola.mostrar(f'\n=== {nombre} ===')
        partida = GameFacade(consola).iniciarJuego()
        resultados.append((nombre, partida, consola))
    # Estado controlado para alcanzar la rama de derrota sin cambiar las reglas.
    consola = ConsolaSimulada(['n'] * 20, imprimir)
    consola.mostrar('\n=== Derrota del jugador (escenario alterno) ===')
    juego = GameFacade(consola)
    partida = juego.crearPartida(TipoMundo.FANTASIA)
    partida.combate.jugador.recibirDano(90)
    consola.mostrar('Preparacion de la prueba: Guerrero comienza herido con 10 de vida.')
    juego.jugarPartida(partida)
    resultados.append(('Derrota del jugador', partida, consola))
    return resultados


if __name__ == '__main__':
    simular()


"""(Singleton)."""
class DatosPersonaje:
    def __init__(self, nombre, vida, ataque):
        self.nombre = nombre
        self.vida = vida
        self.ataque = ataque


class GameConfig:
    _instancia = None

    def __init__(self):
        # Valores elegidos para el laboratorio; no eran visibles en las fotos.
        self.personajes = {
            'guerrero': DatosPersonaje('Guerrero', 100, 20),
            'dragon': DatosPersonaje('Dragon', 120, 15),
            'soldado': DatosPersonaje('Soldado', 100, 25),
            'alien': DatosPersonaje('Alien', 90, 18),
        }
        self.multiplicadorFuerte = 2

    @staticmethod
    def obtenerInstancia():
        # Igual que obtener_Objeto() del Singleton de semana-05.
        if GameConfig._instancia is None:
            GameConfig._instancia = GameConfig()
        return GameConfig._instancia



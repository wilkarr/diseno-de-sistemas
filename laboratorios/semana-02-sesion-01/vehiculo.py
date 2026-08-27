# Vehiculo -> mueva - mover()

# Auto -> mueve por carretera
# Bote -> mueve por mar
# Avion -> mueve por cielo

class ComportamientoMovimiento:
    def mover(self):
        raise NotImplementedError

class MuevePorCarretera(ComportamientoMovimiento):
    def mover(self):
        print ("Conduciendo por carretera")
        
class MuevePorMar(ComportamientoMovimiento):
    def mover(self):
        print ("Navegando por agua")
        
class MuevePorCielo(ComportamientoMovimiento):
    def mover(self):
        print ("Volando por el aire")
        
class Vehiculo:
    def __init__(self, Comportamiento_Movimiento):
        self.comportamiento_movimiento = Comportamiento_Movimiento
        
    def mover(self):
        self.comportamiento_movimiento.mover()
        
class Auto(Vehiculo):
    def __init__(self):
        mueve_por_carretera = MuevePorCarretera()
        super().__init__(mueve_por_carretera)
        
class Bote(Vehiculo):
    def __init__(self):
        mueve_por_mar = MuevePorMar()
        super().__init__(mueve_por_mar)
        
class Avion(Vehiculo):
    def __init__(self):
        mueve_por_cielo = MuevePorCielo()
        super().__init__(mueve_por_cielo)

if __name__ == "__main__":
    auto = Auto()
    auto.mover()
    
    print()
    
    bote = Bote()
    bote.mover()
    print()
    
    avion = Avion()
    avion.mover()
    
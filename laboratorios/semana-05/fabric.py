class Estudiante:
    def __init__(self, nombre):
        self.nombre = nombre

class EquipoOficial(Estudiante): # Capitan hereda de Estudiante
    def __init__(self, nombre):
        super().__init__(nombre)

class ReservaPrioridad:
    def __init__(self, cancha, fecha, hora_inicio, hora_fin, solicitante):
        self.cancha = cancha
        self.fecha = fecha
        self.solicitante = solicitante
        
        pass
    def confirmar(self):
        print('Se asigno reserva PRIORITARIA a ' + self.solicitante.nombre)

class ReservaRegular:
    def __init__(self, cancha, fecha, hora_inicio, hora_fin, solicitante):
        # Ajusta los parámetros según necesites
        self.cancha = cancha
        self.fecha = fecha
        self.solicitante = solicitante
        pass
    def confirmar(self):
        print('Se asigno reserva REGULAR a ' + self.solicitante.nombre)
    

class CreadorDeReserva():
    def crear_reserva (self, cancha, fecha, hora_inicio, hora_fin, solicitante):
        raise NotImplementedError
    
class CreadorDeReservaRegular(CreadorDeReserva):
    def crear_reserva(self, cancha, fecha, hora_inicio, hora_fin, solicitante):
        return ReservaRegular(cancha, fecha, hora_inicio, hora_fin, solicitante)

class CreadorDeReservaPrioritaria(CreadorDeReserva):
    def crear_reserva(self, cancha, fecha, hora_inicio, hora_fin, solicitante):
        return ReservaPrioridad(cancha, fecha, hora_inicio, hora_fin, solicitante)
    
class FabricaDeReservas():
    @staticmethod
    def elegirCreador(solicitante):
        if isinstance(solicitante, EquipoOficial):
            return CreadorDeReservaRegular()
        elif isinstance(solicitante, Estudiante):
            return CreadorDeReservaPrioritaria()
        
def reservar_desde_web(cancha, fecha, hora_inicio, hora_fin, solicitante):
    creador = FabricaDeReservas.elegirCreador(solicitante)
    reserva = creador.crear_reserva(
        cancha,
        fecha, 
        hora_inicio,
        hora_fin, 
        solicitante
    )
    return reserva

def main():
    reserva1=reservar_desde_web('Cancha de futbol', 
                       '2026-09-17', '18:00', 
                       '20:00', Estudiante('Erick'))
    
    reserva1.confirmar()
    
    reserva2= reservar_desde_web('Cancha de futbol', 
                           '2026-09-17', '18:00', 
                           '20:00', EquipoOficial('ErickCapitan'))
    
    reserva2.confirmar()
    

if(__name__=="__main__"):
    main()



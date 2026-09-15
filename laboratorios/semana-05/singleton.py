class GestorDeConfiguracion:
    _objeto = None
    
    def __init__(self):
        self.modo_mantenimiento = False
        GestorDeConfiguracion._objeto = self
        
    @staticmethod
    def obtener_Objeto ():
        if GestorDeConfiguracion._objeto is None:
            GestorDeConfiguracion()
        
        return GestorDeConfiguracion._objeto
    
def reserva_permitida(gestor):
    return not gestor.modo_mantenimiento
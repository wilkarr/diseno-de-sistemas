from singleton import GestorDeConfiguracion, reserva_permitida

def test_rechaza_reserva():
    config = GestorDeConfiguracion.obtener_Objeto()
    config.modo_mantenimiento = True
    
    assert reserva_permitida(config) is False
    
def test_reserva_aceptada():
    config = GestorDeConfiguracion.obtener_Objeto()
    
    assert reserva_permitida(config) is False

# No pasaba la segunda prueba porque en la primera prueba se modifico modo_mantenimiento
# a True y al momento de probar assert reserva_permitida en la segunda llamanos a 
# GestorDeConfiguracion que seguia manteniendo el atributo en True porque llamo a la 
# misma instancia de GestorDeConfiguracion. Eso es debido a como se dijo en la lectura, 
# el singleton funciona como una variable global y cualquier parte del codigo puede modificarlo
# lo cual puede traer problemas como se evidencio en este test

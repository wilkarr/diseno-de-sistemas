class Inventario: 
    def verificar(self, producto):
        print(f'Verficando el stock del {producto}')
        return True

class Pago: 
    def procesar(self, monto):
        print(f'Procesando pago: {monto}')
        return True
    
class Envio: 
    def crear_envio(self, producto):
        print(f'Preparando el envio del {producto}')
        return True
class Notificacion:
    def notificar(self, producto):
        print(f'Not -->Se realizo la compra del producto {producto}')
        return True
class TiendaFacade:
    def __init__(self):
        self.inventario = Inventario()
        self.pago = Pago()
        self.envio = Envio()
        self.notificacion = Notificacion()
        
    def comprar(self, producto, precio):
        if not self.inventario.verificar(producto):
            print('No hay stock')
            return
        
        if not self.pago.procesar(precio):
            print('Fallo el pago')
            return
        
        if not self.envio.crear_envio(producto):
            print('No llego el envio')
            return
        
        if not self.notificacion.notificar(producto):
            print('-->No Se realizo la compra')
            return
        
def main():
    tienda = TiendaFacade()
    tienda.comprar('Laptop', 200)
    
main()
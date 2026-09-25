from abc import ABC, abstractmethod

class EstrategiaDescuento (ABC):
    @abstractmethod
    def aplicar(self, precio_base):
        pass

class SinDescuento (EstrategiaDescuento):
    def aplicar(self, precio_base):
        return precio_base
    
class DescuentoVIP(EstrategiaDescuento):
    def aplicar(self, precio_base):
        return precio_base*0.80
    
class DescuentoEstudiante(EstrategiaDescuento):
    def aplicar(self, precio_base):
        return precio_base*0.95

class DescuentoEmpleado(EstrategiaDescuento):
    def aplicar(self, precio_base):
        return  precio_base*0.75

class Compra: 
    def __init__(self, estrategiaDescuento):
        self.estrategiaDescuento = estrategiaDescuento
        
    def calcular_total(self, precio):
        return self.estrategiaDescuento.aplicar(precio)
    
def main():
    
     
    compra_1  = Compra(SinDescuento())
    compra_2 = Compra(DescuentoEstudiante())
    compra_3 = Compra(DescuentoVIP())
    compra_4 = Compra(DescuentoEmpleado())
     
    print(compra_1.calcular_total(100)) 
    print(compra_2.calcular_total(500)) 
    print(compra_3.calcular_total(1000))
    print(compra_4.calcular_total(1000))
       
main() 
    
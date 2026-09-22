from abc import ABC,abstractmethod
class Boton(ABC):
    @abstractmethod
    def renderizar(self):
        pass

class Menu(ABC):
    @abstractmethod
    def renderizar(self):
        pass

class CheckBox(ABC):
    @abstractmethod
    def renderizar(self):
        pass
    
class BotonWindows(Boton):
    def renderizar(self):
        print('Boton estilo Windows')
        
class CheckBoxWindows(CheckBox):
    def renderizar(self):
        print('CheckBox estilo windows..')
        
class CheckBoxMac(CheckBox):
    def renderizar(self):
        print('CheckBox estilo Mac..')
        
class BotonMac(Boton):
    def renderizar(self):
        print('Boton MAC')

class MenuWindows(Menu):
    def renderizar(self):
        print('Menu estilo Windows')
        
class MenuMac(Menu):
    def renderizar(self):
        print('Menu estilo mac')
        
class UIFactoryABC(ABC):
    @abstractmethod
    def crear_boton(self):
        pass
    @abstractmethod
    def crear_menu(self):
        pass
    @abstractmethod
    def crear_checkBox(self):
        pass

class WindowsFactory(UIFactoryABC):
    def crear_boton(self):
        return BotonWindows()
    def crear_menu(self):
        return MenuWindows()
    def crear_checkBox(self):
        return CheckBoxWindows()

class MacFactory(UIFactoryABC):
    def crea_boton(self):
        return BotonMac()
    def crear_menu(self):
        return MenuMac()
    def crear_checkBox(self):
        return CheckBoxMac()

def crearUI(factory):
    boton = factory.crear_boton()
    menu = factory.crear_menu()
    checkBox = factory.crear_checkBox()
    
    boton.renderizar()
    menu.renderizar()
    checkBox.renderizar()
    
def main():
    sistema = 'Windows'
    if sistema == 'Windows':
        factory = WindowsFactory()
         
    elif sistema == 'Mac':
        factory = MacFactory()
    
    crearUI(factory)
    
main()
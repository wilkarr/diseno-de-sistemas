from abc import ABC, abstractmethod
from datetime import datetime, timedelta


# PATRÓN DE COMPOSICION: Políticas de Prioridad
class PoliticaPrioridad(ABC):
    @abstractmethod
    def tiene_prioridad(self, hora_inicio: datetime) -> bool:
        pass

class PrioridadCapitan(PoliticaPrioridad):
    def tiene_prioridad(self, hora_inicio: datetime) -> bool:
        # Regla: Los equipos oficiales tienen prioridad antes de las 6:00 p.m. (18:00)
        return hora_inicio.hour < 18

class PrioridadRegular(PoliticaPrioridad):
    def tiene_prioridad(self, hora_inicio: datetime) -> bool:
        # Regla: Estudiantes regulares nunca tienen prioridad
        return False

# ENTIDADES BASE
class Disponibilidad:
    def __init__(self, fecha_inicio: datetime, fecha_hora_fin: datetime):
        self._fecha_inicio = fecha_inicio
        self._fecha_hora_fin = fecha_hora_fin

    @property
    def fecha_inicio(self):
        return self._fecha_inicio

    def es_horario_prioritario(self) -> bool:
        return self._fecha_inicio.hour < 18

class Cancha:
    def __init__(self, codigo: str, deporte: str):
        self.codigo = codigo
        self.deporte = deporte
        self._esta_disponible = True

    def esta_disponible(self) -> bool:
        return self._esta_disponible

    def set_disponibilidad(self, estado: bool):
        self._esta_disponible = estado

# ENTIDAD RESERVA _Modelo Rico
class Reserva:
    def __init__(self, id_reserva: str, disponibilidad: Disponibilidad, cancha: Cancha):
        self.__id = id_reserva
        self.__estado = "Pendiente"
        self.__fecha_creacion = datetime.now()
        self.__disponibilidad = disponibilidad
        self.cancha = cancha

    def get_id(self):
        return self.__id
        
    def get_estado(self):
        return self.__estado

    def confirmar(self):
        self.__estado = "Confirmada"
        self.cancha.set_disponibilidad(False)
        print(f"Sistema: Reserva {self.__id} creada y confirmada exitosamente.")

    def cancelar(self, hora_actual: datetime):
        print(f"Sistema: Procesando cancelacion para reserva {self.__id} a las {hora_actual.strftime('%H:%M')}...")
        tiempo_restante = self.__disponibilidad.fecha_inicio - hora_actual
        
        #Regla
        if tiempo_restante < timedelta(hours=2):
            self.__estado = "No-Show"
            print("Sistema: [Regla 2 Horas] Falta menos de 2 horas. Se registra como NO-SHOW.")
        else:
            self.__estado = "Cancelada"
            self.cancha.set_disponibilidad(True)
            print("Sistema: [Regla 2 Horas] Tiempo suficiente. Se realiza CANCELACION NORMAL.")

    def resolver_conflicto(self, nuevo_estado: str):
        self.__estado = nuevo_estado
        print(f"Sistema: Estado de la reserva {self.__id} modificado a '{self.__estado}' por el Administrador.")
        if nuevo_estado == "Cancelada":
            self.cancha.set_disponibilidad(True)


# ACTORES DEL SISTEMA

class Estudiante:
    def __init__(self, codigo_estud: str, politica: PoliticaPrioridad):
        self.codigo_estud = codigo_estud
        self.politica = politica

    def solicitar_reserva(self, cancha: Cancha, disponibilidad: Disponibilidad):
        print(f"\n[{self.codigo_estud}] solicita reserva en cancha {cancha.codigo} a las {disponibilidad.fecha_inicio.strftime('%H:%M')}.")
        
        if not cancha.esta_disponible():
            print("Sistema: La cancha no está disponible. Informando rechazo al usuario.")
            return None

        # Evaluamos la regla de prioridad
        tiene_prioridad = self.politica.tiene_prioridad(disponibilidad.fecha_inicio)
        if tiene_prioridad:
            print("Sistema: Regla aplicada -> Preferencia de Capitán otorgada antes de las 6:00 p.m.")
        else:
            print("Sistema: Regla aplicada -> Reserva de estudiante regular (sin prioridad).")

        reserva = Reserva(f"RES-{self.codigo_estud[-3:]}", disponibilidad, cancha)
        reserva.confirmar()
        return reserva

class Equipo:
    def __init__(self, nombre: str, deporte: str):
        self.nombre = nombre
        self.deporte = deporte

class Capitan(Estudiante):
    def __init__(self, codigo_estud: str, equipo: Equipo):
        # Inyectamos la política del capitán al constructor padre
        super().__init__(codigo_estud, PrioridadCapitan())
        self.equipo = equipo

class Administrador:
    def __init__(self, codigo_admin: str):
        self.codigo_admin = codigo_admin

    def gestionar_cancha(self, cancha: Cancha, estado: bool):
        print(f"\n[Admin {self.codigo_admin}] actualizando cancha {cancha.codigo}. Disponible: {estado}")
        cancha.set_disponibilidad(estado)
        print("Sistema: Se actualiza la informacion de la cancha. Confirmacinn enviada.")

    def intervenir_reserva(self, reserva: Reserva, nuevo_estado: str):
        print(f"\n[Admin {self.codigo_admin}] interviene en reserva {reserva.get_id()} por conflicto.")
        reserva.resolver_conflicto(nuevo_estado)
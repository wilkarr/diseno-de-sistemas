from datetime import datetime
from modelos import Disponibilidad, Cancha, Estudiante, PrioridadRegular, Capitan, Equipo, Administrador

def ejecutar_simulacion():
    print("=== INICIANDO SIMULACIÓN RESERVAU ===\n")
    
    # 1. Instancias iniciales
    admin = Administrador("ADM-001")
    cancha_futbol = Cancha("C-FUT-01", "Fútbol")
    cancha_tenis = Cancha("C-TEN-01", "Tenis")
    
    estudiante_regular = Estudiante("EST-111", PrioridadRegular())
    equipo_tigres = Equipo("Tigres USFQ", "Fútbol")
    capitan = Capitan("CAP-999", equipo_tigres)

    # Horarios de prueba
    fecha_base = datetime(2026, 9, 10, 15, 0) # 3:00 PM (Antes de las 6:00 PM)
    disp_3pm = Disponibilidad(fecha_base, datetime(2026, 9, 10, 16, 0))
    disp_7pm = Disponibilidad(datetime(2026, 9, 10, 19, 0), datetime(2026, 9, 10, 20, 0))

    # CASO DE USO 1: Reservar Cancha (Flujos Principal y Alterno)
    print("--- CU1: RESERVAR CANCHA ---")
    # El capitán reserva a las 3:00 PM (Aplica regla prioridad)
    reserva_cap = capitan.solicitar_reserva(cancha_futbol, disp_3pm)
    
    # El estudiante intenta reservar la MISMA cancha a las 3:00 PM (Flujo alterno: Ocupada)
    res_fallida = estudiante_regular.solicitar_reserva(cancha_futbol, disp_3pm)
    
    # El estudiante reserva otra cancha a las 7:00 PM (Después de las 6:00 PM, regular)
    reserva_est = estudiante_regular.solicitar_reserva(cancha_tenis, disp_7pm)

    # CASO D USO 2: Cancelar Reserva (Regla No-Show vs Normal)

    print("\n--- CU2: CANCELAR RESERVA ---")
    # Flujo Alterno (No-Show): Cancela faltando 1 hora para el juego
    hora_intento_tarde = datetime(2026, 9, 10, 14, 0) # Faltan solo 1h para las 15:00
    reserva_cap.cancelar(hora_intento_tarde)

    # Flujo Principal (Cancelación Normal): Cancela faltando 5 horas
    hora_intento_temprano = datetime(2026, 9, 10, 14, 0) # Faltan 5h para las 19:00
    reserva_est.cancelar(hora_intento_temprano)

    # CASO DE USO 3: Gestionar Canchas
    
    print("\n--- CU3: GESTIONAR CANCHAS ---")
    # El admin desactiva una cancha por mantenimiento
    admin.gestionar_cancha(cancha_futbol, False)

    
    # CASO DE USO 4: Resolver Conflictos de Reservas
    print("\n--- CU4: RESOLVER CONFLICTOS ---")
    # El admin restaura el estado "Cancelada" de la reserva del capitan tras un reclamo justificado
    admin.intervenir_reserva(reserva_cap, "Cancelada (Justificada)")

    print("\n=== SIMULACION FINALIZADA ===")

if __name__ == "__main__":
    ejecutar_simulacion()
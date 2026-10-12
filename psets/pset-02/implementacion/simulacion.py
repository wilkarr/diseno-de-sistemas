"""Escenarios verificables del enunciado; todas las operaciones pasan por la Facade."""
from datetime import datetime, timedelta
from threading import Barrier, Thread
from time import perf_counter
import platform

from modelos import Cancha, Intervalo, Estudiante, Capitan, EquipoOficial, Administrador, Bloqueo
from creacion import Sede, ReservaRecurrenteBuilder
from facade import ReservaUFacade
from politicas import ConfiguracionReglas


AHORA = datetime(2026, 11, 1, 8)
ADMIN = Administrador('ADM-001')


class ConsolaReserva:
    """Frontera de los diagramas: comunica las solicitudes solo a la Facade."""
    def __init__(self, facade):
        self.facade = facade

    def solicitar_reserva(self, solicitante, cancha, intervalo, ahora):
        return self.facade.reservar(solicitante, cancha, intervalo, ahora)

    def solicitar_cancelacion(self, reserva_id, actor, ahora, motivo=''):
        return self.facade.cancelar(reserva_id, actor, ahora, motivo)


def franja(dias=1, hora=15, minutos=0, duracion=60):
    inicio = (AHORA + timedelta(days=dias)).replace(hour=hora, minute=minutos)
    return Intervalo(inicio, inicio + timedelta(minutes=duracion))


def entorno(emitir=print):
    norte, sur = Sede('Norte'), Sede('Sur')
    canchas = [Cancha('N1', 'Futbol', norte), Cancha('N2', 'Tenis', norte),
               Cancha('S1', 'Futbol', sur)]
    return ReservaUFacade(canchas, emitir), canchas


def titulo(texto):
    print('\n' + '=' * 70 + '\n' + texto + '\n' + '=' * 70)


def competir(app, barrera, resultados, numero):
    barrera.wait(timeout=10)
    estudiante = Estudiante(f'EST-HILO-{numero+1}')
    resultados[numero] = app.reservar(estudiante, 'N1', franja(), AHORA)


def no_imprimir(mensaje):
    pass


def simular():
    titulo('1. RESERVAS POR SEDE Y 2. HORARIO FUERA DE SEDE')
    app, canchas = entorno()
    consola = ConsolaReserva(app)
    estudiante = Estudiante('EST-001')
    norte = consola.solicitar_reserva(estudiante, 'N1', franja(hora=6), AHORA)
    sur = consola.solicitar_reserva(estudiante, 'S1', franja(hora=22), AHORA)
    fuera = consola.solicitar_reserva(estudiante, 'S1', franja(hora=6), AHORA)
    assert norte.exito and sur.exito and not fuera.exito
    assert len(app.consultar_historial(ADMIN, 'S1')) == 1

    titulo('3. RECURRENCIA EXITOSA Y RECHAZO COMPLETO EN SEMANA 3')
    capitan = Capitan('CAP-001', EquipoOficial('Tigres', 'Futbol'))
    builder = ReservaRecurrenteBuilder(capitan, canchas[0], franja(dias=4))
    serie = app.reservar_recurrente(builder.semanas(3).equipo(['balones']).notas('Abrir vestidor'), AHORA)
    assert serie.exito and len(serie.serie.reservas) == 3
    app.reservar(estudiante, 'N2', franja(dias=18), AHORA)
    previo = len(app.consultar_historial(ADMIN, 'N2'))
    fallida = app.reservar_recurrente(
        ReservaRecurrenteBuilder(capitan, canchas[1], franja(dias=4)).semanas(4), AHORA)
    assert not fallida.exito and 'Semana 3' in fallida.motivo
    assert len(app.consultar_historial(ADMIN, 'N2')) == previo
    print('VALIDACION: serie rechazada; cero reservas nuevas; regular existente intacta.')

    titulo('4. CANCELACION REGULAR, CAPITAN TARDIO Y ANULACION ADMINISTRATIVA')
    app, _ = entorno()
    consola = ConsolaReserva(app)
    regular = app.reservar(estudiante, 'N1', franja(), AHORA).reserva
    equipo = app.reservar(capitan, 'N2', franja(hora=16), AHORA).reserva
    administrativa = app.reservar(estudiante, 'S1', franja(hora=17), AHORA).reserva
    assert consola.solicitar_cancelacion(regular.id, estudiante, regular.intervalo.inicio-timedelta(hours=2)).reserva.estado == 'Cancelada'
    assert consola.solicitar_cancelacion(equipo.id, capitan, equipo.intervalo.inicio-timedelta(hours=23)).reserva.estado == 'NoShow'
    assert consola.solicitar_cancelacion(administrativa.id, ADMIN, AHORA, 'mantenimiento').reserva.estado == 'Anulada'
    assert len(estudiante.no_shows) == 0 and len(capitan.no_shows) == 1

    titulo('5. TRES NO-SHOWS EN UN MES: SUSPENSION, RECHAZO Y VENCIMIENTO')
    app, _ = entorno()
    reincidente = Estudiante('EST-REINCIDENTE')
    reservas = []
    for i in range(3):
        intervalo = franja(hora=12, minutos=i*20, duracion=10)
        resultado = app.reservar(reincidente, 'N1', intervalo, AHORA)
        reservas.append(resultado.reserva)
    tarde = franja(hora=11).inicio
    for reserva in reservas:
        assert app.cancelar(reserva.id, reincidente, tarde).reserva.estado == 'NoShow'
    assert not app.reservar(reincidente, 'N2', franja(dias=2), tarde).exito
    assert not app.cancelar(reservas[0].id, reincidente, tarde).exito
    assert len(reincidente.no_shows) == 3
    reglas = ConfiguracionReglas.obtener_instancia()
    vencimiento = tarde + timedelta(days=reglas.dias_suspension)
    assert app.reservar(reincidente, 'N2', franja(dias=10), vencimiento).exito
    print('VALIDACION: al vencer exactamente 7 dias se permite reservar; cancelacion repetida no duplica penalidad.')
    diciembre = datetime(2026, 12, 1, 8)
    reserva_dic = app.reservar(reincidente, 'N2', Intervalo(datetime(2026,12,2,12),datetime(2026,12,2,13)), diciembre).reserva
    app.cancelar(reserva_dic.id, reincidente, datetime(2026,12,2,11))
    assert reincidente.contar_no_shows(2026,11) == 3
    assert reincidente.contar_no_shows(2026,12) == 1
    assert not reincidente.esta_suspendido(datetime(2026,12,2,11))
    print('VALIDACION: diciembre comienza su propio recuento; noviembre queda en el historial.')

    titulo('6. BLOQUEO CLONADO: EQUIPO INDEPENDIENTE Y ANULACION SIN PENALIDAD')
    app, _ = entorno()
    afectado = Estudiante('EST-AFECTADO')
    existente = app.reservar(afectado, 'N1', franja(), AHORA).reserva
    plantilla = Bloqueo('Torneo universitario', franja(), ['red', 'balones'])
    resultado = app.bloquear(ADMIN, plantilla, [('N1',franja().inicio.date()), ('N2',franja(dias=2).inicio.date())], AHORA)
    assert resultado.exito and existente.estado == 'Anulada'
    assert not afectado.no_shows
    resultado.clones[0].equipo.append('chalecos')
    assert 'chalecos' not in plantilla.equipo and 'chalecos' not in resultado.clones[1].equipo
    assert not app.consultar_disponibilidad('N1', franja())
    print('VALIDACION: plantilla y segundo clon conservan su equipo; bloqueo impide reservar.')

    titulo('7. DOS HILOS COMPITEN: EXACTAMENTE UNA CONFIRMACION')
    app, _ = entorno()
    barrera = Barrier(2)
    resultados = [None, None]

    hilos = []
    for i in range(2):
        hilo = Thread(target=competir, args=(app, barrera, resultados, i),
                      name=f'solicitud-{i+1}')
        hilos.append(hilo)
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=10)
        assert not hilo.is_alive(), 'Hilo no termino.'
    confirmadas = 0
    for resultado in resultados:
        assert resultado is not None, 'Error en un hilo.'
        if resultado.exito:
            confirmadas += 1
    assert confirmadas == 1
    assert len(app.consultar_historial(ADMIN, 'N1')) == 1
    print('VALIDACION: una confirmacion, un rechazo y una reserva registrada.')

    titulo('8. FEEDBACK PSET 1: PRIORIDAD EFECTIVA Y HORARIOS INDEPENDIENTES')
    app, _ = entorno()
    regular = app.reservar(estudiante, 'N1', franja(), AHORA).reserva
    equipo = app.reservar(capitan, 'N1', franja(), AHORA).reserva
    assert regular.estado == 'Anulada' and equipo.estado == 'Confirmada'
    assert not estudiante.no_shows
    assert not app.reservar(estudiante, 'N1', franja(), AHORA).exito
    assert app.reservar(estudiante, 'N1', franja(hora=19), AHORA).exito
    assert app.reservar(estudiante, 'N2', franja(hora=18), AHORA).exito
    assert not app.reservar(capitan, 'N2', franja(hora=18), AHORA).exito
    assert not app.cancelar(equipo.id, estudiante, AHORA).exito
    puntual = app.reservar(capitan, 'S1', franja(dias=5), AHORA).reserva
    assert app.cancelar(puntual.id, capitan, puntual.intervalo.inicio-timedelta(hours=24)).reserva.estado == 'Cancelada'
    app.gestionar_cancha(ADMIN, 'N1', False)
    normal = app.reservar(estudiante, 'N2', franja(dias=5), AHORA).reserva
    app.gestionar_cancha(ADMIN, 'N2', False)
    app.cancelar(normal.id, estudiante, AHORA)
    assert not app.consultar_disponibilidad('N2', franja(dias=5))
    print('VALIDACION: prioridad altera asignacion; limites exactos correctos; cancelar no reactiva mantenimiento.')

    titulo('9. ALTERNATIVAS: GESTION, CONFLICTOS, INTERVALOS Y BUILDER')
    app, canchas = entorno()
    assert app.gestionar_cancha(ADMIN, 'N3', deporte='Tenis', sede=Sede('Norte'), agregar=True).exito
    assert not app.gestionar_cancha(ADMIN, 'N3', deporte='Tenis', sede=Sede('Norte'), agregar=True).exito
    assert app.gestionar_cancha(ADMIN, 'N3', deporte='Voley').exito
    assert not app.gestionar_cancha(ADMIN, 'N3', False, confirmar=False).exito
    assert app.consultar_disponibilidad('N3', franja())
    primera = app.reservar(estudiante, 'N3', franja(), AHORA).reserva
    assert app.reservar(estudiante, 'N3', franja(hora=16), AHORA).exito
    assert app.resolver_conflicto(ADMIN, primera.id, AHORA, mantener=True).exito
    assert app.resolver_conflicto(ADMIN, primera.id, AHORA, confirmar=False).exito
    assert primera.estado == 'Confirmada'
    assert app.resolver_conflicto(ADMIN, primera.id, AHORA, motivo='revision administrativa').exito
    assert primera.estado == 'Anulada' and not estudiante.no_shows
    assert not app.resolver_conflicto(ADMIN, primera.id, AHORA, motivo='repetida').exito
    # Conflicto mixto: el capitan no puede anular la regular si tambien hay un bloqueo.
    regular = app.reservar(estudiante, 'N1', franja(duracion=30), AHORA).reserva
    plantilla = Bloqueo('Mantenimiento', franja(minutos=30,duracion=30), [])
    assert app.bloquear(ADMIN, plantilla, [('N1',franja().inicio.date())], AHORA).exito
    assert not app.reservar(capitan, 'N1', franja(), AHORA).exito
    assert regular.estado == 'Confirmada'
    assert app.reservar_recurrente(ReservaRecurrenteBuilder(capitan,canchas[1],franja(dias=4)), AHORA).exito
    assert not app.reservar_recurrente(ReservaRecurrenteBuilder(capitan,canchas[1],franja(dias=10)).semanas(9), AHORA).exito
    assert not app.reservar_recurrente(ReservaRecurrenteBuilder(estudiante,canchas[1],franja(dias=10)), AHORA).exito
    # La suspension tambien impide recurrencia antes de comenzar las validaciones semanales.
    suspendido = Capitan('CAP-SUSPENDIDO', EquipoOficial('Aguilas','Tenis'))
    reservas_suspendido = []
    for i in range(3):
        intervalo = franja(hora=10, minutos=i*20, duracion=10)
        resultado = app.reservar(suspendido, 'N2', intervalo, AHORA)
        reservas_suspendido.append(resultado.reserva)
    for reserva in reservas_suspendido:
        assert app.cancelar(reserva.id, suspendido, AHORA+timedelta(hours=3)).exito
    assert not app.reservar_recurrente(ReservaRecurrenteBuilder(suspendido,canchas[1],franja(dias=10)), AHORA+timedelta(hours=3)).exito
    print('VALIDACION: altas/modificaciones; conflictos sin reactivacion; franjas contiguas; prioridad sin anulaciones parciales; Builder por defecto y invalido; capitan suspendido.')

    titulo('10. MEDICION RNF-08: 100 CANCHAS, 1.000 RESERVAS, 100 CONSULTAS')
    sede = Sede('Norte')
    canchas = []
    for i in range(100):
        canchas.append(Cancha(f'PERF-{i}', 'Tenis', sede))
    app = ReservaUFacade(canchas, emitir=no_imprimir)
    cliente = Estudiante('EST-PERF')
    for cancha in canchas:
        for dia in range(1, 11):
            assert app.reservar(cliente, cancha.codigo, franja(dias=dia), AHORA).exito
    tiempos = []
    for cancha in canchas:
        inicio = perf_counter()
        assert app.consultar_disponibilidad(cancha.codigo, franja(dias=11))
        tiempos.append(perf_counter() - inicio)
    p95 = sorted(tiempos)[94]
    assert p95 < 1, f'RNF-08 incumplido: p95={p95:.6f}s'
    print(f'Plataforma: {platform.platform()}; Python {platform.python_version()}; CPU: {platform.machine()}')
    print(f'RNF-08: percentil 95 = {p95:.6f} s; 100/100 consultas disponibles; impresion excluida.')
    print('\nSIMULACION COMPLETA: todos los criterios ejecutados pasaron.')


if __name__ == '__main__':
    simular()

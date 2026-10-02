from estrategias import AtaqueNormal, EstrategiaAtaque


class TipoMundo:
    FANTASIA = 'fantasia'
    CIENCIA_FICCION = 'ciencia_ficcion'


class Personaje:
    def __init__(self, nombre, vida, ataque):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError('El personaje necesita un nombre.')
        if type(vida) is not int or vida <= 0:
            raise ValueError('La vida inicial debe ser un entero positivo.')
        if type(ataque) is not int or ataque <= 0:
            raise ValueError('El ataque debe ser un entero positivo.')
        self.nombre = nombre
        self.vida = vida
        self.ataque = ataque

    def recibirDano(self, cantidad):
        if type(cantidad) is not int or cantidad < 0:
            raise ValueError('El dano debe ser un entero no negativo.')
        self.vida = self.vida - cantidad
        if self.vida < 0:
            self.vida = 0
        return self.vida

    def _validarObjetivo(self, objetivo):
        if not isinstance(objetivo, Personaje):
            raise TypeError('El objetivo debe ser un personaje.')
        if objetivo is self:
            raise ValueError('Un personaje no puede atacarse a si mismo.')
        if self.vida <= 0 or objetivo.vida <= 0:
            raise ValueError('Ambos personajes deben tener vida para atacar.')

    def atacar(self, objetivo):
        self._validarObjetivo(objetivo)
        objetivo.recibirDano(self.ataque)
        return self.ataque


class Jugador(Personaje):
    def __init__(self, nombre, vida, ataque, estrategia=None):
        super().__init__(nombre, vida, ataque)
        if estrategia is None:
            estrategia = AtaqueNormal()
        self.elegirEstrategia(estrategia)

    def elegirEstrategia(self, estrategia):
        if not isinstance(estrategia, EstrategiaAtaque):
            raise TypeError('Se debe elegir una estrategia de ataque valida.')
        self.estrategia = estrategia

    def atacar(self, objetivo):
        self._validarObjetivo(objetivo)
        dano = self.estrategia.calcularDano(self.ataque)
        objetivo.recibirDano(dano)
        return dano


class Enemigo(Personaje):
    pass


class Guerrero(Jugador):
    pass


class Soldado(Jugador):
    pass


class Dragon(Enemigo):
    pass


class Alien(Enemigo):
    pass


class Mundo:
    def __init__(self, tipo, personajes):
        if tipo != TipoMundo.FANTASIA and tipo != TipoMundo.CIENCIA_FICCION:
            raise ValueError('Tipo de mundo desconocido.')
        if len(personajes) != 2:
            raise ValueError('El mundo debe contener exactamente dos personajes.')
        jugador = personajes[0]
        enemigo = personajes[1]
        if tipo == TipoMundo.FANTASIA:
            familiaValida = isinstance(jugador, Guerrero) and isinstance(enemigo, Dragon)
        else:
            familiaValida = isinstance(jugador, Soldado) and isinstance(enemigo, Alien)
        if not familiaValida:
            raise ValueError('Los personajes deben pertenecer a la familia del mundo.')
        self.tipo = tipo
        self.personajes = personajes


class ResultadoTurno:
    def __init__(self, numero, danoJugador, danoEnemigo, vidaJugador, vidaEnemigo, ganador):
        self.numero = numero
        self.danoJugador = danoJugador
        self.danoEnemigo = danoEnemigo
        self.vidaJugador = vidaJugador
        self.vidaEnemigo = vidaEnemigo
        self.ganador = ganador


class Combate:
    def __init__(self, jugador, enemigo):
        if not isinstance(jugador, Jugador) or not isinstance(enemigo, Enemigo):
            raise TypeError('El combate necesita un jugador y un enemigo.')
        self.jugador = jugador
        self.enemigo = enemigo
        self._iniciado = False
        self._terminado = False
        self._turno = 0

    def iniciarCombate(self):
        if self._iniciado:
            raise ValueError('El combate ya fue iniciado.')
        if self.jugador.vida <= 0 or self.enemigo.vida <= 0:
            raise ValueError('No se puede iniciar con personajes sin vida.')
        self._iniciado = True

    def determinarGanador(self):
        if self.enemigo.vida == 0 and self.jugador.vida > 0:
            return self.jugador
        if self.jugador.vida == 0 and self.enemigo.vida > 0:
            return self.enemigo
        return None

    def ejecutarTurno(self):
        if not self._iniciado or self._terminado:
            raise ValueError('El combate debe estar iniciado y sin terminar.')
        self._turno += 1
        danoJugador = self.jugador.atacar(self.enemigo)
        danoEnemigo = 0
        ganador = self.determinarGanador()
        if ganador is None:
            danoEnemigo = self.enemigo.atacar(self.jugador)
            ganador = self.determinarGanador()
        self._terminado = ganador is not None
        return ResultadoTurno(self._turno, danoJugador, danoEnemigo,
                              self.jugador.vida, self.enemigo.vida, ganador)


class Partida:
    def __init__(self, mundo, combate):
        jugador = mundo.personajes[0]
        enemigo = mundo.personajes[1]
        if combate.jugador is not jugador or combate.enemigo is not enemigo:
            raise ValueError('El combate debe usar los personajes de este mundo.')
        self.mundo = mundo
        self.combate = combate
        self.estado = 'pendiente'

    def iniciarPartida(self):
        if self.estado != 'pendiente':
            raise ValueError('La partida ya fue iniciada.')
        self.combate.iniciarCombate()
        self.estado = 'en_curso'

    def finalizarPartida(self):
        if self.estado != 'en_curso' or self.combate.determinarGanador() is None:
            raise ValueError('La partida solo finaliza cuando existe un ganador.')
        self.estado = 'finalizada'


"""Entidad (abstracta), Cliente, Servicio (abstracta) + 3 derivadas, Reserva."""
import re
from abc import ABC, abstractmethod
from datetime import datetime
from excepciones import *

PENDIENTE, CONFIRMADA, CANCELADA, PROCESADA = "PENDIENTE", "CONFIRMADA", "CANCELADA", "PROCESADA"


def texto(v, nombre):
    if v is None or not str(v).strip():
        raise ParametroFaltanteError(f"Falta el parámetro '{nombre}'")
    return str(v).strip()


def num(v, nombre, tipo=float):
    texto(v, nombre)
    try:
        return tipo(v)
    except (ValueError, TypeError) as e:
        raise DatoInvalidoError(f"'{nombre}' debe ser numérico: {v!r}", e) from e


class Entidad(ABC):
    """Clase abstracta base de Cliente, Servicio y Reserva."""
    _contadores = {}
    _categoria = "entidad"

    def __init__(self):
        self._id = None
        self._fecha_creacion = datetime.now()

    def asignar_id(self):
        c = Entidad._contadores.get(self._categoria, 0) + 1
        Entidad._contadores[self._categoria] = c
        self._id = c

    @property
    def id(self): return self._id

    def __eq__(self, o): return type(self) is type(o) and self._id == o._id
    def __hash__(self): return hash((self._categoria, self._id))
    def __str__(self): return self.describir()

    @abstractmethod
    def describir(self): ...


class Cliente(Entidad):
    _categoria = "cliente"

    def __init__(self, nombre=None, email=None, telefono=None, documento=None):
        super().__init__()
        self.nombre, self.email, self.telefono, self.documento = nombre, email, telefono, documento

    @property
    def nombre(self): return self._nombre
    @nombre.setter
    def nombre(self, v):
        v = texto(v, "nombre")
        if len(v) < 2 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+", v):
            raise DatoInvalidoError(f"Nombre inválido: {v!r}")
        self._nombre = v

    @property
    def email(self): return self._email
    @email.setter
    def email(self, v):
        v = texto(v, "email")
        if not re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", v):
            raise DatoInvalidoError(f"Email con formato inválido: {v!r}")
        self._email = v

    @property
    def telefono(self): return self._telefono
    @telefono.setter
    def telefono(self, v):
        v = texto(v, "teléfono")
        if not re.fullmatch(r"\d{7,12}", v):
            raise DatoInvalidoError(f"Teléfono inválido (7-12 dígitos): {v!r}")
        self._telefono = v

    @property
    def documento(self): return self._documento
    @documento.setter
    def documento(self, v):
        v = texto(v, "documento")
        if not re.fullmatch(r"[A-Za-z0-9]{5,15}", v):
            raise DatoInvalidoError(f"Documento inválido (5-15 alfanuméricos): {v!r}")
        self._documento = v

    def describir(self):
        return f"Cliente #{self.id}: {self._nombre} <{self._email}>"


class Servicio(Entidad, ABC):
    _categoria = "servicio"

    def __init__(self, nombre, tarifa, unidades=1):
        nombre = texto(nombre, "nombre")
        tarifa = num(tarifa, "tarifa")
        unidades = num(unidades, "unidades", int)
        if tarifa <= 0:
            raise DatoInvalidoError(f"La tarifa debe ser mayor que 0: {tarifa}")
        if unidades < 0:
            raise DatoInvalidoError(f"Las unidades no pueden ser negativas: {unidades}")
        super().__init__()
        self._nombre, self._tarifa, self._unidades = nombre, tarifa, unidades

    @property
    def nombre(self): return self._nombre
    @property
    def tarifa(self): return self._tarifa
    @property
    def unidades(self): return self._unidades
    def disponible(self): return self._unidades > 0

    def reservar_recurso(self):
        if not self.disponible():
            raise ServicioNoDisponibleError(f"'{self._nombre}' no tiene disponibilidad")
        self._unidades -= 1

    def liberar_recurso(self): self._unidades += 1

    @abstractmethod
    def calcular_costo_base(self, duracion): ...
    @abstractmethod
    def validar_parametros(self, duracion): ...

    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        """Sobrecarga por parámetros opcionales:
        calcular_costo(d) | (d, descuento=10) | (d, impuesto=19) | (d, 10, 19)"""
        desc, imp = num(descuento, "descuento"), num(impuesto, "impuesto")
        try:
            self.validar_parametros(duracion)
            if not 0 <= desc <= 100:
                raise CalculoCostoError(f"Descuento fuera de rango (0-100): {desc}")
            if imp < 0:
                raise CalculoCostoError(f"Impuesto negativo: {imp}")
            total = self.calcular_costo_base(duracion) * (1 - desc / 100) * (1 + imp / 100)
            if total < 0:
                raise CalculoCostoError("El costo calculado es negativo")
        except ErrorSoftwareFJ:
            raise
        except Exception as e:
            raise CalculoCostoError("Cálculo inconsistente", e) from e
        return round(total, 2)


class ReservaSala(Servicio):
    def __init__(self, nombre, tarifa_hora, capacidad, unidades=1):
        cap = num(capacidad, "capacidad", int)
        if cap <= 0:
            raise DatoInvalidoError(f"La capacidad debe ser mayor que 0: {cap}")
        super().__init__(nombre, tarifa_hora, unidades)
        self._capacidad = cap

    def validar_parametros(self, horas):
        if num(horas, "horas") <= 0:
            raise DatoInvalidoError("Las horas deben ser mayores que 0")

    def calcular_costo_base(self, horas):
        recargo = 1.2 if self._capacidad > 20 else 1.0
        return float(horas) * self._tarifa * recargo

    def describir(self):
        return f"Sala '{self._nombre}' (cap. {self._capacidad}) ${self._tarifa}/h"


class AlquilerEquipo(Servicio):
    def __init__(self, nombre, tarifa_dia, tipo_equipo, unidades):
        tipo = texto(tipo_equipo, "tipo de equipo")
        super().__init__(nombre, tarifa_dia, unidades)
        self._tipo = tipo

    def validar_parametros(self, dias):
        d = num(dias, "días")
        if d <= 0 or d != int(d):
            raise DatoInvalidoError("Los días deben ser un entero mayor que 0")

    def calcular_costo_base(self, dias): return float(dias) * self._tarifa

    def describir(self):
        return f"Equipo '{self._nombre}' ({self._tipo}) ${self._tarifa}/día, {self._unidades} u."


class Asesoria(Servicio):
    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre, tarifa_hora, especialidad, nivel, unidades=1):
        esp = texto(especialidad, "especialidad")
        nivel = texto(nivel, "nivel").lower()
        if nivel not in self.NIVELES:
            raise DatoInvalidoError(f"Nivel inexistente: {nivel!r} (use {list(self.NIVELES)})")
        super().__init__(nombre, tarifa_hora, unidades)
        self._especialidad, self._nivel = esp, nivel

    def validar_parametros(self, horas):
        if num(horas, "horas") <= 0:
            raise DatoInvalidoError("Las horas deben ser mayores que 0")

    def calcular_costo_base(self, horas):
        return float(horas) * self._tarifa * self.NIVELES[self._nivel]

    def describir(self):
        return f"Asesoría '{self._nombre}' ({self._especialidad}, {self._nivel}) ${self._tarifa}/h"


class Reserva(Entidad):
    _categoria = "reserva"

    def __init__(self, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido")
        duracion = num(duracion, "duración")
        servicio.validar_parametros(duracion)
        super().__init__()
        self._cliente, self._servicio, self._duracion = cliente, servicio, duracion
        self._estado, self._costo_final = PENDIENTE, None

    @property
    def cliente(self): return self._cliente
    @property
    def servicio(self): return self._servicio
    @property
    def duracion(self): return self._duracion
    @property
    def estado(self): return self._estado
    @property
    def costo_final(self): return self._costo_final

    def _ejecutar(self, accion, permitido, aplicar):
        try:
            if self._estado not in permitido:
                raise OperacionNoPermitidaError(
                    f"No se puede {accion} la reserva #{self.id} en estado {self._estado}")
            resultado = aplicar()
        except ErrorSoftwareFJ as e:
            log.warning(f"Reserva #{self.id}: {accion} rechazada ({type(e).__name__}: {e})")
            raise
        except Exception as e:
            raise ErrorInesperadoError(f"Fallo al {accion} la reserva", e) from e
        else:
            log.info(f"Reserva #{self.id}: {accion} correcto -> {self._estado}")
            return resultado
        finally:
            log.info(f"Reserva #{self.id}: fin de '{accion}'")

    def confirmar(self):
        def aplicar():
            self._servicio.reservar_recurso()
            self._estado = CONFIRMADA
        return self._ejecutar("confirmar", (PENDIENTE,), aplicar)

    def cancelar(self):
        def aplicar():
            if self._estado == CONFIRMADA:
                self._servicio.liberar_recurso()
            self._estado = CANCELADA
        return self._ejecutar("cancelar", (PENDIENTE, CONFIRMADA), aplicar)

    def procesar(self, descuento=0, impuesto=0):
        def aplicar():
            costo = self._servicio.calcular_costo(self._duracion, descuento, impuesto)
            self._costo_final = costo
            self._servicio.liberar_recurso()
            self._estado = PROCESADA
            return costo
        return self._ejecutar("procesar", (CONFIRMADA,), aplicar)

    def describir(self):
        return (f"Reserva #{self.id} | {self._cliente.nombre} | {self._servicio.nombre} | "
                f"{self._duracion:g} | {self._estado}")

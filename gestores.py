"""Módulo de gestores para Software FJ (Clientes, Servicios y Reservas).

Este archivo maneja toda la lógica de negocio del sistema, utilizando listas 
privadas en memoria para administrar las entidades definidas en modelos.py 
(sin usar bases de datos).

Buenas prácticas aplicadas en este módulo:
- Encapsulación: Las listas de datos son privadas (_clientes, _servicios, _reservas) 
  y cuando llaman a .listar(), devolvemos copias para evitar modificaciones externas no deseadas.
- Responsabilidad única: Cada gestor se encarga estrictamente de lo suyo y de un solo tipo de entidad.
- Manejo de errores: Cero prints directos ni caídas repentinas del programa; lanzamos 
  excepciones personalizadas que la función ejecutar_seguro() atrapa y registra ordenadamente en registro.log.
"""

from excepciones import (log, DatoInvalidoError, ParametroFaltanteError,
                         ReservaInvalidaError, ServicioNoDisponibleError)
from modelos import (Cliente, Servicio, Reserva, PENDIENTE, CONFIRMADA,
                     texto, num)


def _a_id(valor, nombre="id"):
    """Convierte un valor (int o str como '3' desde la GUI) en un ID entero positivo.

    Reutiliza num() de modelos.py (lanza ParametroFaltanteError / DatoInvalidoError)
    y evita que un decimal como 1.7 se trunque silenciosamente a 1.
    """
    if isinstance(valor, float) and not valor.is_integer():
        raise DatoInvalidoError(f"'{nombre}' debe ser un entero: {valor!r}")
    n = num(valor, nombre, int)
    if n <= 0:
        raise DatoInvalidoError(f"'{nombre}' debe ser mayor que 0: {n}")
    return n


class GestorClientes:
    """Administra el registro de clientes en memoria."""

    # Criterios válidos para la búsqueda (sobrecarga por criterio).
    CRITERIOS = ("id", "email", "nombre", "documento")

    def __init__(self):
        self._clientes = []  # lista interna privada

    def agregar(self, nombre=None, email=None, telefono=None, documento=None):
        """Registra un cliente. También acepta un objeto Cliente ya creado.

        Las validaciones de formato las hace el propio Cliente (setters);
        aquí solo se valida la regla de negocio: documento único.
        """
        if isinstance(nombre, Cliente):
            cliente = nombre
        else:
            # Si algún dato es inválido o falta, Cliente lanza la excepción
            # y el cliente NO se registra ni consume un ID.
            cliente = Cliente(nombre, email, telefono, documento)

        # Regla de negocio: no se permiten documentos duplicados.
        doc = cliente.documento.lower()
        if any(c.documento.lower() == doc for c in self._clientes):
            raise DatoInvalidoError(
                f"Ya existe un cliente con el documento {cliente.documento!r}")

        cliente.asignar_id()  # el ID se asigna solo cuando todo es válido
        self._clientes.append(cliente)
        log.info(f"Cliente registrado: {cliente.describir()}")
        return cliente

    def buscar(self, valor, criterio="id"):
        """Busca un cliente por 'id', 'email', 'nombre' o 'documento'.

        Ejemplos: buscar(1) | buscar("ana@mail.com", "email") |
                  buscar("Ana Gómez", "nombre") | buscar("10203040", "documento")
        Lanza DatoInvalidoError si el criterio es inválido o no hay coincidencia.
        """
        criterio = texto(criterio, "criterio").lower()
        if criterio not in self.CRITERIOS:
            raise DatoInvalidoError(
                f"Criterio de búsqueda inválido: {criterio!r} (use {list(self.CRITERIOS)})")

        if criterio == "id":
            buscado = _a_id(valor, "id de cliente")
            encontrados = [c for c in self._clientes if c.id == buscado]
        else:
            # Comparación sin distinguir mayúsculas/minúsculas.
            buscado = texto(valor, criterio).lower()
            encontrados = [c for c in self._clientes
                           if str(getattr(c, criterio)).lower() == buscado]

        if not encontrados:
            raise DatoInvalidoError(f"Cliente no encontrado ({criterio}={valor!r})")
        return encontrados[0]

    def listar(self):
        """Devuelve una copia de la lista (protege la lista interna)."""
        return list(self._clientes)


class GestorServicios:
    """Administra el catálogo de servicios en memoria."""

    def __init__(self):
        self._servicios = []

    def agregar(self, servicio):
        """Registra un servicio ya construido (ReservaSala, AlquilerEquipo, Asesoria)."""
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError(
                f"Solo se pueden registrar instancias de Servicio, no {type(servicio).__name__}")
        servicio.asignar_id()
        self._servicios.append(servicio)
        log.info(f"Servicio registrado: {servicio.describir()}")
        return servicio

    def buscar(self, id_servicio):
        """Busca un servicio por ID; lanza DatoInvalidoError si no existe."""
        buscado = _a_id(id_servicio, "id de servicio")
        for s in self._servicios:
            if s.id == buscado:
                return s
        raise DatoInvalidoError(f"Servicio no encontrado (id={buscado})")

    def listar(self):
        return list(self._servicios)


class GestorReservas:
    """Crea y administra reservas. Depende de los gestores de clientes y servicios
    (inyección de dependencias: los recibe en el constructor)."""

    # Estados en los que una reserva se considera "activa".
    ACTIVAS = (PENDIENTE, CONFIRMADA)

    def __init__(self, gestor_clientes, gestor_servicios):
        self._clientes = gestor_clientes
        self._servicios = gestor_servicios
        self._reservas = []

    def crear_reserva(self, cliente_id, servicio_ids, duracion):
        """Crea una o varias reservas para un cliente.

        servicio_ids puede ser un ID único (devuelve una Reserva) o una
        lista/tupla de IDs (devuelve una lista de Reservas). Operación atómica:
        si alguna falla, no se crea ninguna.
        """
        multiple = isinstance(servicio_ids, (list, tuple))
        ids = list(servicio_ids) if multiple else [servicio_ids]
        if not ids:
            raise ParametroFaltanteError("Falta el parámetro 'servicio_ids'")

        # 1) Cliente existente. Se encadena la excepción original (raise ... from).
        try:
            cliente = self._clientes.buscar(cliente_id)
        except DatoInvalidoError as e:
            raise ReservaInvalidaError(f"Cliente inválido para la reserva: {e}", e) from e

        # 2) Validar TODO antes de crear nada.
        servicios, vistos = [], set()
        for sid in ids:
            try:
                servicio = self._servicios.buscar(sid)
            except DatoInvalidoError as e:
                raise ReservaInvalidaError(f"Servicio inválido para la reserva: {e}", e) from e
            if servicio.id in vistos:
                raise ReservaInvalidaError(f"Servicio repetido en la solicitud (id={servicio.id})")
            vistos.add(servicio.id)

            if not servicio.disponible():
                raise ServicioNoDisponibleError(f"'{servicio.nombre}' no tiene disponibilidad")
            if self._hay_activa(cliente, servicio):
                raise ReservaInvalidaError(
                    f"{cliente.nombre} ya tiene una reserva activa de '{servicio.nombre}'")
            servicios.append(servicio)

        # 3) Construir las reservas (Reserva valida la duración con el servicio).
        nuevas = [Reserva(cliente, s, duracion) for s in servicios]

        # 4) Confirmar la creación: asignar IDs y guardar.
        for r in nuevas:
            r.asignar_id()
            self._reservas.append(r)
            log.info(f"Reserva creada: {r.describir()}")
        return nuevas if multiple else nuevas[0]

    def _hay_activa(self, cliente, servicio):
        """True si el cliente ya tiene una reserva PENDIENTE/CONFIRMADA del servicio."""
        return any(r.cliente == cliente and r.servicio == servicio and r.estado in self.ACTIVAS
                   for r in self._reservas)

    def buscar(self, id_reserva):
        """Busca una reserva por ID; lanza ReservaInvalidaError si no existe."""
        try:
            buscado = _a_id(id_reserva, "id de reserva")
        except (DatoInvalidoError, ParametroFaltanteError) as e:
            raise ReservaInvalidaError(f"ID de reserva inválido: {e}", e) from e
        for r in self._reservas:
            if r.id == buscado:
                return r
        raise ReservaInvalidaError(f"Reserva no encontrada (id={buscado})")

    def listar(self):
        return list(self._reservas)


class Sistema:
    """Clase principal: crea y expone los tres gestores."""

    def __init__(self):
        self.clientes = GestorClientes()
        self.servicios = GestorServicios()
        self.reservas = GestorReservas(self.clientes, self.servicios)
        log.info("Sistema Software FJ iniciado")



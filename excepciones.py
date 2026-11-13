 #1. IMPORTACIÓN DE HERRAMIENTAS

import logging
from datetime import datetime

# 2. EXPORTACIÓN DE ELEMENTOS DEL MÓDULO

__all__ = [
    "log",
    "ErrorSoftwareFJ",
    "DatoInvalidoError",
    "ParametroFaltanteError",
    "OperacionNoPermitidaError",
    "ReservaInvalidaError",
    "ServicioNoDisponibleError",
    "CalculoCostoError",
    "ErrorInesperadoError",
    "ejecutar_seguro"
]

# 3. CONFIGURACIÓN DEL REGISTRO DE EVENTOS

def configurar_registro():
    """
    Configura el registro de eventos del sistema.

    Los mensajes se almacenan en registro.log.
    Si el archivo no puede utilizarse, se habilita
    un registro alternativo en la consola.
    """

    # Recuperamos el logger del proyecto.
    registrador = logging.getLogger("SoftwareFJ")

    # Indica que queremos registrar desde INFO en adelante.
    registrador.setLevel(logging.INFO)

    # Evita que los mensajes se dupliquen en el logger raíz.
    registrador.propagate = False

    # Si no hay controladores asociados, creamos uno nuevo.
    if not registrador.handlers:

        try:
            # Intentamos crear el archivo de registro.
            controlador = logging.FileHandler(
                "registro.log",
                mode="a",
                encoding="utf-8"
            )

        except OSError:
            # Si no se puede escribir en el archivo, utilizamos la consola como alternativa.
            controlador = logging.StreamHandler()

        # Definimos cómo aparecerá cada evento registrado.
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        controlador.setFormatter(formato)

        # Asociamos el controlador con el logger.
        registrador.addHandler(controlador)

    return registrador

# Creamos el logger del sistema al cargar el módulo.
log = configurar_registro()

# 4. CLASE BASE DE LOS ERRORES DEL SISTEMA

class ErrorSoftwareFJ(Exception):
    """
    Representa un error general propio de Software FJ.

    Atributos:
        mensaje: explicación del problema.
        causa: excepción original, si existe.
        fecha: momento en que se produjo el error.
        codigo: identificador del tipo de error.
    """

    def __init__(self, mensaje, causa=None, codigo="FJ-000"):

        # Invocamos al constructor de la clase base Exception.
        super().__init__(mensaje)

        # Guardamos los datos que permiten describir el error.
        self.mensaje = mensaje
        self.causa = causa
        self.fecha = datetime.now()
        self.codigo = codigo

# 5. EXCEPCIONES ESPECÍFICAS DEL SISTEMA

class DatoInvalidoError(ErrorSoftwareFJ):
    """Indica que un dato no cumple las reglas de validación."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-001")

class ParametroFaltanteError(ErrorSoftwareFJ):
    """Indica que falta un parámetro obligatorio."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-002")

class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """Indica que una operación no puede realizarse."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-003")

class ReservaInvalidaError(ErrorSoftwareFJ):
    """Indica que una reserva no cumple las condiciones."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-004")

class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """Indica que no hay disponibilidad del servicio solicitado."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-005")

class CalculoCostoError(ErrorSoftwareFJ):
    """Indica que existe un problema al calcular un costo."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-006")

class ErrorInesperadoError(ErrorSoftwareFJ):
    """Representa un error no contemplado previamente."""

    def __init__(self, mensaje, causa=None):
        super().__init__(mensaje, causa, "FJ-999")

# 6. CONTROL CENTRALIZADO DE OPERACIONES
def ejecutar_seguro(funcion, *args, **kwargs):
    """
    Ejecuta una función y controla los errores que puedan surgir.

    Parámetros:
        funcion: operación que se desea ejecutar.
        *args: argumentos posicionales de la operación.
        **kwargs: argumentos identificados por nombre.

    Retorna:
        (True, resultado): si la operación termina correctamente.
        (False, error): si se produce una excepción.
    """

    # Registramos el nombre de la función que se ejecutará.
    nombre_operacion = getattr(
        funcion,
        "__name__",
        "operacion_sin_nombre"
    )

    log.info("Inicio de operación: %s", nombre_operacion)

    try:
        # Intentamos ejecutar la operación solicitada.
        resultado = funcion(*args, **kwargs)

    except ErrorSoftwareFJ as error:
        # Los errores propios del sistema se registran sin transformarlos, conservando su tipo y código.
        log.error(
            "%s | Código: %s | Detalle: %s",
            type(error).__name__,
            error.codigo,
            error
        )
        return False, error

    except Exception as causa_original:
        # Convertimos un error no previsto en una excepción general del sistema y conservamos su causa original.
        error_controlado = ErrorInesperadoError(
            "Se produjo un error no previsto durante la operación.",
            causa_original
        )

        # Establecemos explícitamente la relación entre la excepción nueva y la excepción que la originó.
        error_controlado.__cause__ = causa_original

        # Registramos el problema y su causa técnica.
        log.exception(
            "%s | Código: %s | Causa original: %r",
            type(error_controlado).__name__,
            error_controlado.codigo,
            causa_original
        )
        return False, error_controlado

    else:
        # Si la operación se completa sin errores, registramos el éxito.
        log.info("Operación completada correctamente: %s",
                 nombre_operacion)
        return True, resultado

    finally:
        # Este bloque se ejecuta al finalizar el intento, tanto si hubo éxito como si se produjo un error.
        log.info("Fin de operación: %s", nombre_operacion)

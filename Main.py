"""Software FJ - Sistema de Clientes, Servicios y Reservas (Tkinter).
Uso:  python main.py              -> interfaz gráfica
      python main.py --simulacion -> simulación en consola"""
import sys
from collections import Counter
from excepciones import *
from modelos import *
from gestores import Sistema


def simular(salida=print):
    s = Sistema()
    ctx, res, errores = {}, [0, 0], Counter()

    def op5():
        ctx["sala"] = s.servicios.agregar(ReservaSala("Sala Norte", 50, 10)); return ctx["sala"].describir()

    def op8():
        ctx["r"] = s.reservas.crear_reserva(1, ctx["sala"].id, 3); return ctx["r"].describir()

    def op9():
        ctx["r"].confirmar(); return f"costo final ${ctx['r'].procesar(10, 19)}"

    def op11():
        e = s.servicios.agregar(AlquilerEquipo("Laptop", 30, "Cómputo", 0))
        return s.reservas.crear_reserva(1, e.id, 2)

    def op12():
        r = s.reservas.crear_reserva(1, ctx["sala"].id, 2); r.cancelar(); r.cancelar()

    def procesar_none(r): return r.procesar()

    ops = [
        ("Registrar cliente válido", lambda: s.clientes.agregar("Ana Gómez", "ana@mail.com", "3001234567", "10203040").describir()),
        ("Cliente con email mal formado", lambda: s.clientes.agregar("Luis Pérez", "luis@@mail", "3001112233", "20304050")),
        ("Cliente sin nombre", lambda: s.clientes.agregar(None, "x@mail.com", "3001112233", "30405060")),
        ("Cliente con documento duplicado", lambda: s.clientes.agregar("Ana Copia", "copia@mail.com", "3009998877", "10203040")),
        ("Crear sala válida", op5),
        ("Equipo con unidades negativas", lambda: s.servicios.agregar(AlquilerEquipo("Proyector", 20, "Video", -2))),
        ("Asesoría con nivel inexistente", lambda: s.servicios.agregar(Asesoria("Consultoría", 80, "Redes", "maestro"))),
        ("Reserva válida de Ana (3 h)", op8),
        ("Confirmar y procesar con 10% desc. e IVA 19%", op9),
        ("Reservar con cliente inexistente", lambda: s.reservas.crear_reserva(99, ctx["sala"].id, 2)),
        ("Reservar equipo sin unidades", op11),
        ("Cancelar una reserva ya cancelada", op12),
        ("Descuento del 150% (cálculo inconsistente)", lambda: ctx["sala"].calcular_costo(2, descuento=150)),
        ("Error no previsto (None en lugar de reserva)", lambda: procesar_none(None)),
    ]
    for i, (desc, f) in enumerate(ops, 1):
        ok, r = ejecutar_seguro(f)
        if ok:
            res[0] += 1; salida(f"[{i:02}] OK    {desc} -> {r if r is not None else 'hecho'}")
        else:
            res[1] += 1; errores[type(r).__name__] += 1
            salida(f"[{i:02}] ERROR {desc} -> {type(r).__name__}: {r}")
    salida("\n=== RESUMEN ===")
    salida(f"Operaciones: {len(ops)} | Exitosas: {res[0]} | Fallidas controladas: {res[1]}")
    for k, v in errores.items():
        salida(f"  {k}: {v}")
    salida("\n=== ESTADO FINAL (solo en memoria) ===")
    for lista in (s.clientes.listar(), s.servicios.listar(), s.reservas.listar()):
        for x in lista:
            salida("  " + x.describir())
    salida("El sistema siguió activo hasta el final. Detalle en registro.log")

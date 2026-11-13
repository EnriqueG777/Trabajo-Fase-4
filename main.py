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


def gui():
    import tkinter as tk
    from tkinter import ttk, messagebox

    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Software FJ - Gestión integral"); self.geometry("960x620")
            self.s = Sistema()
            self.estado = tk.StringVar(value="Listo")
            nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
            self.t_cli, self.t_srv, self.t_res = (ttk.Frame(nb, padding=8) for _ in range(3))
            self.t_sim, self.t_log = ttk.Frame(nb, padding=8), ttk.Frame(nb, padding=8)
            for t, n in ((self.t_cli, "Clientes"), (self.t_srv, "Servicios"), (self.t_res, "Reservas"),
                         (self.t_sim, "Simulación"), (self.t_log, "Registro")):
                nb.add(t, text=n)
            ttk.Label(self, textvariable=self.estado, relief="sunken", anchor="w").pack(fill="x")
            self._clientes(); self._servicios(); self._reservas(); self._simulacion(); self._registro()

        # utilidades
        def campos(self, parent, etiquetas):
            es = []
            for i, e in enumerate(etiquetas):
                ttk.Label(parent, text=e).grid(row=0, column=i, padx=3, sticky="w")
                en = ttk.Entry(parent, width=16); en.grid(row=1, column=i, padx=3); es.append(en)
            return es

        def tabla(self, parent, cols):
            t = ttk.Treeview(parent, columns=cols, show="headings", height=12)
            for c in cols: t.heading(c, text=c); t.column(c, width=110)
            t.pack(fill="both", expand=True, pady=8); return t

        def llenar(self, tabla, filas):
            tabla.delete(*tabla.get_children())
            for f in filas: tabla.insert("", "end", values=f)

        def run(self, f, msg):
            ok, r = ejecutar_seguro(f)
            if ok: self.estado.set(msg)
            else:
                self.estado.set(f"Error controlado: {type(r).__name__}")
                messagebox.showwarning(type(r).__name__, str(r))
            self.refrescar()

        def refrescar(self):
            self.llenar(self.tc, [(c.id, c.nombre, c.email, c.telefono, c.documento) for c in self.s.clientes.listar()])
            self.llenar(self.ts, [(x.id, type(x).__name__, x.nombre, x.tarifa, x.unidades) for x in self.s.servicios.listar()])
            self.llenar(self.tr, [(r.id, r.cliente.nombre, r.servicio.nombre, f"{r.duracion:g}", r.estado,
                                   r.costo_final if r.costo_final is not None else "") for r in self.s.reservas.listar()])

        # pestañas
        def _clientes(self):
            f = ttk.Frame(self.t_cli); f.pack(fill="x")
            self.ec = self.campos(f, ["Nombre", "Email", "Teléfono", "Documento"])
            ttk.Button(f, text="Registrar", command=lambda: self.run(
                lambda: self.s.clientes.agregar(*[e.get() for e in self.ec]), "Cliente registrado")).grid(row=1, column=4, padx=6)
            self.tc = self.tabla(self.t_cli, ("ID", "Nombre", "Email", "Teléfono", "Documento"))

        def _servicios(self):
            f = ttk.Frame(self.t_srv); f.pack(fill="x")
            ttk.Label(f, text="Tipo").grid(row=0, column=0, sticky="w")
            self.tipo = ttk.Combobox(f, values=["Sala", "Equipo", "Asesoría"], state="readonly", width=12)
            self.tipo.set("Sala"); self.tipo.grid(row=1, column=0, padx=3)
            self.es = []
            self.lbs = []
            for i in range(4):
                l = ttk.Label(f, text=""); l.grid(row=0, column=i + 1, sticky="w", padx=3); self.lbs.append(l)
                e = ttk.Entry(f, width=16); e.grid(row=1, column=i + 1, padx=3); self.es.append(e)
            self.tipo.bind("<<ComboboxSelected>>", lambda _: self._etiquetas())
            ttk.Button(f, text="Crear servicio", command=self._crear_srv).grid(row=1, column=5, padx=6)
            self._etiquetas()
            self.ts = self.tabla(self.t_srv, ("ID", "Tipo", "Nombre", "Tarifa", "Unidades"))

        def _etiquetas(self):
            et = {"Sala": ["Nombre", "Tarifa/hora", "Capacidad", "Unidades"],
                  "Equipo": ["Nombre", "Tarifa/día", "Tipo equipo", "Unidades"],
                  "Asesoría": ["Nombre", "Tarifa/hora", "Especialidad", "Nivel"]}[self.tipo.get()]
            for l, t in zip(self.lbs, et): l.config(text=t)

        def _crear_srv(self):
            v = [e.get() for e in self.es]
            def crear():
                t = self.tipo.get()
                if t == "Sala": return self.s.servicios.agregar(ReservaSala(v[0], v[1], v[2], v[3] or 1))
                if t == "Equipo": return self.s.servicios.agregar(AlquilerEquipo(v[0], v[1], v[2], v[3]))
                return self.s.servicios.agregar(Asesoria(v[0], v[1], v[2], v[3]))
            self.run(crear, "Servicio creado")

        def _reservas(self):
            f = ttk.Frame(self.t_res); f.pack(fill="x")
            self.er = self.campos(f, ["ID cliente", "ID servicio", "Duración"])
            ttk.Button(f, text="Crear reserva", command=lambda: self.run(
                lambda: self.s.reservas.crear_reserva(self.er[0].get(), self.er[1].get(), self.er[2].get()),
                "Reserva creada")).grid(row=1, column=3, padx=6)
            g = ttk.Frame(self.t_res); g.pack(fill="x", pady=6)
            self.ea = self.campos(g, ["ID reserva", "Descuento %", "IVA %"])
            self.ea[1].insert(0, "0"); self.ea[2].insert(0, "0")
            def accion(n):
                def f():
                    r = self.s.reservas.buscar(self.ea[0].get())
                    if n == "confirmar": return r.confirmar()
                    if n == "cancelar": return r.cancelar()
                    return r.procesar(self.ea[1].get(), self.ea[2].get())
                self.run(f, f"Reserva: {n} correcto")
            for i, n in enumerate(("confirmar", "cancelar", "procesar")):
                ttk.Button(g, text=n.capitalize(), command=lambda n=n: accion(n)).grid(row=1, column=3 + i, padx=4)
            self.tr = self.tabla(self.t_res, ("ID", "Cliente", "Servicio", "Duración", "Estado", "Costo"))

        def _simulacion(self):
            ttk.Button(self.t_sim, text="Ejecutar simulación (14 operaciones)", command=self._sim).pack(anchor="w")
            self.txt = tk.Text(self.t_sim, font=("Consolas", 10)); self.txt.pack(fill="both", expand=True, pady=6)

        def _sim(self):
            self.txt.delete("1.0", "end")
            ejecutar_seguro(simular, lambda m: self.txt.insert("end", m + "\n"))
            self.estado.set("Simulación terminada (usa un sistema independiente)")

        def _registro(self):
            ttk.Button(self.t_log, text="Actualizar", command=self._leer_log).pack(anchor="w")
            self.tl = tk.Text(self.t_log, font=("Consolas", 9)); self.tl.pack(fill="both", expand=True, pady=6)

        def _leer_log(self):
            self.tl.delete("1.0", "end")
            try:
                with open("registro.log", encoding="utf-8") as f: self.tl.insert("end", f.read())
            except OSError as e:
                self.tl.insert("end", f"No se pudo leer el registro: {e}")

    App().mainloop()


if __name__ == "__main__":
    simular() if "--simulacion" in sys.argv else gui()

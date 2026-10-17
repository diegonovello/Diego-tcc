"""Painel experimental Uno: ESPACO mantido, M1 -> M2 -> M3.
Elaborado com auxilio de IA (Codex/OpenAI). Nao e parada de emergencia.
Instalar: python -m pip install pyserial
Executar: python painel_espaco.py (fechar Monitor Serial antes).
"""
import time
import ctypes
import sys
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    raise SystemExit("Instale a dependencia: python -m pip install pyserial")

RUN, PAUSE = b"\x11", b"\x13"


def physical_space():
    """Windows: confirmar estado fisico, alem dos eventos de soltar do Tk."""
    if sys.platform == "win32":
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000)
    return None


class Painel:
    def __init__(self, root):
        self.root, self.port = root, None
        self.held = False
        self.require_release = False
        self.next_heartbeat = 0.0
        self.ready_at = 0.0
        root.title("Snake — movimento lento com ESPACO mantido")
        root.protocol("WM_DELETE_WINDOW", self.close)
        row = ttk.Frame(root, padding=8)
        row.pack(fill="x")
        self.device = ttk.Combobox(row, values=[p.device for p in list_ports.comports()], width=15)
        self.device.pack(side="left")
        if self.device["values"]:
            self.device.current(0)
        ttk.Button(row, text="Conectar", command=self.connect).pack(side="left")
        ttk.Button(row, text="Desconectar", command=self.disconnect).pack(side="left")
        ttk.Label(root, text="Conectar reinicia o Uno. Nao referencia nem arma automaticamente.").pack()
        self.command = ttk.Entry(root, width=65)
        self.command.pack(padx=8, pady=6)
        self.command.insert(0, "config")
        self.command.bind("<Return>", lambda _: self.send_command())
        ttk.Button(root, text="Enviar comando / previa", command=self.send_command).pack()
        ttk.Label(root, text="Configurar → referenciar RETO → armar → X;Y (cm) ou caso N → mover").pack()
        self.area = tk.Canvas(root, width=650, height=105, background="#dddddd", takefocus=True)
        self.area.pack(padx=8, pady=8)
        self.label = self.area.create_text(325, 52, text="Clique AQUI; depois mantenha ESPACO para movimentar.\nSoltar ou sair desta area pausa os pulsos.", justify="center")
        self.area.bind("<Button-1>", lambda _: self.area.focus_set())
        self.area.bind("<KeyPress-space>", self.press)
        self.area.bind("<KeyRelease-space>", self.release)
        self.area.bind("<FocusOut>", self.release)
        self.area.bind("<Leave>", self.leave)
        root.bind_all("<Escape>", self.abort)
        ttk.Button(root, text="ABORTAR (!) — invalida referencia", command=self.abort).pack()
        self.log = tk.Text(root, width=92, height=20, state="disabled")
        self.log.pack(padx=8, pady=8)
        self.pending_text = ""
        self.root.after(10, self.tick)

    def append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        # Limitar historico para a interface nao crescer indefinidamente.
        if int(self.log.index("end-1c").split(".")[0]) > 600:
            self.log.delete("1.0", "101.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def write(self, data):
        if self.port is None:
            return False
        try:
            # Nao acumular permissoes se a USB/driver estiver bloqueada.
            if self.port.out_waiting:
                if data == PAUSE or data == b"!":
                    self.port.reset_output_buffer()
                else:
                    raise serial.SerialException("Fila serial ocupada; reconectar e conferir estado")
            if self.port.write(data) != len(data):
                raise serial.SerialException("Escrita incompleta")
            return True
        except (serial.SerialException, OSError) as error:
            self.append(f"\nFalha serial: {error}. Heartbeat interrompido.\n")
            self.disconnect()
            return False

    def connect(self):
        self.disconnect()
        try:
            self.port = serial.Serial(self.device.get().strip(), 115200, timeout=0,
                                      write_timeout=0, xonxoff=False, rtscts=False)
            self.ready_at = time.monotonic() + 2.5
            self.append("\nConectado. Aguarde reinicio do Uno (2,5 s).\n")
        except (serial.SerialException, OSError, ValueError) as error:
            messagebox.showerror("Serial", str(error))

    def disconnect(self):
        self.held = False
        port, self.port = self.port, None
        if port is not None:
            try:
                port.reset_output_buffer()
                port.write(PAUSE)
            except (serial.SerialException, OSError):
                pass  # Ausencia de heartbeat tambem expira a permissao no Uno.
            finally:
                port.close()
        if hasattr(self, "area"):
            self.area.configure(background="#dddddd")

    def release(self, event=None):
        was_held, self.held = self.held, False
        if physical_space():
            self.require_release = True
        if was_held:
            self.write(PAUSE)
        self.area.configure(background="#dddddd")
        return "break"

    def leave(self, event=None):
        self.release()
        self.root.focus_set()  # exige clicar novamente na area antes de permitir
        return "break"

    def press(self, event=None):
        if self.held:  # Repeticao automatica da tecla nao cria novas sessoes.
            return "break"
        if self.require_release:
            return "break"
        if self.port is None or time.monotonic() < self.ready_at:
            return "break"
        if self.root.focus_get() is not self.area:
            return "break"
        self.held = self.write(RUN)
        self.next_heartbeat = time.monotonic() + 0.05
        if self.held:
            self.area.configure(background="#ffe49a")
        return "break"

    def send_command(self):
        self.release()
        if self.port is None or time.monotonic() < self.ready_at:
            self.append("\nConecte e aguarde o reinicio antes de enviar.\n")
            return
        command = self.command.get().strip()
        if not command or len(command) > 62 or not command.isascii():
            self.append("\nComando vazio, longo ou nao ASCII.\n")
            return
        # O envio de mover exige soltar e pressionar ESPACO novamente.
        self.write((command + "\n").encode("ascii"))
        self.append(f"\n> {command}\n")

    def abort(self, event=None):
        self.release()
        self.write(b"!")
        return "break"

    def tick(self):
        try:
            physical = physical_space()
            if physical is False:
                self.require_release = False
                if self.held:
                    self.release()
            if self.port is not None:
                # Ler apenas um bloco por passagem; nunca bloquear eventos da tecla.
                data = self.port.read(min(self.port.in_waiting, 2048))
                if data:
                    self.append(data.decode("utf-8", errors="replace"))
                if self.held and self.root.focus_get() is not self.area:
                    self.release()
                now = time.monotonic()
                if self.held and now >= self.next_heartbeat:
                    self.write(RUN)
                    self.next_heartbeat = now + 0.05  # sem rajadas para recuperar atraso
        except (serial.SerialException, OSError) as error:
            self.append(f"\nConexao perdida: {error}\n")
            self.disconnect()
        finally:
            self.root.after(10, self.tick)

    def close(self):
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    app = tk.Tk()
    Painel(app)
    app.mainloop()

import os
import sys
import keyboard
import tkinter as tk
from PIL import Image, ImageTk
import queue
import threading
import win32clipboard
from io import BytesIO
import time
from tkinter import ttk
import json
import unicodedata
import winshell
from tkinter import messagebox
from win32com.client import Dispatch
from pathlib import Path
import requests
import zipfile
import io
import pystray
from PIL import Image as PILImage


DOWNLOADS_DIR = Path.home() / "Downloads"
APP_DIR = DOWNLOADS_DIR / "HKEmotes"
EMOTES_FOLDER = APP_DIR / "Emotes"
CONFIG_FILE = APP_DIR / "config.json"
FAVORITES_FILE = APP_DIR / "favorites.json"
hotkey_personal_handle = None
ICON_PATH = APP_DIR / "senk.ico"
VERSION = "v0.1 Beta(offlineVersion)"
FOOTER_DER = "by HikashiVT"
BG_COLOR = "#0f1115"
CARD_COLOR = "#1a1d24"
TEXT_COLOR = "#cdd6f4"
ACCENT = "#5865F2"  
config = {
    "start_with_windows": False,
    "hotkey": "ctrl+.",
    "version": VERSION
}

favoritos = set()
cola = queue.Queue()
ventana = None
imagenes_guardadas = [] 
refrescar_emotes = None   


STARTER_URL = "https://github.com/HikashiVT/HKEmotes-StarterPack/releases/latest/download/emotes.zip"

def resource_path(relative):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)
tray_icon = None

def abrir_panel_desde_tray(icon=None, item=None):
    cola.put("abrir")

def salir_app(icon=None, item=None):
    global tray_icon

    if tray_icon:
        tray_icon.stop()

    root.after(0, root.destroy)

def iniciar_bandeja():
    global tray_icon

    try:
        icon_img = PILImage.open(str(ICON_PATH))
    except:
        icon_img = PILImage.new("RGB", (64, 64), "black")

    menu = pystray.Menu(
        pystray.MenuItem("Abrir HKEmotes", abrir_panel_desde_tray),
        pystray.MenuItem("Salir", salir_app)
    )

    tray_icon = pystray.Icon(
        "HKEmotes",
        icon_img,
        "HKEmotes",
        menu
    )

    tray_icon.run()
def descargar_emotes_si_vacio():
    if any(EMOTES_FOLDER.iterdir()):
        return  # ya tiene emotes

    try:
        print("Descargando starter pack...")
        r = requests.get(STARTER_URL, timeout=10)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(EMOTES_FOLDER)
        print("Starter pack instalado")
    except:
        print("No se pudo descargar starter pack")
def crear_estructura_usuario():
    APP_DIR.mkdir(exist_ok=True)
    EMOTES_FOLDER.mkdir(exist_ok=True)

    # crear json vacíos si no existen
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    if not FAVORITES_FILE.exists():
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    # copiar icono al APP_DIR si no existe
    if not ICON_PATH.exists():
        try:
            origen_icono = resource_path("senk.ico")
            import shutil
            shutil.copy(origen_icono, ICON_PATH)
        except:
            pass
def cargar_config():
    global config

    if not CONFIG_FILE.exists() or CONFIG_FILE.stat().st_size == 0:
        guardar_config()
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            config.update(data)
        else:
            guardar_config()

    except json.JSONDecodeError:
        guardar_config()
def guardar_favoritos():
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(favoritos), f, indent=4)

def cargar_favoritos():
    global favoritos

    if not FAVORITES_FILE.exists() or FAVORITES_FILE.stat().st_size == 0:
        guardar_favoritos()
        return

    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            favoritos = set(data)
        else:
            favoritos = set()
            guardar_favoritos()

    except json.JSONDecodeError:
        favoritos = set()
        guardar_favoritos()
def guardar_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    return texto
def configurar_inicio_windows():
    startup = winshell.startup()
    ruta_acceso = os.path.join(startup, "HKEmotes.lnk")

    if config["start_with_windows"]:
        target = os.path.abspath(sys.argv[0])
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(ruta_acceso)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = str(ICON_PATH)
        shortcut.save()
    else:
        if os.path.exists(ruta_acceso):
            os.remove(ruta_acceso)
import ctypes
from ctypes import wintypes

def copiar_imagen(ruta):
    ext = os.path.splitext(ruta)[1].lower()


    if ext == ".gif":

        CF_HDROP = 15
        GMEM_MOVEABLE = 0x0002

        # 🔥 declarar correctamente WinAPI (FIX CRASH)
        kernel32 = ctypes.windll.kernel32
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID

        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL

        class DROPFILES(ctypes.Structure):
            _fields_ = [
                ("pFiles", wintypes.DWORD),
                ("pt_x", wintypes.LONG),
                ("pt_y", wintypes.LONG),
                ("fNC", wintypes.BOOL),
                ("fWide", wintypes.BOOL),
            ]

        ruta = os.path.abspath(ruta)
        data_files = (ruta + "\0\0").encode("utf-16le")

        dropfiles = DROPFILES()
        dropfiles.pFiles = ctypes.sizeof(DROPFILES)
        dropfiles.pt_x = 0
        dropfiles.pt_y = 0
        dropfiles.fNC = False
        dropfiles.fWide = True

        size = ctypes.sizeof(DROPFILES) + len(data_files)

        h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
        if not h_global:
            print("❌ GlobalAlloc falló")
            return

        p_global = kernel32.GlobalLock(h_global)
        if not p_global:
            print("❌ GlobalLock falló")
            return

        ctypes.memmove(p_global, ctypes.byref(dropfiles), ctypes.sizeof(dropfiles))
        ctypes.memmove(
            p_global + ctypes.sizeof(dropfiles),
            data_files,
            len(data_files)
        )

        kernel32.GlobalUnlock(h_global)

        for _ in range(10):
            try:
                win32clipboard.OpenClipboard()
                break
            except:
                time.sleep(0.01)
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(CF_HDROP, h_global)
        win32clipboard.CloseClipboard()

        cerrar()
        time.sleep(0.05)
        keyboard.press_and_release("ctrl+v")
        return
    # 🟢 IMAGEN NORMAL (PNG/JPG)
    img = Image.open(ruta)
    output = BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    for _ in range(10):
        try:
            win32clipboard.OpenClipboard()
            break
        except:
            time.sleep(0.01)
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    h_global = None
    win32clipboard.CloseClipboard()

    cerrar()
    time.sleep(0.05)
    keyboard.press_and_release("ctrl+v")
def cerrar():
    global ventana
    if ventana:
        ventana.destroy()
        ventana = None
def toggle_favorito(nombre_archivo):
    global refrescar_emotes

    if nombre_archivo in favoritos:
        favoritos.remove(nombre_archivo)
    else:
        favoritos.add(nombre_archivo)

    guardar_favoritos()
    if refrescar_emotes:
        refrescar_emotes()
def abrir_ajustes():
    win = tk.Toplevel()
    win.title("Ajustes")
    win.geometry("260x200")
    win.configure(bg=BG_COLOR)
    win.attributes("-topmost", True)
    win.iconbitmap(str(ICON_PATH))

    # ===== SWITCH iniciar con windows =====
    start_var = tk.BooleanVar(value=config["start_with_windows"])

    def toggle_startup():
        config["start_with_windows"] = start_var.get()
        guardar_config()
        configurar_inicio_windows()

    tk.Checkbutton(
        win,
        text="Iniciar con Windows",
        variable=start_var,
        command=toggle_startup,
        bg=BG_COLOR,
        fg=TEXT_COLOR,
        selectcolor=CARD_COLOR
    ).pack(anchor="w", padx=15, pady=10)

    # ===== HOTKEY CUSTOM =====
    tk.Label(win, text="Hotkey:", bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w", padx=15)

    hotkey_entry = tk.Entry(win)
    hotkey_entry.insert(0, config["hotkey"])
    hotkey_entry.pack(padx=15, fill="x")

    def guardar_hotkey():
        nueva = hotkey_entry.get().strip().lower()

        #  si está vacío → no guardar
        if nueva == "":
            messagebox.showwarning("Hotkey inválida", "No puedes dejar la hotkey vacía")
            return

        # 🚨 si intenta borrar la de emergencia
        if nueva == "ctrl+.":
            messagebox.showinfo("Hotkey protegida", "CTRL + . siempre existe como hotkey de emergencia 😊")

        config["hotkey"] = nueva
        guardar_config()

        registrar_hotkeys()

        messagebox.showinfo("Guardado", "Hotkey actualizada correctamente")

    tk.Button(win, text="Guardar Hotkey", command=guardar_hotkey).pack(pady=8)

    # ===== UPDATE =====
    def check_update():
        messagebox.showinfo("Update", "No hay actualizaciones aún")

    tk.Button(win, text="Check update", command=check_update).pack(pady=10)
def crear_panel():
    global ventana, imagenes_guardadas
    if ventana and ventana.winfo_exists():
        return
    ventana = tk.Toplevel()
    ventana.title("HKEmotes")
    ventana.geometry("380x480")
    ventana.configure(bg=BG_COLOR)
    ventana.attributes("-topmost", True)
    ventana.iconbitmap(str(ICON_PATH))

    x = ventana.winfo_screenwidth()//2 - 220
    y = ventana.winfo_screenheight()//2 - 280
    ventana.geometry(f"+{x}+{y}")

    # 🔎 BUSCADOR
    buscador = tk.Entry(
        ventana,
        font=("Segoe UI", 13),
        bg=CARD_COLOR,
        fg=TEXT_COLOR,
        insertbackground=TEXT_COLOR,
        relief="flat"
    )
    buscador.pack(fill="x", padx=12, pady=10, ipady=6)

    style = ttk.Style()
    style.theme_use("default")

    style.configure("Dark.Vertical.TScrollbar",
        background="#1a1d24",
        troughcolor=BG_COLOR,
        bordercolor=BG_COLOR,
        arrowcolor="#5865F2",
        gripcount=0,
        relief="flat"
    )

    style.map("Dark.Vertical.TScrollbar",
        background=[("active", "#2b2f3a")]
    )
    btn_settings = tk.Button(
    ventana,
    text="⚙",
    font=("Segoe UI", 12),
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    relief="flat",
    command=abrir_ajustes
    )
    btn_settings.place(x=340, y=10)
#scroll
    frame_scroll = tk.Frame(ventana, bg=BG_COLOR)
    frame_scroll.pack(fill="both", expand=True, padx=10, pady=(0,8))

    canvas = tk.Canvas(frame_scroll, bg=BG_COLOR, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(
        frame_scroll,
        orient="vertical",
        command=canvas.yview,
        style="Dark.Vertical.TScrollbar"
    )
    scrollbar.pack(side="right", fill="y")


    canvas.configure(yscrollcommand=scrollbar.set)

    # frame interno con ancho fijo real
    contenedor = tk.Frame(canvas, bg=BG_COLOR)
    window_id = canvas.create_window((0, 0), window=contenedor, anchor="nw")


    def resize_canvas(event):
        canvas.itemconfig(window_id, width=event.width)

    canvas.bind("<Configure>", resize_canvas)

    # actualizar scrollregion
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    contenedor.bind("<Configure>", on_frame_configure)


    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    #  CARGAR EMOTES
    def cargar_emotes(filtro=""):
        global imagenes_guardadas
        imagenes_guardadas = []

        for widget in contenedor.winfo_children():
            widget.destroy()

        col = row = 0

        archivos = os.listdir(EMOTES_FOLDER)
        archivos.sort(key=lambda x: x not in favoritos)

        # ⭐  favoritos primero
        archivos.sort(key=lambda x: x not in favoritos)

        for archivo in archivos:
            if not archivo.lower().endswith((".png", ".gif", ".jpg")):
                continue
            if normalizar(filtro) not in normalizar(archivo):
                continue

            ruta = EMOTES_FOLDER / archivo
            

            try:
                img = Image.open(ruta)
                img.thumbnail((60, 60))
                tk_img = ImageTk.PhotoImage(img)
                imagenes_guardadas.append(tk_img)

                nombre_archivo = archivo  # 🔥 faltaba esto

                frame_btn = tk.Frame(contenedor, bg=CARD_COLOR)
                frame_btn.grid(row=row, column=col, padx=6, pady=6)

                btn = tk.Button(
                    frame_btn,
                    image=tk_img,
                    bg=CARD_COLOR,
                    activebackground=ACCENT,
                    relief="flat",
                    command=lambda r=ruta: copiar_imagen(r)
                )
                btn.pack(padx=4, pady=4)

                # ⭐ dibujar estrella si es favorito
                if nombre_archivo in favoritos:
                    estrella = tk.Label(
                        frame_btn,
                        text="★",
                        fg="#FFD166",
                        bg=CARD_COLOR,
                        font=("Segoe UI", 10, "bold")
                    )
                    estrella.place(x=2, y=2)

                # 🖱️ click derecho → toggle favorito
                btn.bind("<Button-3>", lambda e, n=nombre_archivo: toggle_favorito(n))

                col += 1
                if col > 3:
                    col = 0
                    row += 1

            except Exception as e:
                print("Error:", archivo, e)
    global refrescar_emotes
    refrescar_emotes = cargar_emotes

    buscador.bind("<KeyRelease>", lambda e: cargar_emotes(buscador.get()))
    cargar_emotes()

    # 🧾 FOOTER
    footer = tk.Frame(ventana, bg=CARD_COLOR, height=26)
    footer.pack(fill="x", side="bottom")

    tk.Label(footer, text=VERSION, bg=CARD_COLOR, fg="#8b949e",
             font=("Segoe UI", 9)).pack(side="left", padx=8)

    tk.Label(footer, text=FOOTER_DER, bg=CARD_COLOR, fg="#8b949e",
             font=("Segoe UI", 9)).pack(side="right", padx=8)

    ventana.bind("<Escape>", lambda e: cerrar())
crear_estructura_usuario()
descargar_emotes_si_vacio()
cargar_config()
cargar_favoritos()

# HOTKEY THREAD
def registrar_hotkeys():
    global hotkey_personal_handle

    # 🔒 HOTKEY DE EMERGENCIA (solo se registra una vez)
    try:
        keyboard.add_hotkey("ctrl+.", lambda: cola.put("abrir"))
    except:
        pass

    # ❌ eliminar hotkey personalizada anterior SIN usar clear_all_hotkeys()
    if hotkey_personal_handle:
        try:
            keyboard.remove_hotkey(hotkey_personal_handle)
        except:
            pass
        hotkey_personal_handle = None

    # ⚙️ registrar nueva hotkey personalizada
    hotkey_user = config.get("hotkey", "").strip().lower()

    if hotkey_user and hotkey_user != "ctrl+.":
        try:
            hotkey_personal_handle = keyboard.add_hotkey(
                hotkey_user,
                lambda: cola.put("abrir")
            )
            print("Hotkey personalizada activa:", hotkey_user)

        except Exception as e:
            print("Hotkey inválida, usando solo CTRL + .", e)
# LOOP TKINTER
def revisar_cola():
    try:
        if cola.get_nowait() == "abrir":
            crear_panel()
    except:
        pass
    root.after(100, revisar_cola)

root = tk.Tk()
root.withdraw()
cargar_favoritos()

threading.Thread(target=keyboard.wait, daemon=True).start()
threading.Thread(target=iniciar_bandeja, daemon=True).start()

registrar_hotkeys()
revisar_cola()

print("Emote panel activo! Usa CTRL + .")
root.mainloop()
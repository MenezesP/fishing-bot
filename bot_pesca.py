import pyautogui
import pydirectinput
import keyboard
import time
import sys
import threading
import tkinter as tk
import ctypes

# ==========================================
# CONFIGURAÇÕES DO BOT
# ==========================================
TEMPO_PESCA_MINUTOS = 6
NOME_JANELA_JOGO = 'PokeMemories'

# Novas Teclas
TECLA_MARCAR = 'f9'
TECLA_INICIAR = 'f10'
TECLA_PARAR = 'f11'

pydirectinput.PAUSE = 0.1

PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_short)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

def mover_rato_fisico(x, y):
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77

    largura_ecra = ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    altura_ecra = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    esquerda = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    topo = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    
    x_calc = int(((x - esquerda) * 65535) / largura_ecra)
    y_calc = int(((y - topo) * 65535) / altura_ecra)

    extra = ctypes.pointer(ctypes.c_ulong(0))
    ii_ = Input_I()
    ii_.mi = MouseInput(x_calc, y_calc, 0, 0x0001 | 0x8000 | 0x4000, 0, extra) 
    comando = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(comando), ctypes.sizeof(comando))

def clicar_rato_fisico():
    extra = ctypes.pointer(ctypes.c_ulong(0))
    ii_down = Input_I()
    ii_down.mi = MouseInput(0, 0, 0, 0x0002, 0, extra)
    cmd_down = Input(ctypes.c_ulong(0), ii_down)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd_down), ctypes.sizeof(cmd_down))
    
    time.sleep(0.05)
    
    ii_up = Input_I()
    ii_up.mi = MouseInput(0, 0, 0, 0x0004, 0, extra)
    cmd_up = Input(ctypes.c_ulong(0), ii_up)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd_up), ctypes.sizeof(cmd_up))

def eh_administrador():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class BotPescaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot Pesca v5 (Sem Imagens)")
        self.root.geometry("280x220")
        self.root.attributes('-topmost', True) 
        self.root.configure(bg='#2c3e50')
        self.root.resizable(False, False)

        self.is_running = False
        self.primeira_pesca = True 
        self.janela_alvo = None
        
        self.pos_agua_x = None
        self.pos_agua_y = None

        # --- UI Elementos ---
        self.lbl_titulo = tk.Label(root, text="🐟 Poke Memories Bot", font=("Arial", 12, "bold"), bg='#2c3e50', fg='white')
        self.lbl_titulo.pack(pady=5)
        
        if not eh_administrador():
            self.lbl_admin = tk.Label(root, text="⚠️ ABRE COMO ADMINISTRADOR!", font=("Arial", 9, "bold"), bg='#c0392b', fg='white')
            self.lbl_admin.pack(fill=tk.X)

        self.lbl_agua = tk.Label(root, text=f"💧 Água: Marcar local da água ({TECLA_MARCAR.upper()})", font=("Arial", 9, "bold"), bg='#2c3e50', fg='#f1c40f')
        self.lbl_agua.pack(pady=2)

        self.lbl_status = tk.Label(root, text="Status: PARADO", font=("Arial", 10, "bold"), bg='#2c3e50', fg='#e74c3c')
        self.lbl_status.pack()

        self.lbl_alvo = tk.Label(root, text="Alvo: Nenhum jogo focado", font=("Arial", 8), bg='#2c3e50', fg='#bdc3c7')
        self.lbl_alvo.pack()

        self.lbl_log = tk.Label(root, text="Aguardando marcação...", font=("Arial", 9), bg='#2c3e50', fg='#bdc3c7')
        self.lbl_log.pack(pady=5)

        # Botões
        frame_botoes = tk.Frame(root, bg='#2c3e50')
        self.btn_iniciar = tk.Button(frame_botoes, text=f"Iniciar ({TECLA_INICIAR.upper()})", command=self.iniciar_bot, bg='#27ae60', fg='white', width=12)
        self.btn_iniciar.grid(row=0, column=0, padx=5)
        
        self.btn_parar = tk.Button(frame_botoes, text=f"Parar ({TECLA_PARAR.upper()})", command=self.parar_bot, bg='#c0392b', fg='white', width=12)
        self.btn_parar.grid(row=0, column=1, padx=5)
        frame_botoes.pack()

        # Teclas Globais
        keyboard.on_press_key(TECLA_MARCAR, lambda _: self.marcar_agua())
        keyboard.on_press_key(TECLA_INICIAR, lambda _: self.iniciar_bot())
        keyboard.on_press_key(TECLA_PARAR, lambda _: self.parar_bot())

        self.bot_thread = threading.Thread(target=self.loop_principal_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()

    def atualizar_log(self, mensagem):
        print(f"[Log] {mensagem}")
        self.root.after(0, self.lbl_log.config, {"text": mensagem})

    def marcar_agua(self):
        if not self.is_running:
            self.pos_agua_x, self.pos_agua_y = pyautogui.position()
            mensagem = f"💧 Água: ({self.pos_agua_x}, {self.pos_agua_y})"
            self.root.after(0, self.lbl_agua.config, {"text": mensagem, "fg": "#3498db"})
            self.atualizar_log("Posição da água gravada com sucesso!")

    def iniciar_bot(self):
        if not self.is_running:
            if self.pos_agua_x is None or self.pos_agua_y is None:
                self.atualizar_log(f"ERRO: Tem que colocar o local da água! {TECLA_MARCAR.upper()}!")
                return
            
            # Trava na janela que está ativa
            janela_ativa = pyautogui.getActiveWindow()
            if janela_ativa and NOME_JANELA_JOGO in janela_ativa.title:
                self.janela_alvo = janela_ativa
                self.root.after(0, self.lbl_alvo.config, {"text": f"Alvo: {janela_ativa.title} Travado!"})
            else:
                janelas = pyautogui.getWindowsWithTitle(NOME_JANELA_JOGO)
                if janelas:
                    self.janela_alvo = janelas[0]
                    self.root.after(0, self.lbl_alvo.config, {"text": f"Alvo: Jogo Padrão Travado!"})
                else:
                    self.atualizar_log("ERRO: Jogo não encontrado.")
                    return

            self.is_running = True
            self.root.after(0, self.lbl_status.config, {"text": "Status: ATIVADO", "fg": "#2ecc71"})
            self.atualizar_log("Bot ligado. Iniciando pesca...")

    def parar_bot(self):
        if self.is_running:
            self.is_running = False
            self.primeira_pesca = True 
            self.janela_alvo = None
            self.root.after(0, self.lbl_status.config, {"text": "Status: PARADO", "fg": "#e74c3c"})
            self.root.after(0, self.lbl_alvo.config, {"text": "Alvo: Liberado"})
            self.atualizar_log("Ciclo interrompido.")

    def focar_janela_jogo(self):
        self.atualizar_log(f"Focando o Alvo Travado...")
        try:
            if self.janela_alvo:
                if self.janela_alvo.isMinimized:
                    self.janela_alvo.restore()
                self.janela_alvo.activate()
                time.sleep(0.8) 
                return True
            return False
        except:
            return True 

    def rotina_pesca(self):
        if not self.focar_janela_jogo():
            return False

        canto_x = self.janela_alvo.left + 10 if self.janela_alvo else 10
        canto_y = self.janela_alvo.top + 10 if self.janela_alvo else 10
        mover_rato_fisico(canto_x, canto_y)
        time.sleep(0.2)

        # Agora usamos diretamente a posição gravada pela tecla F9
        x, y = self.pos_agua_x, self.pos_agua_y
        
        if not self.primeira_pesca:
            self.atualizar_log("Renovação: 'V' + Clique (Cancelar)...")
            pydirectinput.press('v')
            time.sleep(0.4) 
            mover_rato_fisico(x, y)
            time.sleep(0.3) 
            clicar_rato_fisico()
            time.sleep(1.0)
        else:
            self.primeira_pesca = False

        self.atualizar_log("Ação: 'V' + Clique (Pescar)...")
        pydirectinput.press('v')
        time.sleep(0.4) 
        mover_rato_fisico(x, y)
        time.sleep(0.3) 
        clicar_rato_fisico()
        
        time.sleep(0.3)
        mover_rato_fisico(canto_x, canto_y)
        
        return True

    def loop_principal_bot(self):
        while True:
            if self.is_running:
                sucesso = self.rotina_pesca()
                
                if sucesso:
                    self.atualizar_log(f"Pescando ({TEMPO_PESCA_MINUTOS}m)...")
                    tempo_total_seg = TEMPO_PESCA_MINUTOS * 60
                    tempo_decorrido = 0
                    
                    while tempo_decorrido < tempo_total_seg and self.is_running:
                        time.sleep(1)
                        tempo_decorrido += 1
                        
                else:
                    self.atualizar_log("Falha ao focar jogo. Tentando em 3s...")
                    time.sleep(3)
                    
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = BotPescaApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit()
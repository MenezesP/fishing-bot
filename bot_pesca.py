import pyautogui
import pydirectinput
import keyboard
import time
import sys
import os
import threading
import tkinter as tk
import ctypes
from ctypes import wintypes

TEMPO_PESCA_MINUTOS = 6
INTERVALO_ANTI_AFK_SEGUNDOS = 45

NOME_JANELA_JOGO = 'PokeMemories'
IMG_AGUA = 'agua.png'
NIVEL_CONFIANCA = 0.6  

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
    """Injeta movimento absoluto no driver do rato (0 a 65535)."""
    largura_ecra = ctypes.windll.user32.GetSystemMetrics(0)
    altura_ecra = ctypes.windll.user32.GetSystemMetrics(1)
    
    x_calc = int(x * 65535 / largura_ecra)
    y_calc = int(y * 65535 / altura_ecra)

    extra = ctypes.pointer(ctypes.c_ulong(0))
    ii_ = Input_I()
    # 0x0001 = MOVE, 0x8000 = ABSOLUTE
    ii_.mi = MouseInput(x_calc, y_calc, 0, 0x0001 | 0x8000, 0, extra) 
    comando = Input(ctypes.c_ulong(0), ii_) # 0 = INPUT_MOUSE
    ctypes.windll.user32.SendInput(1, ctypes.pointer(comando), ctypes.sizeof(comando))

def clicar_rato_fisico():
    """Injeta um clique esquerdo no driver do rato."""
    extra = ctypes.pointer(ctypes.c_ulong(0))
    
    # 0x0002 = LEFTDOWN
    ii_down = Input_I()
    ii_down.mi = MouseInput(0, 0, 0, 0x0002, 0, extra)
    cmd_down = Input(ctypes.c_ulong(0), ii_down)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd_down), ctypes.sizeof(cmd_down))
    
    time.sleep(0.05)
    
    # 0x0004 = LEFTUP
    ii_up = Input_I()
    ii_up.mi = MouseInput(0, 0, 0, 0x0004, 0, extra)
    cmd_up = Input(ctypes.c_ulong(0), ii_up)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd_up), ctypes.sizeof(cmd_up))

def eh_administrador():
    """Verifica se o script está a rodar com privilégios máximos."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class BotPescaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot Pesca v3")
        self.root.geometry("280x180")
        self.root.attributes('-topmost', True) 
        self.root.configure(bg='#2c3e50')
        self.root.resizable(False, False)

        self.is_running = False
        self.primeira_pesca = True 

        # --- UI Elementos ---
        self.lbl_titulo = tk.Label(root, text="🐟 Poke Memories Bot", font=("Arial", 12, "bold"), bg='#2c3e50', fg='white')
        self.lbl_titulo.pack(pady=5)
        
        # Alerta de Administrador
        if not eh_administrador():
            self.lbl_admin = tk.Label(root, text="⚠️ ABRE COMO ADMINISTRADOR!", font=("Arial", 9, "bold"), bg='#c0392b', fg='white')
            self.lbl_admin.pack(fill=tk.X)

        self.lbl_status = tk.Label(root, text="Status: PARADO", font=("Arial", 10, "bold"), bg='#2c3e50', fg='#e74c3c')
        self.lbl_status.pack(pady=2)

        self.lbl_log = tk.Label(root, text="Aguardando comandos...", font=("Arial", 9), bg='#2c3e50', fg='#bdc3c7')
        self.lbl_log.pack(pady=5)

        # Botões
        frame_botoes = tk.Frame(root, bg='#2c3e50')
        self.btn_iniciar = tk.Button(frame_botoes, text=f"Iniciar ({TECLA_INICIAR.upper()})", command=self.iniciar_bot, bg='#27ae60', fg='white', width=12)
        self.btn_iniciar.grid(row=0, column=0, padx=5)
        
        self.btn_parar = tk.Button(frame_botoes, text=f"Parar ({TECLA_PARAR.upper()})", command=self.parar_bot, bg='#c0392b', fg='white', width=12)
        self.btn_parar.grid(row=0, column=1, padx=5)
        frame_botoes.pack()

        if not os.path.exists(IMG_AGUA):
            self.atualizar_log("ERRO: agua.png não encontrada!")
            self.lbl_status.config(text="ERRO DE IMAGEM", fg="red")

        keyboard.on_press_key(TECLA_INICIAR, lambda _: self.iniciar_bot())
        keyboard.on_press_key(TECLA_PARAR, lambda _: self.parar_bot())

        self.bot_thread = threading.Thread(target=self.loop_principal_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()

    def atualizar_log(self, mensagem):
        print(f"[Log] {mensagem}")
        self.root.after(0, self.lbl_log.config, {"text": mensagem})

    def iniciar_bot(self):
        if not self.is_running and os.path.exists(IMG_AGUA):
            self.is_running = True
            self.root.after(0, self.lbl_status.config, {"text": "Status: ATIVADO", "fg": "#2ecc71"})
            self.atualizar_log("Bot ligado. A focar jogo...")

    def parar_bot(self):
        if self.is_running:
            self.is_running = False
            self.primeira_pesca = True  # Reseta para o próximo ciclo inicial
            self.root.after(0, self.lbl_status.config, {"text": "Status: PARADO", "fg": "#e74c3c"})
            self.atualizar_log("Ciclo interrompido.")

    def executar_anti_afk(self):
        self.atualizar_log("Anti-AFK: A virar...")
        pydirectinput.keyDown('ctrl')
        pydirectinput.press('up')
        time.sleep(0.3)
        pydirectinput.press('down')
        pydirectinput.keyUp('ctrl')

    def focar_janela_jogo(self):
        self.atualizar_log(f"A focar '{NOME_JANELA_JOGO}'...")
        try:
            janelas = pyautogui.getWindowsWithTitle(NOME_JANELA_JOGO)
            if janelas:
                janela_jogo = janelas[0]
                if janela_jogo.isMinimized:
                    janela_jogo.restore()
                janela_jogo.activate()
                time.sleep(0.8) # Tempo maior para garantir que o Windows tirou a proteção
                return True
            else:
                self.atualizar_log("Erro: Jogo não encontrado.")
                return False
        except:
            return True 

    def procurar_imagem(self, imagem, tentativas=3):
        largura_ecra, altura_ecra = pyautogui.size()
        regiao_segura = (int(largura_ecra*0.15), int(altura_ecra*0.20), int(largura_ecra*0.60), int(altura_ecra*0.60))
        
        self.atualizar_log("A procurar água...")
        for tentativa in range(tentativas):
            try:
                posicao = pyautogui.locateCenterOnScreen(imagem, confidence=NIVEL_CONFIANCA, region=regiao_segura)
                if posicao is not None:
                    return posicao
            except:
                pass
            time.sleep(0.4)
        return None

    def rotina_pesca(self):
        if not self.focar_janela_jogo():
            return False

        mover_rato_fisico(10, 10)
        time.sleep(0.2)

        posicao_agua = self.procurar_imagem(IMG_AGUA)
        
        if posicao_agua:
            x, y = int(posicao_agua.x), int(posicao_agua.y)
            
            # Se não for a primeira pesca, precisamos cancelar a pesca atual
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

            # --- AÇÃO PRINCIPAL (Lança a pesca) ---
            self.atualizar_log("Ação: 'V' + Clique (Pescar)...")
            pydirectinput.press('v')
            time.sleep(0.4) 
            mover_rato_fisico(x, y)
            time.sleep(0.3) 
            clicar_rato_fisico()
            
            time.sleep(0.3)
            mover_rato_fisico(10, 10)
            
            return True
        else:
            self.atualizar_log("Falha: Água não encontrada.")
            return False

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
                        
                        if tempo_decorrido % INTERVALO_ANTI_AFK_SEGUNDOS == 0 and self.is_running:
                            self.focar_janela_jogo() 
                            self.executar_anti_afk()
                            self.atualizar_log("Pescando...")
                else:
                    self.atualizar_log("Nova tentativa em 3s...")
                    time.sleep(3)
                    
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = BotPescaApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit()
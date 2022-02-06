# Parte de interface Grafica
from enigma import Enigma
import threading
import re


def print_ui_header():
    print(''' _____ _   _ ___ ____ __  __    _
| ____| \ | |_ _/ ___|  \/  |  / \ \r
|  _| |  \| || | |  _| |\/| | / _ \ \r
| |___| |\  || | |_| | |  | |/ ___ \ \r
|_____|_| \_|___\____|_|  |_/_/   \_\ ''')

    print("\nFeito pelo grupo 7.\n\n")

    com_str = "COMANDOS: /code {texto}               - Codifica um texto usando as configurações atuais.\n" \
              "          /help                       - Exibe esse menu de ajuda\n" \
              "          /exit ou Ctrl+C             - Termina o programa.\n" \
              "          /rotr {NUM:NUM:NUM}         - Ajusta os rotores para as posições especificadas, os números\n" \
              "                                         devem ser menores ou iguais a 26.\n" \
              "          /plug {LETRA:LETRA, ...}    - Conecta duas letras no plug-board. Se alguma das letras\n" \
              "                                         já estiver conectada, a conexão mais nova tem prioridade.\n" \
              "          /lckr                       - Trava ou destrava o rotor. Isso impede a posição do rotor de\n" \
              "                                         mudar ENTRE diferentes chamadas pro comando code.\n"
    print(com_str)


class UI(threading.Thread):
    def __init__(self, enigma = Enigma(), name="enigma-ui-thread"):

        self.cmd = None
        self.args = None
        self.enigma = enigma
        self.lock_rotor_flag = False
        self.allowed_commands = ({"/code": self.code, "/exit": self.exit, "/rotr": self.rotr, "/plug": self.plug,
                                  "/help": self.help, "/lckr": self.lckr})
        print_ui_header()

        super().__init__(name=name)
        self.start()

    def lckr(self):
        self.lock_rotor_flag ^= True
        print(f"\nTrava do rotor entre cifras {'ligada' if self.lock_rotor_flag else 'desligada'}")

    def help(self):
        print_ui_header()

    def code(self):
        tmp = None
        if self.lock_rotor_flag:
            tmp = self.enigma.rotor_pos

        if self.args:
            txt = "".join(self.args)
            print(f"\nTexto de input -> {txt}")
            self.enigma.txt = txt
            print(f"Output -> {self.enigma.encrypt()}")

        if self.lock_rotor_flag:
            self.enigma.rotor_pos = tmp

    def exit(self):
        exit()

    def rotr(self):
        if self.args:
            form = "".join(self.args)
            self.enigma.rotor_pos = form


    def plug(self):
        plugs = "".join(self.args).strip("{}").strip()
        plugs = plugs.split(",")

        d = {plug.split(":")[0].upper(): plug.split(":")[1].upper() for plug in plugs}
        print(f"Plug-board conectada: {d}")
        self.enigma.plugboard = d


    def run(self):
        while True:
            self.args = input(f"{self.enigma.rotor_pos} -> ")
            self.cmd = re.search("^/[a-z]{4}", self.args)


            if self.cmd:
                self.cmd = self.args[self.cmd.start():self.cmd.end()]
                try:
                    self.args = self.args.split()[1::]
                except IndexError:
                    self.args = None

                if self.cmd in self.allowed_commands:
                    self.allowed_commands[self.cmd]()
                else:
                    print("\nComando Inválido, digite /help para obter ajuda.")


if __name__ == "__main__":
    EnigmaUI = UI()


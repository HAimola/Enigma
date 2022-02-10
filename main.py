import logging

import enigma
import logging
import threading
import sys
import re


def print_ui_header():
    print(''' _____ _   _ ___ ____ __  __    _
| ____| \ | |_ _/ ___|  \/  |  / \ \r
|  _| |  \| || | |  _| |\/| | / _ \ \r
| |___| |\  || | |_| | |  | |/ ___ \ \r
|_____|_| \_|___\____|_|  |_/_/   \_\ ''')

    print("\nFeito pelo grupo 7.\n\n")

    com_str = "COMANDOS: /encrypt {texto}            - Codifica um texto usando as configurações atuais.\n" \
              "          /help                       - Exibe esse menu de ajuda\n" \
              "          /exit ou Ctrl+C             - Termina o programa.\n" \
              "          /selrotor (NUM, NUM, NUM)   - Seleciona o tipo de rotor \n" \
              "          /selreflector 'B' ou 'C'    - Seleciona o tipo de refletor usado\n" \
              "          /setrotor NUM:NUM:NUM       - Ajusta os rotores para as posições especificadas, os números\n" \
              "                                         devem ser menores ou iguais a 26.\n" \
              "          /plug {LETRA:LETRA, ...}    - Conecta duas letras no plug-board. Se alguma das letras\n" \
              "                                         já estiver conectada, a conexão mais nova tem prioridade.\n" \
              "          /rmplug {LETRA:LETRA, ...}  - Desconecta duas letras que já estão no plug-board.\n" \
              "          /lockrotor                  - Trava ou destrava o rotor. Isso impede a posição do rotor de\n" \
              "                                         mudar ENTRE diferentes chamadas pro comando code.\n" \
              "          /reset                      - Reinicia a máquina para todas as condições iniciais\n" \

    print(com_str)


class UI(threading.Thread):
    def __init__(self, enigma_in=None, name="enigma-ui-thread"):

        self.logger = logging.getLogger("enigma.logger")
        if "-debug" in sys.argv:
            self.set_debug()

        self.cmd = None
        self.args = None
        self.enigma = enigma_in if isinstance(enigma_in, enigma.Enigma) else enigma.Enigma()
        self.lock_rotor_flag = False
        self.allowed_commands = ({"/encrypt": self.encrypt, "/exit": self.exit, "/setrotor": self.setrotor,
                                  "/plug": self.plug, "/rmplug": self.rmplug, "/help": self.help,
                                  "/selrotor": self.selrotor, "/selreflector":self.selreflector,
                                  "/lockrotor": self.lockrotor, "/reset": self.reset, "/debug": self.set_debug})
        print_ui_header()

        super().__init__(name=name)
        self.start()

    def lockrotor(self):
        self.logger.debug(f"[UI_CALL] Comando /lockrotor. Estado anterior: {self.lock_rotor_flag=}")
        self.lock_rotor_flag ^= True
        self.logger.info(f"Trava do rotor entre cifras {'ligada' if self.lock_rotor_flag else 'desligada'}")

    def help(self):
        self.logger.debug("[UI_CALL] Comando /help")
        print_ui_header()

    def encrypt(self):
        self.logger.debug(f"[UI_CALL] Comando /encrypt: {self.args=}")
        tmp = None
        if self.lock_rotor_flag:
            tmp = self.enigma.rotor_pos
            self.logger.debug(f"Rotation lock ativado: {self.enigma.rotor_pos=}")

        if self.args:
            txt = "".join(self.args)
            self.enigma.txt = txt
            enc = self.enigma.encrypt()

            if enc:
                self.logger.info(f"Input  -> {txt}")
                self.logger.info(f"Output -> {enc}")

        if self.lock_rotor_flag:
            self.logger.debug(f"Restaurando rot_pos: {self.enigma.rotor_pos=} -> {tmp}")
            self.enigma.rotor_pos = tmp

    def exit(self):
        self.logger.debug("[UI_CALL] Comando /exit")
        exit()

    def setrotor(self):
        if self.args:
            form = "".join(self.args)
            self.logger.debug(f"[UI_CALL] Comando /setrotor: {self.args}")
            self.enigma.rotor_pos = form

    def plug(self):
        self.logger.debug("[UI_CALL] Comando /plug")
        plugs = "".join(self.args).strip("{}").strip()

        if not self.args:
            self.logger.debug(f"Args de plug vazio. {self.args=}")
            self.logger.warning("Nenhum plug foi adicionado. Use o formato {LETRA:LETRA}")
            return

        if not plugs:
            self.logger.warning("Não foi possível detectar plugs válidos no input. Use o formato {LETRA:LETRA}")
        else:
            self.logger.debug(f"Par detectado, formato aceito: {plugs=}")
            plugs = plugs.split(",")
            d = {plug.split(":")[0].upper(): plug.split(":")[1].upper() for plug in plugs}
            self.enigma.plugboard = d
            self.logger.debug(f"Dicionario de input adicionado")

    def selrotor(self):
        self.logger.debug("[UI_CALL] Comando /selrotor")

        if self.args:
            tup = "".join(self.args).strip("()").split(",")
            try:
                tup = tuple((int(rotor) for rotor in tup))
                self.logger.debug(f"Tupla detectada, formato aceito: {tup=}, {isinstance(all(tup), int)=}")
            except ValueError:
                self.logger.debug(f"Erro no cast para int do input do rotor_config. {tup=}")
                self.logger.error("Tipo de rotor inválido. Selecione um rotor com números de 1 à 5.")
                tup = ()
            self.enigma.rotor_config = tup
        else:
            self.logger.debug(f"Args de rotor vazio. {self.args=}")
            self.logger.warning("Nenhum rotor foi escolhido. Use o formato (NÚMERO, NÚMERO, NÚMERO)")

    def selreflector(self):
        self.logger.debug("[UI_CALL] Comando /selreflector")
        refl = self.args[0]

        if self.args:
            if len(refl) > 1:
                self.logger.debug(f"Letra de refletor >1: {refl=}, {len(refl)}")
                self.logger.error("Tipo de refletor inválido. Selecione B ou C.")
            elif refl not in ("B", "C"):
                self.logger.debug(f"Letra inválida: {refl=}, {refl in ('B', 'C')=}")
                self.logger.error("Tipo de refletor inválido. Selecione B ou C.")
            else:
                self.enigma.reflector_option = refl
        else:
            self.logger.debug(f"Args de refletor vazio. {self.args=}")
            self.logger.warning("Nenhum refletor foi escolhido. Digite B ou C")

    def rmplug(self):
        self.logger.debug("[UI_CALL] Comando /rmplug (WIP)")

    def reset(self):
        self.logger.debug("[UI_CALL] Comando /reset")
        self.logger.info("Resetando configurações da máquina.")

        self.enigma._plugboard = {}
        self.enigma.rotor_pos = "0:0:0"
        self.enigma.rotor_config = ()
        self.enigma.reflector_option = "B"

        self.logger.debug(f"Reset da instancia: {self.enigma.plugboard}, {self.enigma.rotor_pos}, "
                          f"{self.enigma.rotor_config}, {self.enigma.reflector_option}")

    def set_debug(self):
        self.logger.debug("[UI_CALL] Comando /debug")
        if self.logger.level == logging.DEBUG:
            self.logger.info("Desativando debugger")
            self.logger.setLevel(logging.INFO)
            enigma.set_debug()
        else:
            self.logger.info("Ativando debugger")
            self.logger.setLevel(logging.DEBUG)
            enigma.set_debug()

    def run(self):
        while True:
            self.logger.debug("[UI_CALL] Input")
            self.args = input(f"{self.enigma.rotor_pos} -> ")

            self.cmd = re.search("^/[a-z]*", self.args)

            if self.cmd:
                self.cmd = self.args[self.cmd.start():self.cmd.end()]
                self.args = self.args.split()[1::]

                self.logger.debug(f"Resultado do regex slicing do input {self.cmd=}, {self.args=}")
                if self.cmd in self.allowed_commands:
                    self.logger.debug(f"Commando encontrado: {self.allowed_commands[self.cmd]}")
                    self.allowed_commands[self.cmd]()
                else:
                    self.logger.warning("Comando Inválido, digite /help para obter ajuda.")


if __name__ == "__main__":
    EnigmaUI = UI()

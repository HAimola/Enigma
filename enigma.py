from hardware_tables import *

import re
import logging
import colorama

logging.root.setLevel(level=logging.INFO)
SPECIAL_CHAR_RE = re.compile("[+_`!@#$%^&*=().,';~/\d-]")
colorama.init()


# Classe que formata as cores do logger no win32
class LogFormatter(logging.Formatter):
    fmt = "[%(levelname)s] %(asctime)s - %(message)s"

    level_color = {
        logging.DEBUG: colorama.Fore.GREEN + fmt + colorama.Fore.RESET,
        logging.INFO: colorama.Fore.WHITE + fmt + colorama.Fore.RESET,
        logging.WARNING: colorama.Fore.YELLOW + fmt + colorama.Fore.RESET,
        logging.ERROR: colorama.Fore.LIGHTRED_EX + fmt + colorama.Fore.RESET,
        logging.CRITICAL: colorama.Fore.RED + fmt + colorama.Fore.RESET
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        log_fmt = self.level_color[record.levelno]
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def set_debug():
    if logging.root.level == logging.DEBUG:
        logging.root.setLevel(logging.INFO)
    else:
        logging.root.setLevel(logging.DEBUG)


# Função que lê a chave de um dicionário ao receber o valor
# Importante para inverter o caminho dos rotores quando eles passam pelo refletor
def read_key(d: dict, val):
    dict_values = list(d.values())
    dict_keys = list(d.keys())

    if val in dict_values:
        return dict_keys[dict_values.index(val)]


# Classe que codifica e aceita as configurações do usuário
class Enigma:

    def __init__(self, input_text: str = "", rotor_config: tuple[str, str, str] = None, rotor_pos: str = "00:00:00",
                 plugboard: dict = None, reflector_config: str = "B", logger=logging.getLogger("enigma.logger")):

        self.logger: logging.Logger = logger

        self.logger.setLevel(logging.root.level)
        handler = logging.StreamHandler()
        handler.setFormatter(LogFormatter())
        self.logger.addHandler(handler)

        self.logger.debug(f"[CALL] Objeto Enigma Criado: {self}")

        self._txt: str = ""
        self._rotor_config: tuple = ()
        self._rotor_pos: str = ""
        self._plugboard: dict = {}
        self._rotor_pos: str = ""
        self._reflector_option: str = ""
        self.rotor1 = None
        self.rotor2 = None
        self.rotor3 = None
        self.reflector = None

        self.txt = input_text
        self.reflector_option: str = reflector_config
        self.rotor_config: tuple = rotor_config
        self.rotor_pos = rotor_pos
        self.plugboard = plugboard if plugboard is not None else {}

    @property
    def txt(self):
        return self._txt

    @txt.setter
    def txt(self, value):
        search = re.findall(SPECIAL_CHAR_RE, value)
        self.logger.debug(f"[CALL] txt setter: args={value}, {type(value)}")
        self.logger.debug(f"txt regex: {search=}, {len(search)=}")

        # A máquina Enigma original só encriptava letras
        # Termina o programa caso não seja string e se tem algum caractér especial ou número.
        if not isinstance(value, str):
            self.logger.debug("txt input inválido")
            self.logger.error(f"Dados passados - {value} - não são em forma de texto! ")
        elif search:
            self.logger.debug("Regex search encontrou caractéres especiais.")
            self.logger.error("String com caractéres especiais ou números! Use apenas letras.")
        else:
            self._txt = value.upper()

    @property
    def rotor_pos(self):
        return f"{self.INTER_23.r2.shift:02d}:{self.INTER_12.r2.shift:02d}:{self.INTER_IN1.r2.shift:02d}"

    @rotor_pos.setter
    def rotor_pos(self, value):
        # O formato da posição do Rotor é bem específico:
        # Exitem 3 rotores ativos e eles têm posições de 0 à 25
        # Caso o usuário queira alterar o valor da posição, ele deve fazer no formato correto (Digito:Digito:Digito).
        # Termina o programa se não tiverem 3 grupos de digitos ou se eles não forem digitos

        self._rotor_pos = "0:0:0" if not self._rotor_pos else self._rotor_pos

        search = re.findall("\d{1,2}:\d{1,2}:\d{1,2}", value)
        if not search:
            self.logger.error("Posição do Rotor inválida. O padrão desta opção deve ser: Número:Número:Número")
            return

        self._rotor_pos = value
        search = re.findall("\d{1,2}", self._rotor_pos)

        self.INTER_IN1.absolute_rotor_shift(int(search[2]))
        self.INTER_12.absolute_rotor_shift(int(search[1]))
        self.INTER_23.absolute_rotor_shift(int(search[0]))
        self.logger.debug(f"Regex do rotor_pos: {search}")

    @property
    def plugboard(self):
        return self._plugboard

    @plugboard.setter
    def plugboard(self, d: dict or str):
        self.logger.debug(f"[CALL] plugboard setter, args={d}, {type(d)}")
        self.logger.debug(f"Estado anterior do dict plugboard {self._plugboard}")

        if isinstance(d, dict):
            self.logger.debug(f"Dict de plugboard detectado.")
            for key, value in d.items():
                if len(key) > 1 or len(value) > 1:

                    self.logger.error(f"Os plugs só podem ser conectados em pares um à um.")
                    break

                if re.findall(SPECIAL_CHAR_RE, key) or re.findall(SPECIAL_CHAR_RE, value):
                    self.logger.debug(f"Input na plugboard invalido: {key}:{value}, {type(key)}:{type(value)}")
                    self.logger.error(f"Apenas letras de A a Z podem ser inseridas como plugs no plugboard.")
                    break

                if not key:
                    self.logger.warning(f"Plug {value} não está sendo conectado à nada. Descartando plug.")
                    continue

                if not value:
                    self.logger.warning(f"Plug {key} não está sendo conectado à nada. Descartando plug.")
                    continue

                self._plugboard[key] = value
                self.logger.info(f"Par {key}:{value} adicionado ao plugboard!")

            err_keys = []

            for key in self._plugboard:
                if key in self._plugboard.values():
                    err_keys.append(key)
                    self.logger.debug(f"Encontrado duplicados no dict do plugboard: {key=}")
                    self.logger.warning(f"Existem letras com duas conexões ao mesmo tempo! "
                                        f"Descartando plug {key}:{self._plugboard[key]}")

            self.logger.debug(f"{err_keys=}")

            for key in err_keys:
                self._plugboard.pop(key)
                self.logger.debug(f"Removendo key {key}. Estado posterior: {self._plugboard=}")

            self.logger.info(f"Configuração atual: {self._plugboard}")

    @property
    def rotor_config(self):
        return self._rotor_config

    @rotor_config.setter
    def rotor_config(self, value):
        self.logger.debug(f"[CALL] rotor_config setter: args={value}, type(args)={type(value)}")

        if isinstance(value, tuple):
            if len(value) < 3:
                self.logger.debug(f"Poucos inputs. Input do rotor_config={value}")
                self.logger.error("Configurações de rotor insuficientes. São necessários pelo menos 3 rotores.")
                return
            for i in value:
                if i > 5 or i < 1:
                    self.logger.debug(f"Cast com sucesso, mas input fora do limite. {value=}")
                    self.logger.error("Número do rotor não existe. Escolha um número de 1 à 5.")
                    return

            self._rotor_config = value

        elif self.rotor_config is None or not self.rotor_config:
            self.logger.debug(f"{self._rotor_config=}. Usando default (1, 2, 3)")
            self._rotor_config = (1, 2, 3)

        rotors_options = (ROTOR_1, ROTOR_2, ROTOR_3, ROTOR_4, ROTOR_5)

        self.rotor1 = rotors_options[self._rotor_config[0]-1]
        self.rotor2 = rotors_options[self._rotor_config[1]-1]
        self.rotor3 = rotors_options[self._rotor_config[2]-1]

        self.logger.debug(f"Rotores selecionados: {self.rotor1.number}, {self.rotor2.number}, {self.rotor3.number}")

        self.INTER_3R = Interface(self.rotor3, self.reflector)
        self.INTER_23 = Interface(self.rotor2, self.rotor3, self.INTER_3R)
        self.INTER_12 = Interface(self.rotor1, self.rotor2, self.INTER_23)
        self.INTER_IN1 = Interface(InputRotor("in"), self.rotor1, self.INTER_12)

        self.logger.debug(f"Interfaces criadas: self.INTER_IN1.r2 == self.INTER_12.r1 -> "
                          f"{self.INTER_IN1.r2 == self.INTER_12.r1}")

    @property
    def reflector_option(self):
        return self._reflector_option

    @reflector_option.setter
    def reflector_option(self, value):
        self.logger.debug(f"[CALL] reflector_option setter: args={value}")

        # Só existem 2 modelos convencionais de refletor: B e C (existem as variações Dünn, mas eu não implementei)
        if value not in ("C", "B"):
            self.logger.debug(f"refector input inválido {value=}")
            self.logger.error("O modelo de refletor não existe. Escolha o refletor B ou C.")
            self.reflector_option = "B"

        self._reflector_option = value
        reflector_options = (REFLECTOR_B, REFLECTOR_C)

        if value == "B":
            self.reflector = reflector_options[0]
        else:
            self.reflector = reflector_options[1]

        self.logger.debug(f"Refletor selecionado: {self.reflector_option}")

    def instance_in_plugboard(self, plug: str):
        """
        Checa se uma letra está na plug board e, caso esteja, retorna ela trocada.

            Parametros
                    plug (str): Uma string de tamanho 1 que será resgatada do dicionário Enigma.plugboard

            Returns
                    plug (str): caso a letra não esteja no plugboard, retorna o plug sem alteração
                                Caso esteja, retorna sua contraparte no dicionário Enigma.plugboard

        """
        if plug in self.plugboard:
            self.logger.debug(f"Letra é instância nas keys do plugboard: {plug=}, {self.plugboard[plug]=}")
            return self.plugboard[plug]
        elif plug in self.plugboard.values():
            self.logger.debug(f"Letra é instância nos values do plugboard: {plug=}, {self.plugboard[plug]=}")
            return read_key(self.plugboard, plug)
        return plug

    # Função que de fato encripta - e decripta - o texto de input.
    # Por conta da arquitetura do programa, implementar outras variações dos rotores ou dos refletores é
    # bem simples e pode ser feito só colocando as variáveis no script "hardware_tables.py"
    def encrypt(self) -> str:
        self.logger.debug(f"[CALL] Encrypt: {self.txt}, {self.rotor_config}, {self.rotor_pos}, {self.reflector.name}")

        result = ""

        for letter in self.txt:

            # Se for um espaço, simplesmente adiciona no resultado
            # Não existe codificação para o espaço
            # TODO: Adicionar a opção de codificação sem espaço
            if letter == " ":
                result += letter
                continue

            letter = self.instance_in_plugboard(letter)
            self.INTER_IN1.shift_rotor()

            # Uma explicação breve da arquitetura e da máquina:
            # - Existem 2 tipos de dicionários no programa, ambos no script hardware_tables.py, os dicionários
            #   de cifragem  (que têm os nomes de ROTOR_1 à ROTOR_5) e os dicionários de interface
            #  (INTER_IN1, INTER_12, ...)
            #
            # - Os dicionários de cifragem são as tabelas que de fato fazem a encriptagem.  No programa, eles mostram
            #  a equivalência entre uma e letra e sua versão cifrada. Por exemplo, se o usuário apertar a letra A no
            #  teclado, o Rotor_1 traduziria a letra A para E. O design da máquina enigma é bidirecional, ou
            #  recíproco, o que significa que decifrar e cifrar são simplesmente operações inversas do mesmo mecanismo.
            #  Assim como ela consegue cifrar a letra A em E, ela decifra E em A.
            #
            # - Os dicionários de interface requerem um pouco mais de conhecimento interno sobre a máquina em si.
            #   Por motivos criptográficos, existem 3 rotores que encriptam as letras de maneiras diferentes. Esses
            #   rotores estão ligados "em série", ou em sequência, da seguinte maneira:
            #
            # ENTRADA ROTOR 1   A B C D E F G H I J ...                                    A  ENT. ROT 1
            #                   | | | | | | | | | |             Quando o usuário aperta    |
            #                  FIOS EMBARALHADOS (ROTOR_1)      o botão A, o rotor 1       |_________________
            #                   | | | | | | | | | |             embaralha e joga o sinal                    |
            # SAÍDA ROTOR 1     A B C D E F G H I J ...         para o fio E, que é                         E SAI. ROT 1
            # ENTRADA ROTOR 2   A B C D E F G H I J ...         consequentemente embara-                    E ENT. ROT 2
            #                   | | | | | | | | | |             lhado pelo 2 e jogado pro                   |
            #                  FIOS EMBARALHADOS (ROTOR_2)      fio S. Olhe o circuito ao                   |_____
            #                   | | | | | | | | | |             lado                                              |
            # SAÍDA ROTOR 2     A B C D E F G H I J                   ------->                     SAI. ROT 2     S
            #
            #  Para adicionar complexidade e robustês à cifra, os rotores giram entre si. Isso muda a interface entre
            # os rotores. O dicionário apenas mantém um registro da interface atual entre eles:
            #
            # ROTOR 1 GIROU   B C D E F G H I J K ... Z A  } Interface entre 1 e 2 -> INTER_12
            # ROTOR 2 NORMAL  A B C D E F G H I J ... Y Z  }

            tmp = self.INTER_IN1[letter]
            tmp = self.rotor1[tmp]
            tmp = self.INTER_12[tmp]
            tmp = self.rotor2[tmp]
            tmp = self.INTER_23[tmp]
            tmp = self.rotor3[tmp]
            tmp = self.INTER_3R[tmp]

            tmp = self.reflector[tmp]

            tmp = read_key(self.INTER_3R, tmp)
            tmp = read_key(self.rotor3, tmp)
            tmp = read_key(self.INTER_23, tmp)
            tmp = read_key(self.rotor2, tmp)
            tmp = read_key(self.INTER_12, tmp)
            tmp = read_key(self.rotor1, tmp)
            tmp = read_key(self.INTER_IN1, tmp)

            tmp = self.instance_in_plugboard(tmp)

            result += tmp

        return result

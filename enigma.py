from hardware_tables import ROTOR_1, ROTOR_2, ROTOR_3, ROTOR_4, ROTOR_5, REFLECTOR_B, REFLECTOR_C
from hardware_tables import _ROT_INTER_IN1, _ROT_INTER_12, _ROT_INTER_23, _ROT_INTER_3R

import re
import logging
import colorama


logging.root.setLevel(level=logging.INFO)
SPECIAL_CHAR_RE = re.compile("[+_`!@#$%^&*=().,';~/\d-]")
colorama.init()


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


def default_rotors_and_interfaces():
    global ROT_INTER_IN1, ROT_INTER_12, ROT_INTER_23, ROT_INTER_3R

    ROT_INTER_IN1 = _ROT_INTER_IN1.copy()
    ROT_INTER_12 = _ROT_INTER_12.copy()
    ROT_INTER_23 = _ROT_INTER_23.copy()
    ROT_INTER_3R = _ROT_INTER_3R.copy()


def shift_values_right(d: dict, offset: int):
    if offset < 0:
        shift_values_left(d, abs(offset))

    list_d = list(d.values())
    offset = offset % len(list_d)

    list_d = list_d[-offset:] + list_d[:-offset]
    return {key: list_d[shift_index] for shift_index, key in enumerate(d.keys())}


def shift_values_left(d: dict, offset: int):
    list_d = list(d.values())
    offset = offset % len(list_d)

    list_d = list_d[offset:] + list_d[:offset]
    return {key: list_d[shift_index] for shift_index, key in enumerate(d.keys())}


def shift_keys_left(d: dict, offset: int):
    list_d = list(d.keys())
    offset = offset % len(list_d)

    list_d = list_d[offset:] + list_d[:offset]
    return {list_d[shift_index]: value for shift_index, value in enumerate(d.values())}


def shift_keys_right(d: dict, offset: int):
    if offset < 0:
        shift_keys_left(d, abs(offset))

    list_d = list(d.keys())
    offset = offset % len(list_d)

    list_d = list_d[-offset:] + list_d[:-offset]
    return {list_d[shift_index]: value for shift_index, value in enumerate(d.values())}


# Função que lê a chave de um dicionário ao receber o valor
# Importante para inverter o caminho dos rotores quando eles passam pelo refletor
def read_key(d: dict, val, key=True):
    dict_values = list(d.values())
    dict_keys = list(d.keys())

    if key:
        if val in dict_values:
            return dict_keys[dict_values.index(val)]
    else:
        return d[val]

    return None


# Classe que codifica e aceita as configurações do usuário
class Enigma:

    def __init__(self, input_text: str = "", rotor_pos: str = "00:00:00", rotor_config: tuple[str, str, str] = None,
                 plugboard: dict = None, reflector_config: str = "B", logger=logging.getLogger("enigma.logger")):

        self.logger: logging.Logger = logger

        self.logger.setLevel(logging.root.level)
        handler = logging.StreamHandler()
        handler.setFormatter(LogFormatter())
        self.logger.addHandler(handler)

        self.logger.debug(f"[CALL] Objeto Enigma Criado: {self}")

        self._txt: str = ""
        self._rotor_pos: str = ""
        self._plugboard: dict = {}
        self._rotor_pos: str = ""
        self._rotor_config: tuple = ()
        self._reflector_option: str = ""

        self.txt = input_text
        self.rotor_pos = rotor_pos
        self.plugboard = plugboard if plugboard is not None else {}
        self.rotor_config: tuple = rotor_config
        self.reflector_option: str = reflector_config

        self.ring1: int = 0
        self.ring2: int = 0
        self.ring3: int = 0
        self.rotor1 = None
        self.rotor2 = None
        self.rotor3 = None
        self.reflector = None

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
        return f"{self.ring3:02d}:{self.ring2:02d}:{self.ring1:02d}"

    @rotor_pos.setter
    def rotor_pos(self, value):
        # O formato da posição do Rotor é bem específico:
        # Exitem 3 rotores ativos e eles têm posições de 0 à 25
        # Caso o usuário queira alterar o valor da posição, ele deve fazer no formato correto (Digito:Digito:Digito).
        # Termina o programa se não tiverem 3 grupos de digitos ou se eles não forem digitos

        self._rotor_pos = "0:0:0" if not self._rotor_pos else self._rotor_pos

        search = re.findall("\d{1,2}:\d{1,2}:\d{1,2}", self._rotor_pos)
        if not search:
            self.logger.error("Posição do Rotor inválida. O padrão desta opção deve ser: Número:Número:Número")

        self._rotor_pos = value
        search = re.findall("\d{1,2}", self._rotor_pos)

        self.logger.debug(f"Regex do rotor_pos: {search}")
        self.ring1 = int(search[2])
        self.ring2 = int(search[1])
        self.ring3 = int(search[0])
        self.logger.debug(f"Anéis dos rotores setados: {self.ring1}:{self.ring2}:{self.ring3}")

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
            err_comp_dict = d.copy()

            for key in self._plugboard:
                if key in err_comp_dict.values():
                    value = self._plugboard[key]
                    err_keys.append(key)
                    err_comp_dict.pop(key)
                    self.logger.error(f"Existem plugs repetidos conectados ao plug board. Descartando plug {key}:{value}")

            for key in err_keys:
                self._plugboard.pop(key)

            self.logger.info(f"Configuração atual: {self._plugboard}")

    @property
    def rotor_config(self):
        return self._rotor_config

    @rotor_config.setter
    def rotor_config(self, value):
        self.logger.debug(f"[CALL] rotor_config setter: args={value}")
        tmp_list = []
        if isinstance(value, tuple) and value:
            if len(value) < 3:
                self.logger.debug(f"Poucos inputs. Input do rotor_config={value}")
                self.logger.error("Configurações de rotor insuficientes. São necessários pelo menos 3 rotores.")
            else:
                for inp in value:
                    try:
                        val = int(inp)
                        if val > 5 or val < 1:
                            self.logger.debug(f"Cast com sucesso, mas input fora do limite. {val=}")
                            self.logger.error("Número do rotor não existe. Escolha um número de 1 à 5.")
                        tmp_list.append(val)

                    except ValueError:
                        self.logger.debug(f"Erro no cast para int do input do rotor_config. {inp=}, {type(inp)=}")
                        self.logger.error("Configuração dos rotores não é um número. Escolha um número de 1 à 5.")
                self._rotor_config = tuple(tmp_list)

        elif self.rotor_config is None or not self.rotor_config:
            self.logger.debug(f"{self._rotor_config=}. Usando default ('1', '2', '3')")
            self._rotor_config = ("1", "2", "3")

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

    # Essa função enforça os limites dos rotores e implementa um função do design chamada de Turnover
    def increment_higher_ring(self):
        if self.ring1 == 17:
            self.ring2 += 1
        elif self.ring1 >= 26:
            self.ring1 = 0

        if self.ring2 == 5:
            self.ring3 += 1
        elif self.ring2 >= 26:
            self.ring2 = 0

        if self.ring3 >= 26:
            self.ring3 = 0

    def instance_in_plugboard(self, plug: str):
        if plug in self._plugboard:
            return self._plugboard[plug]
        elif plug in self._plugboard.values():
            return read_key(self._plugboard, plug)
        return plug

    # Função que de fato encripta - e decripta - o texto de input.
    # Por conta da arquitetura do programa, implementar outras variações dos rotores ou dos refletores é
    # bem simples e pode ser feito só colocando as variáveis no script "hardware_tables.py"
    def encrypt(self) -> str:
        global ROT_INTER_IN1, ROT_INTER_12, ROT_INTER_23, ROT_INTER_3R
        default_rotors_and_interfaces()
        tmp = ""
        result = ""

        rotors_options = (ROTOR_1, ROTOR_2, ROTOR_3, ROTOR_4, ROTOR_5)
        reflector_options = (REFLECTOR_B, REFLECTOR_C)

        self.rotor1 = rotors_options[int(self.rotor_config[0]) - 1]
        self.rotor2 = rotors_options[int(self.rotor_config[1]) - 1]
        self.rotor3 = rotors_options[int(self.rotor_config[2]) - 1]

        self.logger.debug(f"Rotores selecionados: {self.rotor1['A']=}, {self.rotor2['A']=}, {self.rotor3['A']=}")

        if self.reflector_option == "B":
            self.reflector = reflector_options[0]
        else:
            self.reflector = reflector_options[1]

        for letter in self.txt:
            if letter == " ":
                result += letter
                continue

            letter = self.instance_in_plugboard(letter)

            self.ring1 += 1
            self.increment_higher_ring()

            # Uma explicação breve da arquitetura e da máquina:
            # - Existem 2 tipos de dicionários no programa, ambos no script hardware_tables.py, os dicionários
            #   de cifragem  (que têm os nomes de ROTOR_1 à ROTOR_5) e os dicionários de interface
            #  (ROTOR_INTER_IN1, ROTOR_INTER_12, ...)
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
            # ROTOR 1 GIROU   B C D E F G H I J K ... Z A  } Interface entre 1 e 2 -> ROT_INTER_12
            # ROTOR 2 NORMAL  A B C D E F G H I J ... Y Z  }

            ROT_INTER_IN1 = shift_values_right(ROT_INTER_IN1, -self.ring1)
            ROT_INTER_12 = shift_values_right(ROT_INTER_12, self.ring1)
            ROT_INTER_12 = shift_keys_right(ROT_INTER_12, self.ring2)
            ROT_INTER_23 = shift_values_right(ROT_INTER_23, self.ring2)
            ROT_INTER_23 = shift_keys_right(ROT_INTER_23, self.ring3)
            ROT_INTER_3R = shift_values_right(ROT_INTER_3R, self.ring3)

            tmp = ROT_INTER_IN1[letter]
            tmp = self.rotor1[tmp]
            tmp = ROT_INTER_12[tmp]
            tmp = self.rotor2[tmp]
            tmp = ROT_INTER_23[tmp]
            tmp = self.rotor3[tmp]
            tmp = ROT_INTER_3R[tmp]

            if tmp not in self.reflector.keys():
                tmp = read_key(self.reflector, tmp)
            else:
                tmp = self.reflector[tmp]

            tmp = read_key(ROT_INTER_3R, tmp)
            tmp = read_key(self.rotor3, tmp)
            tmp = read_key(ROT_INTER_23, tmp)
            tmp = read_key(self.rotor2, tmp)
            tmp = read_key(ROT_INTER_12, tmp)
            tmp = read_key(self.rotor1, tmp)
            tmp = read_key(ROT_INTER_IN1, tmp)

            tmp = self.instance_in_plugboard(tmp)

            result += tmp
            default_rotors_and_interfaces()

        return result

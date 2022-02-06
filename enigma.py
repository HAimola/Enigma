from hardware_tables import ROTOR_1, ROTOR_2, ROTOR_3, ROTOR_4, ROTOR_5, REFLECTOR_B, REFLECTOR_C
from hardware_tables import _ROT_INTER_IN1, _ROT_INTER_12, _ROT_INTER_23, _ROT_INTER_3R

import re


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


def check_dict_repeating_values(d: dict, except_msg):
    for key in d:
        if key in d.values():
            raise ValueError(except_msg)


# Classe que codifica e aceita as configurações do usuário
class Enigma:

    def __init__(self, input_text: str = "", rotor_pos: str = "00:00:00", rotor_config: tuple[str, str, str] = None,
                 plugboard: tuple or dict = (), reflector_config: str = "B"):

        self.txt = input_text.upper()
        self._rotor_pos = rotor_pos
        self.rotor_config = rotor_config
        self._plugboard = plugboard
        self.reflector_option = reflector_config
        self.sanitize_flag = True

        self.sanitize_flag = None
        self.ring1: int = 0
        self.ring2: int = 0
        self.ring3: int = 0

        self.rotor1 = None
        self.rotor2 = None
        self.rotor3 = None
        self.reflector = None
        self.sanitize_flag = True

    @property
    def rotor_pos(self):
        return f"{self.ring3:02d}:{self.ring2:02d}:{self.ring1:02d}"

    @rotor_pos.setter
    def rotor_pos(self, value):
        self._rotor_pos = value
        search = re.findall("\d{1,2}", self._rotor_pos)

        self.ring1 = int(search[2])
        self.ring2 = int(search[1])
        self.ring3 = int(search[0])

    @property
    def plugboard(self):
        return self._plugboard

    @plugboard.setter
    def plugboard(self, value):


        comp = re.compile("[+_`!@#$%^&*=().,';~/\d-]")

        if isinstance(value, tuple):

            for plug in value:
                search = re.findall(comp, plug)
                if search:
                    raise ValueError(f"String do plugboard {plug} com caractér especial ou números! Use apenas letras.")
                if len(plug) != 2:
                    raise ValueError(f"Configuração de plugboard {plug} não tem duas conexões!")

            self._plugboard = {plug[0]: plug[1] for plug in value if plug[0] != plug[1]}
        elif isinstance(value, dict):
            self._plugboard = value

        check_dict_repeating_values(self.plugboard, except_msg="Existem valores repetidos no plugboard. Uma "
                                                               "letra pode se conectar à apenas uma outra letra!")

    def __setattr__(self, key, value):
        if key == "txt":
            value = value.upper()

        super().__setattr__(key, value)

        if "sanitize_flag" in self.__dict__:
            if self.sanitize_flag is not None:
                self.sanitize_inputs()

    # Função que sanitiza todos os inputs
    def sanitize_inputs(self):

        if not isinstance(self.txt, str):
            raise ValueError(f"Dados passados - {self.txt} - não são em forma de texto! ")

        # A máquina Enigma original só encriptava letras
        # Termina o programa caso tenha algum caractér especial ou número.
        comp = re.compile("[+_`!@#$%^&*=().,';~/\d-]")
        search = re.findall(comp, self.txt)

        if search:
            raise ValueError("String com caractéres especiais ou números! Use apenas letras.")

        # O formato da posição do Rotor é bem específico:
        # Exitem 3 rotores ativos e eles têm posições de 0 à 25
        # Caso o usuário queira alterar o valor da posição, ele deve fazer no formato correto (Digito:Digito:Digito).
        # Termina o programa se não tiverem 3 grupos de digitos ou se eles não forem digitos
        comp = re.compile("\d{1,2}:\d{1,2}:\d{1,2}")
        search = re.findall(comp, self._rotor_pos)

        if not search:
            raise ValueError("Posição do Rotor inválida. O padrão desta opção deve ser: Número:Número:Número")

        if self.rotor_config:
            if len(self.rotor_config) < 3:
                raise ValueError("Configurações de rotor insuficientes. São necessários pelo menos 3 rotores.")

            for i in self.rotor_config:
                try:
                    val = int(i)
                except ValueError:
                    raise ValueError("Configuração dos rotores não é um número. Escolha um número de 1 à 5.")

                if val > 4 or val < 1:
                    raise ValueError("Número do rotor não existe. Escolha um número de 1 à 5.")
        else:
            self.rotor_config = ("1", "2", "3")

        # Só existem 2 modelos convencionais de refletor: B e C (existem as variações Dünn, mas eu não implementei)
        if self.reflector_option not in ("C", "B"):
            raise ValueError("O modelo de refletor não existe. Escolha o refletor B ou C.")

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

    def instance_in_plugboard(self, input: str):
        if input in self._plugboard:
            return self._plugboard[input]
        elif input in self._plugboard.values():
            return read_key(self._plugboard, input)
        return input

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

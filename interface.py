from rotor import Rotor, InputRotor, Reflector


class Interface(dict):
    def __init__(self, con1: Rotor or InputRotor, con2: Rotor or Reflector, interface_input = None, *args, **kwargs):
        self.connection: list = [con1, con2]
        self.r1: Rotor or InputRotor = con1
        self.r2: Rotor or Reflector = con2
        self.next_inter: Interface = interface_input

        init_dict = {"A": "A",
                     "B": "B",
                     "C": "C",
                     "D": "D",
                     "E": "E",
                     "F": "F",
                     "G": "G",
                     "H": "H",
                     "I": "I",
                     "J": "J",
                     "K": "K",
                     "L": "L",
                     "M": "M",
                     "N": "N",
                     "O": "O",
                     "P": "P",
                     "Q": "Q",
                     "R": "R",
                     "S": "S",
                     "T": "T",
                     "U": "U",
                     "V": "V",
                     "W": "W",
                     "X": "X",
                     "Y": "Y",
                     "Z": "Z",
                     } if not args else args[0]

        super().__init__(init_dict, **kwargs)

    # Avança as chaves ou os valores de um dicionário pra
    # esquerda ou para direita
    def relative_shift(self, offset: int, key=False):
        list_d = []
        offset = offset % len(self)

        if key:
            list_d = list(self.keys())
        else:
            list_d = list(self.values())

        # Nenhum
        if offset == 0:
            return
        # Esquerda
        elif offset < 0:
            offset = abs(offset)
            list_d = list_d[offset:] + list_d[:offset]
        # Direita
        else:
            list_d = list_d[-offset:] + list_d[:-offset]

        dup = self.copy()
        self.clear()
        if key:
            self.__init__(self.connection[0], self.connection[1], self.next_inter,
                          {list_d[shift_idx]: value for shift_idx, value in enumerate(dup.values())})
        else:
            self.__init__(self.connection[0], self.connection[1], self.next_inter,
                          {key: list_d[shift_idx] for shift_idx, key in enumerate(dup.keys())})

        del dup

    # Gira o rotor fazendo o shift das duas interfaces
    # que representam um rotor
    def shift_rotor(self):
        if not isinstance(self.r2, Reflector):
            self.r2.shift += 1
            self.next_inter.relative_shift(-1, key=True)
            self.relative_shift(-1)
            self.turnover()

    # Gira o rotor para uma posição absoluta. 0 é a posição
    # inicial e 26 é a última posição
    def absolute_rotor_shift(self, position: int):
        if not isinstance(self.r2, Reflector):
            offset = self.r2.shift - position
            self.relative_shift(offset)
            self.next_inter.relative_shift(offset, key=True)
            self.r2.shift = position
            self.next_inter.r1.shift = position

    # Checa se o rotor já atingiu o ponto de turnove
    # Se sim, avança o próximo rotor.
    def turnover(self):
        if isinstance(self.r1, InputRotor):
            if self.r2.shift == self.r2.turnover:
                self.next_inter.shift_rotor()

        elif not isinstance(self.r2, Reflector):
            if self.r2.shift == self.r2.turnover:
                self.shift_rotor()
                self.next_inter.shift_rotor()

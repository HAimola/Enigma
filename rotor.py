class Rotor(dict):
    def __init__(self, number: int, turnover: int, *args, **kwargs):
        self.number = number
        self._shift: int = 0
        self.turnover: int = turnover
        super(Rotor, self).__init__(*args, **kwargs)

    @property
    def shift(self):
        return self._shift

    @shift.setter
    def shift(self, value):
        self._shift = value
        if self._shift >= 26:
            self._shift = 0

    def __setitem__(self, key, value):
        raise KeyError("Não é possível alterar o dicionário do rotor.")


# Simplesmente espelha qualquer leitura de item
# Só serve pra representar o barramento de entrada
# na hora de criar a interface com o input
class InputRotor(dict):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super().__init__({})

    def __getitem__(self, item):
        return item


class Reflector(dict):
    def __init__(self, *args):
        if isinstance(args[0], Reflector):
            self.name = args[0].name
            super().__init__(args[0])
        else:
            self.name: str = args[0]
            super().__init__(*args[1::])

    def __re_init__(self, *args):
        self.__init__(*args)

    def __getitem__(self, key):
        if key in self.keys():
            return super().__getitem__(key)
        else:
            val_list = list(self.values())
            key_list = list(self.keys())

            return key_list[val_list.index(key)]

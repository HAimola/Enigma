# Parte de interface Grafica
from enigma import Enigma


def print_ui_header():
    print(''' _____ _   _ ___ ____ __  __    _
| ____| \ | |_ _/ ___|  \/  |  / \ \r
|  _| |  \| || | |  _| |\/| | / _ \ \r
| |___| |\  || | |_| | |  | |/ ___ \ \r
|_____|_| \_|___\____|_|  |_/_/   \_\ ''')

    print("\nFeito pelo grupo 7.\n\n")

    com_str = "COMANDOS: /cod {texto}               - Codifica um texto usando as configurações atuais.\n" \
              "          /exit ou Ctrl+C            - Termina o programa.\n" \
              "          /rot {NUM:NUM:NUM}         - Ajusta os rotores para as posições dadas, os números\n" \
              "                                         devem ser menores ou iguais a 26.\n" \
              "          /plug {LETRA:LETRA, ...}   - Conecta duas letras no plug-board. Se alguma das letras\n" \
              "                                         já estiver conectada, a conexão mais nova tem prioridade."
    print(com_str)


def main():
    print_ui_header()
    a = Enigma("A", plugboard={"A":"B", "W":"C"})
    print(a.encrypt())


    # while True:
    #     try:
    #         pass
    #     except KeyboardInterrupt:
    #         print(f"\n\n{'-'*90}")
    #         print("Obrigado por ter usado!")
    #         exit()


if __name__ == "__main__":
    main()

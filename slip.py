# 2022 - 1 - UFSCar - Departamento de Computação..
# Trabalho de Redes 2 - Camada de transporte TCP.
# Alunos:.
# Bruno Leandro Pereira - RA: 791067.
# Bruno Luis Rodrigues Medri - RA: 790004.
# Thiago Roberto Albino - RA: 790034.
# Vitor de Almeida Recoaro - RA: 790035.


class CamadaEnlace:
    ignore_checksum = False

    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        self.callback = None
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self._callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def _callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:
    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.resto = b""

    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        datagramaParaEnviar = b""

        for byte in datagrama:
            if byte == 0xC0:
                datagramaParaEnviar += b"\xdb" + b"\xdc"

            elif byte == 0xDB:
                datagramaParaEnviar += b"\xdb" + b"\xdd"

            else:
                datagramaParaEnviar += bytes([byte])

        datagramaParaEnviar = b"\xc0" + datagramaParaEnviar + b"\xc0"
        self.linha_serial.enviar(datagramaParaEnviar)

    def __raw_recv(self, dados):
        # Pega o resto que pode ter sido recebido nos dados anteriores.
        datagrama = self.resto

        for byte in dados:

            if byte == 0xC0 and datagrama != b"":

                try:
                    self.callback(datagrama)
                except:
                    import traceback

                    traceback.print_exc()
                finally:
                    # faça aqui a limpeza necessária para garantir que não vão sobrar
                    # pedaços do datagrama em nenhum buffer mantido por você
                    datagrama = b""
                    self.resto = b""

            elif byte != 0xC0:
                datagrama += bytes([byte])

                if datagrama[-2:] == b"\xdb\xdc":
                    datagrama = datagrama[:-2] + b"\xc0"

                elif datagrama[-2:] == b"\xdb\xdd":
                    datagrama = datagrama[:-2] + b"\xdb"

        self.resto = datagrama

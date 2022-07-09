import face_recognition
import random
import faker
import simpy
import secrets
import json

FOTOS_MOTORISTAS = [
    "faces/bruna1.jpg",
    "faces/tiago1.jpg",

    "faces/jennifer1.jpg",
    "faces/jennifer2.jpg",
    "faces/jennifer3.jpg",

    "faces/lazaro1.jpg",
    "faces/lazaro2.jpg",
    "faces/lazaro3.jpg"
]

ARQUIVO_CONFIGURACAO = "configuracao.json"

TEMPO_ENTRE_MOTORISTA = 1
TEMPO_ENTRE_PERSERGUICAO = 30


def preparar():
    global configuracao

    # carregar arquivos de configuração
    configuracao = None
    with open(ARQUIVO_CONFIGURACAO, "r") as arquivo_configuracao:
        configuracao = json.load(arquivo_configuracao)
        if configuracao:
            print("configuracao carregada. versão da simulação:",
                  configuracao["versao"])

    global motoristas_reconhecido
    motoristas_reconhecido = {}

    global motoristas_perigoso
    motoristas_perigoso = {}

    global gerador_dados_falsos
    gerador_dados_falsos = faker.Faker(locale="pt_BR")


def simular_enquadro():
    motorista = {
        "foto": random.choice(FOTOS_MOTORISTAS),
        "ficha": None
    }

    return motorista


def identificar_status(motorista):
    global configuracao
    global gerador_dados_falsos

    print("Analisando ficha do motorista...")
    foto_motorista = face_recognition.load_image_file(motorista["foto"])
    encoding_foto_motorista = face_recognition.face_encodings(foto_motorista)[0]

    reconhecido = False
    for ficha in configuracao["fichas"]:
        fotos_banco = ficha["fotos"]
        total_reconhecimentos = 0

        for foto in fotos_banco:
            foto_banco = face_recognition.load_image_file(foto)
            encoding_foto_banco = face_recognition.face_encodings(foto_banco)[0] 

            foto_reconhecida = face_recognition.compare_faces(
                [encoding_foto_motorista], encoding_foto_banco)[0]
            if foto_reconhecida:
                total_reconhecimentos += 1

        if total_reconhecimentos/len(fotos_banco) > 0.6:
            reconhecido = True

            motorista["ficha"] = {}
            motorista["ficha"]["nome"] = gerador_dados_falsos.name()
            motorista["ficha"]["idade"] = random.randint(18, 80)
            motorista["ficha"]["status"] = random.choice(
                ["NOVO", "RECORRENTE", "RENOVADO", "PERIGOSO", "EXEMPLO"])
            motorista["ficha"]["endereco"] = gerador_dados_falsos.address()
            motorista["ficha"]["historico"] = []
            motorista["ficha"]["qtd_multas"] = random.randint(1, 3)
            motorista["ficha"]["veiculo"] = random.choice(["Motocicleta", "Caminhonete", "Caminhão", "Carro"])
            

    return reconhecido, motorista


def imprimir_ficha(motorista_reconhecido):
    print("Nome:", motorista_reconhecido["ficha"]["nome"])
    print("Idade:", motorista_reconhecido["ficha"]["idade"])
    print("Endereço:", motorista_reconhecido["ficha"]["endereco"])
    print("Status:", motorista_reconhecido["ficha"]["status"])
    print("Histórico de multas:",
          motorista_reconhecido["ficha"]["historico"])
    print("Veículo:", motorista_reconhecido["ficha"]["veiculo"])

def reconhecer_motorista(env):
    global motoristas_reconhecido

    while True:
        print("Reconhecendo um motorista...", env.now)

        motorista = simular_enquadro()
        reconhecido, motorista_reconhecido = identificar_status(motorista)
        if reconhecido:
            id_enquadro = secrets.token_hex(nbytes=16).upper()
            motoristas_reconhecido[id_enquadro] = motorista_reconhecido

            print(
                "Um motorista foi reconhecido em nossa base de dados, imprimindo sua ficha...")
        else:
            print("O motorista não se encontra cadastrado em nossa base de dados. APREENDER VEÍCULO e seguir protocolo")
            print("")

        yield env.timeout(TEMPO_ENTRE_MOTORISTA)


def avaliar_motorista(env):
    global motoristas_reconhecido
    global motoristas_perigoso

    while True:
        if len(motoristas_reconhecido):
            print("verificando dados do motorista em ciclo/tempo", env.now)

            for id_enquadro, motorista_reconhecido in list(motoristas_reconhecido.items()):
                    if(motorista_reconhecido["ficha"]["status"] == "NOVO"):
                        print("Primeiro enquadro do motorista. Analisar situação")
                        gerar_multa(id_enquadro, motorista_reconhecido)
                        print("")
                        timeout = 1

                    elif(motorista_reconhecido["ficha"]["status"] == "RECORRENTE"):
                        print("Consultar dados do motorista e historico de multas")
                        gerar_multa(id_enquadro, motorista_reconhecido)
                        print("")
                        timeout = 1

                    elif(motorista_reconhecido["ficha"]["status"] == "RENOVADO"):
                        print("O motorista apresentou bom comportamento nos ultimos tempos")
                        imprimir_ficha(motorista_reconhecido)
                        print("")
                        timeout = 1

                    elif(motorista_reconhecido["ficha"]["status"] == "PERIGOSO"):
                        print("")
                        motoristas_perigoso[id_enquadro] = motorista_reconhecido
                        timeout = 1 

                    elif(motorista_reconhecido["ficha"]["status"] == "EXEMPLO"):
                        print("Motorista Exemplar!! ")
                        imprimir_ficha(motorista_reconhecido)
                        print("")
                        timeout = 1
                        

            timeout = 1

            yield env.timeout(timeout)
        else:
            yield env.timeout(1)

def gerar_multa(id_enquadro, motorista_reconhecido):
    global valor_multa
    valor_multa = random.randint(100, 1000)
    
    print("Multa Gerada do enquadro:", id_enquadro, " .Segue os dados abaixo")
    print("Nome:", motorista_reconhecido["ficha"]["nome"])
    print("Idade:", motorista_reconhecido["ficha"]["idade"])
    print("Status:", motorista_reconhecido["ficha"]["status"])
    print("Veículo:", motorista_reconhecido["ficha"]["veiculo"])
    print("Valor da multa de R$", valor_multa, ",00 reais")

def codigo_perseguicao(id_enquadro, motorista_perigoso):
    print("O suspeito é: ", motorista_perigoso["ficha"]["nome"])
    print("Dirigindo um ", motorista_perigoso["ficha"]["veiculo"])
    print("Com código de rastreio: ", id_enquadro)

def prender_motorista(env):
    global motoristas_perigoso

    while True:
        if len(motoristas_perigoso):
            print("Ligando para as autoridades policiais mais próximas para conter motorista", env.now)

            for id_enquadro, motorista_perigoso in list (motoristas_perigoso.items()):
                print("Motorista Perigoso!! Iniciando perseguição...")
                codigo_perseguicao(id_enquadro, motorista_perigoso)
                print("")

            yield env.timeout(TEMPO_ENTRE_PERSERGUICAO)
        else:
            yield env.timeout(1)



if __name__ == "__main__":
    preparar()

    env = simpy.Environment()

    # tenta reconhecer o motorista do veiculo 
    env.process(reconhecer_motorista(env))

    # relação do motorista na situação atual com o seu status
    env.process(avaliar_motorista(env))

    # chamar policia
    env.process(prender_motorista(env))
    

    env.run(until=10000)

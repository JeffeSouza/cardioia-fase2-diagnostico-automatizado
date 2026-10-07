"""Gera data/frases_risco.csv (frase, situacao, origem) para a Parte 2.

A base combina duas origens:
- "manual": frases escritas por mim, simulando relatos de triagem;
- "fase1": frases montadas a partir do dataset simulado da Fase 1
  (data/fase1/pacientes_cardiacos_simulados.csv), usando o rótulo
  `rotulo_risco_cardiovascular_simulado` como situação de risco.

Uso:
    python tools/gerar_base_risco.py
"""

import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_FASE1 = RAIZ / "data" / "fase1" / "pacientes_cardiacos_simulados.csv"
ARQ_SAIDA = RAIZ / "data" / "frases_risco.csv"
SEMENTE = 20261006
QTD_FASE1_BAIXO = 48  # todos os casos de alto risco da Fase 1 entram; baixo risco é amostrado

ALTO_RISCO = [
    "sinto dor no peito e falta de ar",
    "estou com um aperto forte no peito que vai para o braço esquerdo",
    "dor no peito muito forte há trinta minutos com suor frio",
    "sinto uma pressão no peito que não passa nem em repouso",
    "a dor no peito começou de repente e estou enjoado e suando",
    "dor no peito que irradia para a mandíbula e para as costas",
    "tive dor no peito e desmaiei por alguns segundos",
    "estou com falta de ar intensa e os lábios ficaram roxos",
    "não consigo respirar direito nem deitado nem sentado",
    "acordo de madrugada sem ar e preciso sentar para respirar",
    "meu coração está disparado há horas e sinto tontura forte",
    "desmaiei enquanto subia a escada e senti o peito apertar",
    "meu coração bate muito rápido e irregular e estou quase desmaiando",
    "sinto dor no peito ao respirar e tossi sangue",
    "falta de ar súbita depois de uma viagem longa de ônibus",
    "minha pressão está 200 por 120 e estou com dor de cabeça muito forte",
    "estou com a vista turva e a pressão muito alta",
    "sinto queimação forte no peito que piora com esforço e não melhora com remédio",
    "dor no peito e o braço esquerdo ficou dormente",
    "estou suando frio com enjoo e um peso enorme no peito",
    "minhas pernas incharam muito e agora fico sem ar ao falar",
    "ganhei três quilos em dois dias e não consigo deitar sem perder o fôlego",
    "sinto o coração falhando e já desmaiei duas vezes hoje",
    "senti uma dor rasgando no peito que foi para as costas",
    "estou com aperto no peito e o lado esquerdo do rosto ficou dormente",
    "a dor no peito acordou-me durante a noite e não passa",
    "minha boca entortou e o braço ficou fraco de repente",
    "tenho falta de ar e dor no peito mesmo parado",
    "faço tratamento para o coração e a dor no peito voltou mais forte",
    "fiquei sem ar ao caminhar poucos metros e os pés estão roxos",
    "sinto palpitações fortes com dor no peito e muita tontura",
    "minha frequência cardíaca está acima de 150 e não baixa",
    "o oxímetro mostra saturação de 85 e estou cansado demais para levantar",
    "estou com febre alta, calafrios e o médico já disse que tenho sopro no coração",
    "minha mãe de 78 anos está confusa, pálida e com dor no peito",
    "meu pai de 70 anos sente aperto no peito e está muito sudoreico",
    "tenho diabetes e senti um cansaço extremo com dor no estômago e suor frio",
    "sinto dor no peito em aperto desde o almoço e ela está piorando",
    "estou com dor no peito e meu marcapasso parece não estar funcionando",
    "a falta de ar piora a cada hora e tusso uma espuma rosada",
    "acordei com a perna inchada e agora sinto dor no peito e falta de ar",
    "senti o peito apertar no jogo de futebol e caí no chão",
    "tenho pressão alta e hoje senti uma dor de cabeça explosiva com vômito",
    "dor intensa no peito que melhora apenas um pouco quando fico sentado",
    "sinto o peito pesado, enjoo e uma sensação de morte iminente",
    "o coração disparou durante o trabalho e fiquei com a visão escura",
    "sou cardiopata e hoje estou com falta de ar mesmo em repouso",
    "senti uma dor esmagadora no peito ao carregar peso",
    "estou tonta, com batimentos muito lentos e quase desmaiei no banho",
    "minha avó tem insuficiência cardíaca e hoje está muito sem ar",
    "o peito dói muito, a pressão caiu e estou muito pálido",
    "tive um apagão enquanto dirigia e o coração estava acelerado",
    "sinto falta de ar e o peito chiando com dor forte no lado esquerdo",
    "dor no peito forte há mais de vinte minutos sem melhora",
    "tomei o remédio sublingual e a dor no peito continua",
    "tive infarto ano passado e hoje voltei a sentir aperto no peito",
    "estou com tosse com sangue e dor ao respirar desde a cirurgia",
    "não sinto as pernas direito e o peito está apertado",
    "meu filho desmaiou no treino e reclamou de dor no peito antes",
    "batimento acelerado, suor frio e dor no peito ao mesmo tempo",
]

BAIXO_RISCO = [
    "tive um leve incômodo nas costas",
    "estou com um pouco de dor de cabeça depois de ficar no computador",
    "sinto cansaço no fim do dia depois do trabalho",
    "meu nariz está entupido e espirro bastante",
    "tenho dor nas pernas depois da corrida de domingo",
    "dor muscular no ombro depois da academia",
    "sinto um leve enjoo quando ando de carro",
    "estou com dor de garganta há dois dias",
    "meu coração acelera quando tomo muito café, mas passa rápido",
    "fico ofegante ao subir quatro andares de escada correndo",
    "tive uma tontura leve ao levantar rápido da cama",
    "sinto dor no peito quando aperto o local depois do treino de supino",
    "tenho azia depois de comer feijoada",
    "estou com tosse seca e coriza",
    "senti uma pontada rápida no peito que passou em segundos",
    "às vezes sinto palpitação quando estou nervoso antes de provas",
    "minha pressão estava 12 por 8 na farmácia",
    "estou com dificuldade para dormir por causa do barulho",
    "sinto dor nas costas por ficar muito tempo sentado",
    "tenho um leve inchaço nos pés depois de um dia muito quente",
    "sinto cansaço depois de dormir pouco",
    "tive uma câimbra na panturrilha durante a noite",
    "estou com dor de cabeça leve por causa da gripe",
    "sinto o coração bater forte depois de fazer exercício, e logo normaliza",
    "dor no joelho quando subo escadas",
    "estou um pouco ansioso com o trabalho",
    "sinto dor no peito quando tusso por causa do resfriado",
    "fiquei com falta de ar leve depois de nadar bastante, mas passou",
    "estou com dor nos músculos do peito depois de carregar a mudança",
    "minha garganta arranha e tenho febre baixa",
    "sinto uma leve tontura quando fico muito tempo sem comer",
    "estou com dor de dente",
    "tenho a pele seca e coceira",
    "faço caminhada todos os dias e me sinto bem",
    "vim apenas renovar a receita do remédio de pressão, estou bem",
    "não tenho dor no peito nem falta de ar, só um resfriado",
    "não sinto dor no peito, apenas um pouco de cansaço",
    "sinto queimação no estômago depois de comer pimenta",
    "dor na lombar depois de jardinagem",
    "estou com o olho irritado e lacrimejando",
    "sinto formigamento na mão quando durmo em cima do braço",
    "meus pés ficam frios no inverno",
    "senti o coração acelerar num susto, mas logo passou",
    "tenho um pouco de dor de barriga depois do almoço",
    "estou com alergia e espirros pela manhã",
    "senti uma fisgada nas costelas ao virar o corpo",
    "estou com dor no pescoço por dormir de mau jeito",
    "tenho rinite e o nariz escorre",
    "cansaço leve depois de uma semana de muitas provas",
    "dor de cabeça que melhora com analgésico e descanso",
    "minha frequência cardíaca no relógio deu 72 em repouso",
    "estou com uma afta que incomoda para comer",
    "tive um mal-estar leve depois de tomar sol demais",
    "sinto as pernas pesadas depois de um dia inteiro em pé, mas melhora ao elevá-las",
    "minha mãe de 70 anos faz exames de rotina e está sem sintomas",
    "meu pai tem 65 anos, faz academia e não sente nada",
    "a dor no peito foi só uma batida no futebol e não dói ao respirar",
    "estou com prisão de ventre há dois dias",
    "sinto uma leve dor no braço depois da vacina",
    "fiquei com o coração acelerado depois de tomar energético, já normalizou",
]

FAIXAS_IDADE = [(45, "jovem"), (60, "de meia-idade"), (200, "idoso")]
DOR_TORACICA = {
    "pressao": "dor no peito em pressão",
    "aperto": "aperto no peito",
    "queimacao": "queimação no peito",
}
ECG = {
    "alteracao_st_t": "alteração ST-T no ECG",
    "taquicardia_sinusal": "taquicardia no ECG",
    "arritmia_suspeita": "suspeita de arritmia no ECG",
}
MODELOS = [
    "{pessoa} relata {sintomas}{fatores}.",
    "{pessoa} procurou atendimento com {sintomas}{fatores}.",
    "Paciente {pessoa_min} refere {sintomas}{fatores}.",
]


def descrever_pessoa(sexo, idade):
    faixa = next(nome for limite, nome in FAIXAS_IDADE if idade < limite)
    if sexo == "F":
        return "Mulher " + faixa.replace("idoso", "idosa")
    return "Homem " + faixa


def montar_frase_fase1(linha, rng):
    sintomas = []
    if linha["sintoma_dor_toracica"] in DOR_TORACICA:
        sintomas.append(DOR_TORACICA[linha["sintoma_dor_toracica"]])
    if linha["sintoma_falta_ar"] == "1":
        sintomas.append("falta de ar")
    if linha["sintoma_palpitacoes"] == "1":
        sintomas.append("palpitações")
    if linha["sintoma_fadiga"] == "1":
        sintomas.append("cansaço")
    texto_sintomas = ", ".join(sintomas) if sintomas else "nenhum sintoma no momento"

    fatores = []
    if int(linha["pressao_sistolica_mmhg"]) >= 140:
        fatores.append(f"pressão {linha['pressao_sistolica_mmhg']} por {linha['pressao_diastolica_mmhg']}")
    if int(linha["colesterol_total_mg_dl"]) >= 240:
        fatores.append("colesterol alto")
    if linha["diabetes_historico"] == "1":
        fatores.append("diabetes")
    if linha["tabagista"] == "1":
        fatores.append("tabagismo")
    if linha["historico_doenca_cardiaca"] == "1":
        fatores.append("histórico de doença cardíaca")
    if linha["historico_familiar_cardiopatia"] == "1":
        fatores.append("cardiopatia na família")
    if linha["atividade_fisica"] == "sedentario":
        fatores.append("sedentarismo")
    if linha["padrao_ecg"] in ECG:
        fatores.append(ECG[linha["padrao_ecg"]])
    texto_fatores = (", com " + ", ".join(fatores)) if fatores else ""

    pessoa = descrever_pessoa(linha["sexo"], int(linha["idade_anos"]))
    modelo = rng.choice(MODELOS)
    return modelo.format(
        pessoa=pessoa, pessoa_min=pessoa.lower(), sintomas=texto_sintomas, fatores=texto_fatores
    )


def gerar_fase1(rng):
    with open(ARQ_FASE1, encoding="utf-8") as arq:
        linhas = list(csv.DictReader(arq))
    altos = [l for l in linhas if l["rotulo_risco_cardiovascular_simulado"] == "1"]
    baixos = rng.sample([l for l in linhas if l["rotulo_risco_cardiovascular_simulado"] == "0"], QTD_FASE1_BAIXO)
    registros = []
    for linha in altos + baixos:
        situacao = "alto risco" if linha["rotulo_risco_cardiovascular_simulado"] == "1" else "baixo risco"
        registros.append((montar_frase_fase1(linha, rng), situacao, "fase1"))
    return registros


def main():
    rng = random.Random(SEMENTE)
    registros = [(f, "alto risco", "manual") for f in ALTO_RISCO]
    registros += [(f, "baixo risco", "manual") for f in BAIXO_RISCO]
    registros += gerar_fase1(rng)
    rng.shuffle(registros)

    with open(ARQ_SAIDA, "w", encoding="utf-8", newline="") as arq:
        escritor = csv.writer(arq)
        escritor.writerow(["frase", "situacao", "origem"])
        escritor.writerows(registros)

    total_alto = sum(1 for _, s, _ in registros if s == "alto risco")
    print(f"{len(registros)} frases salvas em {ARQ_SAIDA.relative_to(RAIZ).as_posix()} "
          f"({total_alto} alto risco / {len(registros) - total_alto} baixo risco)")


if __name__ == "__main__":
    main()

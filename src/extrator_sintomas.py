"""CardioIA Fase 2 - Parte 1: extração de sintomas e sugestão de diagnóstico.

Abordagem simbólica (NLP baseado em regras):
1. normalização: minúsculas, tokenização, remoção de stopwords e estemização RSLP;
2. reconhecimento de sintomas por dicionário (mapa de conhecimento em CSV);
3. regras de negação ("não sinto dor no peito" não conta como sintoma);
4. NER por regex para tempo de início e impacto na rotina;
5. pontuação das doenças, ponderando sintomas específicos acima dos genéricos.

Uso:
    python src/extrator_sintomas.py
"""

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer

RAIZ = Path(__file__).resolve().parent.parent
ARQ_FRASES = RAIZ / "data" / "frases_sintomas.txt"
ARQ_MAPA = RAIZ / "data" / "mapa_conhecimento.csv"
ARQ_SAIDA = RAIZ / "outputs" / "diagnosticos_parte1.csv"
ARQ_ONTOLOGIA = RAIZ / "outputs" / "ontologia_cardioia.ttl"

NEGACOES = {"nao", "nem", "sem", "nunca"}
JANELA_NEGACAO = 3  # quantas palavras antes do sintoma a negação alcança
SALTO_MAXIMO = 2    # palavras extras permitidas entre os termos de uma expressão

NUMERAIS = r"(?:\d+|um|uma|dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|alguns|algumas|poucos|poucas)"
UNIDADES = r"(?:minutos?|horas?|dias?|semanas?|mês|meses|anos?)"
PADROES_TEMPO = [
    rf"\b(?:há|faz)\s+(?:cerca\s+de\s+|mais\s+de\s+|uns\s+|umas\s+)?{NUMERAIS}\s+{UNIDADES}",
    r"\bdesde\s+(?:a\s+|o\s+)?(?:ontem(?:\s+à\s+noite)?|anteontem|hoje|\w+(?:\s+de\s+\w+)?)",
    r"\b(?:hoje(?:\s+de\s+manhã|\s+à\s+noite)?|ontem(?:\s+à\s+noite)?|anteontem|de\s+repente)\b",
]
PADRAO_IMPACTO = (
    r"(?:não\s+consig\w*|não\s+conseg\w*|mal\s+consigo|parei\s+de|tive\s+que\s+parar"
    r"|faltei|me\s+impede|impede|atrapalha)[^,.;]*"
)


def _garantir_recursos_nltk():
    for recurso, caminho in [("rslp", "stemmers/rslp"), ("stopwords", "corpora/stopwords")]:
        try:
            nltk.data.find(caminho)
        except LookupError:
            nltk.download(recurso, quiet=True)


_garantir_recursos_nltk()
STEMMER = RSLPStemmer()
STOPWORDS = {w for w in stopwords.words("portuguese")} - {"não", "nem", "sem", "nunca"}


def remover_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto):
    """Retorna a lista de radicais (stems) relevantes do texto."""
    tokens = re.findall(r"[a-zà-ÿ]+", texto.lower())
    return [remover_acentos(STEMMER.stem(t)) for t in tokens if t not in STOPWORDS]


def dividir_oracoes(frase):
    """Separa a frase em orações para que a negação não 'vaze' para outra parte."""
    return [o for o in re.split(r"[,.;:!?]|\bmas\b", frase.lower()) if o.strip()]


def carregar_mapa(caminho=ARQ_MAPA):
    """Lê o CSV e devolve {expressão: {doenças}} e o radical de cada expressão."""
    expressao_doencas = defaultdict(set)
    with open(caminho, encoding="utf-8") as arq:
        for linha in csv.DictReader(arq):
            doenca = linha["Doença Associada"].strip()
            for coluna in ("Sintoma 1", "Sintoma 2"):
                expressao = linha[coluna].strip().lower()
                if expressao:
                    expressao_doencas[expressao].add(doenca)
    radicais = {exp: normalizar(exp) for exp in expressao_doencas}
    return dict(expressao_doencas), radicais


def carregar_frases(caminho=ARQ_FRASES):
    with open(caminho, encoding="utf-8") as arq:
        return [linha.strip() for linha in arq if linha.strip()]


def _localizar(padrao, tokens):
    """Procura os radicais do padrão em ordem, permitindo até SALTO_MAXIMO palavras entre eles."""
    if not padrao:
        return None
    for inicio, token in enumerate(tokens):
        if token != padrao[0]:
            continue
        pos = inicio
        for termo in padrao[1:]:
            janela = tokens[pos + 1: pos + 2 + SALTO_MAXIMO]
            if termo not in janela:
                break
            pos = pos + 1 + janela.index(termo)
        else:
            return inicio
    return None


def extrair_sintomas(frase, radicais):
    """Devolve (sintomas_afirmados, sintomas_negados) encontrados na frase."""
    afirmados, negados = set(), set()
    for oracao in dividir_oracoes(frase):
        tokens = normalizar(oracao)
        for expressao, padrao in radicais.items():
            inicio = _localizar(padrao, tokens)
            if inicio is None:
                continue
            anteriores = tokens[max(0, inicio - JANELA_NEGACAO): inicio]
            (negados if NEGACOES & set(anteriores) else afirmados).add(expressao)
    return afirmados, negados - afirmados


def _extrair_trechos(padroes, texto):
    """Aplica regex e remove trechos contidos em outros já encontrados."""
    achados = []
    for padrao in padroes:
        achados += [(m.start(), m.end()) for m in re.finditer(padrao, texto)]
    achados.sort(key=lambda s: (s[0], -s[1]))
    resultado, fim_atual = [], -1
    for ini, fim in achados:
        if fim > fim_atual:
            resultado.append(texto[ini:fim].strip())
            fim_atual = fim
    return resultado


def extrair_tempo(frase):
    return _extrair_trechos(PADROES_TEMPO, frase.lower())


def extrair_impacto(frase):
    return _extrair_trechos([PADRAO_IMPACTO], frase.lower())


def pontuar_doencas(sintomas, expressao_doencas):
    """Soma o peso de cada sintoma: 1 / nº de doenças ligadas a ele (ideia semelhante ao IDF)."""
    pontos = defaultdict(float)
    evidencias = defaultdict(list)
    for sintoma in sintomas:
        doencas = expressao_doencas[sintoma]
        for doenca in doencas:
            pontos[doenca] += 1 / len(doencas)
            evidencias[doenca].append(sintoma)
    ranking = sorted(pontos.items(), key=lambda item: item[1], reverse=True)
    return ranking, evidencias


def analisar_frase(frase, expressao_doencas, radicais):
    sintomas, negados = extrair_sintomas(frase, radicais)
    ranking, evidencias = pontuar_doencas(sintomas, expressao_doencas)
    diagnostico = ranking[0][0] if ranking else "Sem sugestão (nenhum sintoma reconhecido)"
    total = sum(p for _, p in ranking) or 1
    return {
        "frase": frase,
        "sintomas": sorted(sintomas),
        "sintomas_negados": sorted(negados),
        "inicio": extrair_tempo(frase),
        "impacto_rotina": extrair_impacto(frase),
        "diagnostico_sugerido": diagnostico,
        "confianca_relativa": round(ranking[0][1] / total, 2) if ranking else 0.0,
        "evidencias": sorted(evidencias.get(diagnostico, [])),
        "alternativas": [f"{d} ({p:.2f})" for d, p in ranking[1:3]],
    }


def analisar_arquivo(caminho_frases=ARQ_FRASES, caminho_mapa=ARQ_MAPA):
    expressao_doencas, radicais = carregar_mapa(caminho_mapa)
    return [analisar_frase(f, expressao_doencas, radicais) for f in carregar_frases(caminho_frases)]


def salvar_resultados(resultados, destino=ARQ_SAIDA):
    destino.parent.mkdir(parents=True, exist_ok=True)
    campos = list(resultados[0].keys())
    with open(destino, "w", encoding="utf-8", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=campos)
        escritor.writeheader()
        for r in resultados:
            escritor.writerow({k: " | ".join(v) if isinstance(v, list) else v for k, v in r.items()})


def exportar_ontologia(caminho_mapa=ARQ_MAPA, destino=ARQ_ONTOLOGIA):
    """Converte o mapa de conhecimento em uma ontologia RDF (Turtle) com rdflib."""
    from rdflib import RDF, RDFS, Graph, Literal, Namespace, OWL

    cardio = Namespace("http://cardioia.example.org/ontologia#")
    g = Graph()
    g.bind("cardio", cardio)
    for classe in ("Sintoma", "Doenca"):
        g.add((cardio[classe], RDF.type, OWL.Class))
    g.add((cardio.indicaDoenca, RDF.type, OWL.ObjectProperty))
    g.add((cardio.indicaDoenca, RDFS.domain, cardio.Sintoma))
    g.add((cardio.indicaDoenca, RDFS.range, cardio.Doenca))

    def uri(texto):
        return cardio[re.sub(r"\W+", "_", remover_acentos(texto.lower())).strip("_")]

    expressao_doencas, _ = carregar_mapa(caminho_mapa)
    for expressao, doencas in expressao_doencas.items():
        g.add((uri(expressao), RDF.type, cardio.Sintoma))
        g.add((uri(expressao), RDFS.label, Literal(expressao, lang="pt")))
        for doenca in doencas:
            g.add((uri(doenca), RDF.type, cardio.Doenca))
            g.add((uri(doenca), RDFS.label, Literal(doenca, lang="pt")))
            g.add((uri(expressao), cardio.indicaDoenca, uri(doenca)))
    destino.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=destino, format="turtle")
    return g


def imprimir_relatorio(resultados):
    for i, r in enumerate(resultados, start=1):
        print(f"\n[{i:02d}] {r['frase']}")
        print(f"     Sintomas identificados : {', '.join(r['sintomas']) or '-'}")
        if r["sintomas_negados"]:
            print(f"     Sintomas negados       : {', '.join(r['sintomas_negados'])}")
        print(f"     Início                 : {', '.join(r['inicio']) or '-'}")
        print(f"     Impacto na rotina      : {', '.join(r['impacto_rotina']) or '-'}")
        print(f"     Diagnóstico sugerido   : {r['diagnostico_sugerido']} "
              f"(confiança relativa {r['confianca_relativa']:.0%})")
        if r["alternativas"]:
            print(f"     Alternativas           : {', '.join(r['alternativas'])}")


if __name__ == "__main__":
    resultados = analisar_arquivo()
    imprimir_relatorio(resultados)
    salvar_resultados(resultados)
    exportar_ontologia()
    print(f"\nResultados salvos em {ARQ_SAIDA.relative_to(RAIZ).as_posix()}")
    print(f"Ontologia salva em {ARQ_ONTOLOGIA.relative_to(RAIZ).as_posix()}")
    print("\nAviso: sugestão educacional de apoio à triagem; não substitui avaliação médica.")

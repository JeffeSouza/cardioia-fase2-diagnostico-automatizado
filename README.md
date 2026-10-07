# CardioIA — Fase 2: Diagnóstico Automatizado (IA no Estetoscópio Digital)

Módulo de NLP do projeto CardioIA. Ele analisa relatos curtos de pacientes, **identifica sintomas**, **sugere diagnósticos** com um mapa de conhecimento e **classifica o nível de risco** (alto ou baixo) com TF-IDF e Machine Learning, com análise de vieses e governança de dados.

> **Aviso:** projeto acadêmico. Frases, rótulos e diagnósticos são **simulados**. Nenhum resultado deve ser usado para diagnóstico, triagem real ou decisão clínica.

## 🎥 Vídeo de demonstração

**Link (YouTube, não listado):** _a definir_

## Sumário

- [Estrutura do repositório](#estrutura-do-repositório)
- [Como executar](#como-executar)
- [Parte 1 — Extração de sintomas e sugestão de diagnóstico](#parte-1--extração-de-sintomas-e-sugestão-de-diagnóstico)
- [Parte 2 — Classificador de risco com TF-IDF](#parte-2--classificador-de-risco-com-tf-idf)
- [Vieses, limitações e governança](#vieses-limitações-e-governança)
- [Relação com o conteúdo da fase](#relação-com-o-conteúdo-da-fase)

## Estrutura do repositório

```text
CardioIA_Fase2/
├── README.md
├── requirements.txt
├── data/
│   ├── frases_sintomas.txt          # Parte 1 – 10 relatos de pacientes
│   ├── mapa_conhecimento.csv        # Parte 1 – Sintoma 1 | Sintoma 2 | Doença Associada
│   ├── frases_risco.csv             # Parte 2 – frase, situacao (alto/baixo risco), origem
│   └── fase1/
│       └── pacientes_cardiacos_simulados.csv   # dataset reaproveitado da Fase 1
├── src/
│   └── extrator_sintomas.py         # Parte 1 – NLP baseado em regras
├── notebooks/
│   ├── 01_extracao_sintomas.ipynb   # Parte 1 – demonstração passo a passo
│   └── 02_classificador_risco.ipynb # Parte 2 – TF-IDF, modelos, avaliação e vieses
├── tools/
│   └── gerar_base_risco.py          # gera data/frases_risco.csv de forma reprodutível
└── outputs/
    ├── diagnosticos_parte1.csv      # resultado da Parte 1
    └── ontologia_cardioia.ttl       # mapa de conhecimento exportado como ontologia RDF
```

## Como executar

Requisitos: Python 3.12 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Parte 1 – roda o extrator nas 10 frases e salva os resultados em outputs/
python src/extrator_sintomas.py

# Parte 2 – (opcional) recria a base rotulada
python tools/gerar_base_risco.py

# Notebooks
jupyter notebook notebooks/
```

Na primeira execução, os recursos `rslp` e `stopwords` do NLTK são baixados automaticamente. Os notebooks já estão salvos com as saídas, então dá para ler os resultados direto no GitHub.

## Parte 1 — Extração de sintomas e sugestão de diagnóstico

### Entregáveis

| Item | Arquivo |
|---|---|
| 10 frases de pacientes | [`data/frases_sintomas.txt`](data/frases_sintomas.txt) |
| Mapa de conhecimento (64 linhas, 13 doenças) | [`data/mapa_conhecimento.csv`](data/mapa_conhecimento.csv) |
| Código Python | [`src/extrator_sintomas.py`](src/extrator_sintomas.py) e [`notebooks/01_extracao_sintomas.ipynb`](notebooks/01_extracao_sintomas.ipynb) |

Cada frase informa **o que o paciente sente**, **quando começou** e **como isso afeta a rotina**. Por exemplo:

> *"Há dois dias estou com uma dor no peito que piora quando faço esforço físico e alivia quando descanso, por isso parei de subir as escadas do trabalho."*

O mapa de conhecimento segue o formato pedido (`Sintoma 1 | Sintoma 2 | Doença Associada`) e associa expressões populares e técnicas a 13 doenças cardiovasculares.

### Como funciona

Abordagem **simbólica (NLP baseado em regras)**:

1. **Normalização:** minúsculas, tokenização, remoção de *stopwords* (mantendo *não, nem, sem, nunca*) e **estemização RSLP** do NLTK. Assim "pernas inchadas" e "perna inchada" casam com a mesma regra.
2. **Reconhecimento por dicionário:** uma expressão do mapa é encontrada quando seus radicais aparecem em ordem na frase, com até 2 palavras entre eles.
3. **Negação:** "não sinto dor no peito" registra o sintoma como **negado**, e ele não conta para o diagnóstico.
4. **NER por regex:** extrai o **início** ("há dois dias", "desde ontem à noite") e o **impacto na rotina** ("parei de…", "não consigo…").
5. **Pontuação:** cada sintoma soma `1 / nº de doenças associadas`. Sintomas específicos (como "tossi com sangue") pesam mais que genéricos (como "falta de ar"), uma ideia parecida com o IDF.
6. **Ontologia:** o mapa também é exportado em RDF/Turtle (`rdflib`) e pode ser consultado com SPARQL.

### Resultado

| # | Principais sintomas identificados | Início | Diagnóstico sugerido |
|---|---|---|---|
| 1 | dor no peito ao esforço, alivia quando descanso | há dois dias | Angina Estável |
| 2 | aperto forte no peito, espalha para o braço esquerdo, suor frio, enjoo | desde ontem à noite | Infarto Agudo do Miocárdio |
| 3 | cansaço constante, pernas inchadas, dormir com travesseiros | há uma semana | Insuficiência Cardíaca |
| 4 | coração dispara, batendo irregular, tontura | há três semanas | Arritmia Cardíaca |
| 5 | dor de cabeça forte, dor na nuca, vista embaçada, pressão muito alta | hoje de manhã | Crise Hipertensiva |
| 6 | piora quando respiro fundo/deito, melhora quando me inclino, depois de uma gripe | há quatro dias | Pericardite |
| 7 | panturrilha inchada, viagem de avião (*dor no peito negada*) | há cinco dias | Trombose Venosa Profunda |
| 8 | desmaiei enquanto corria, falta de ar ao fazer exercício, tontura | ontem / há um mês | Estenose Aórtica |
| 9 | febre que vai e volta, calafrios, suor à noite, tratamento dentário | há duas semanas | Endocardite Infecciosa |
| 10 | falta de ar intensa, dor no peito ao respirar, tossi com sangue | de repente, há duas horas | Embolia Pulmonar |

A saída completa, com sintomas negados, impacto na rotina, confiança relativa e diagnósticos alternativos, está em [`outputs/diagnosticos_parte1.csv`](outputs/diagnosticos_parte1.csv).

## Parte 2 — Classificador de risco com TF-IDF

### Entregáveis

| Item | Arquivo |
|---|---|
| Base rotulada (200 frases) | [`data/frases_risco.csv`](data/frases_risco.csv) |
| Notebook com TF-IDF, classificação e avaliação | [`notebooks/02_classificador_risco.ipynb`](notebooks/02_classificador_risco.ipynb) |

### Base de dados

| Origem | Alto risco | Baixo risco | Descrição |
|---|---:|---:|---|
| `manual` | 60 | 60 | relatos escritos por mim, com linguagem coloquial, negações e casos ambíguos |
| `fase1` | 32 | 48 | frases geradas a partir do dataset simulado da **Fase 1** (sexo, faixa etária, sintomas e fatores de risco), com o rótulo `rotulo_risco_cardiovascular_simulado` |
| **Total** | **92** | **108** | |

### Pipeline

`frase` → minúsculas + *stopwords* (mantendo "não", "nem" e "sem") → **TF-IDF** (unigramas + bigramas) → classificador → avaliação

| Modelo | Acurácia (teste) | Recall alto risco | Acurácia (validação cruzada, 5 dobras) |
|---|---:|---:|---:|
| **Regressão Logística** ✅ | 0,78 | **0,87** | 0,70 |
| Árvore de Decisão | 0,80 | 0,70 | 0,73 |
| Naive Bayes | 0,78 | 0,78 | 0,64 |

Escolhi a **Regressão Logística** pelo maior recall de alto risco: em triagem, deixar passar um caso grave é o erro mais caro. Ela também é interpretável, e seus coeficientes mostram que termos como *peito*, *falta de ar*, *desmaiei* e *esquerdo* puxam a decisão para alto risco.

### Comportamento em frases novas

O modelo acerta casos clássicos e informais ("tô com o peito doendo e sem fôlego"), mas erra em:

- **negação:** "não sinto dor no peito nem falta de ar" é classificada como **alto risco** (65%);
- **ambiguidade:** "aperto no coração de saudade da família" também vira alto risco.

## Vieses, limitações e governança

A análise completa está na seção 8 do notebook 2, seguindo o roteiro de *fairness* do Cap. 7.

| Distorção observada | Evidência | Mitigação testada | Efeito |
|---|---|---|---|
| Palavras com negação são tratadas como sintoma presente | "não sinto dor no peito…" → 65% de alto risco | Marcação de negação (`nao_dor`, `nao_peito`) antes do TF-IDF | 48% → **baixo risco** |
| Atalho demográfico | "meia-idade" é o termo de maior peso para baixo risco; a mesma queixa varia 0,17 só ao trocar sexo e idade | Remoção dos termos demográficos | variação contrafactual **0,00** |
| Igualdade de oportunidade por sexo | paridade demográfica ≈ igual (diferença de 0,003), mas recall de alto risco de 0,80 (homens) contra 0,53 (mulheres) | Monitorar métricas por subgrupo e ampliar os dados | documentado como risco |
| Viés de rótulo da Fase 1 | rótulo calculado com pressão, colesterol e ECG; recall de 0,66 nas frases da Fase 1 contra 0,87 nas manuais | Usar rótulos de especialistas em uma base real | documentado |
| Falsos negativos | 3 casos de alto risco não detectados no teste | Limiar de 0,45 em vez de 0,50 | recall de **100%** (acurácia cai de 0,80 para 0,74) |

As mitigações aplicadas juntas **não reduziram a acurácia**: ela subiu de 0,78 para 0,80 no teste.

**Limitações:** a base é pequena e sintética; o vocabulário da Parte 1 é fechado; a negação é tratada por regra local; a linguagem informal e regional é pouco representada.

**Governança e responsabilidade:**

- uma solução de saúde como esta é de **alto risco** e exige **supervisão humana**: o sistema apoia a triagem, mas não decide;
- dados reais de saúde são **dados pessoais sensíveis** pela LGPD e exigem base legal, minimização, anonimização e controle de acesso;
- seriam necessários uma base representativa rotulada por especialistas, validação externa, métricas por subgrupo monitoradas em produção e registro (log) das sugestões para auditoria;
- a explicabilidade está presente nas duas partes: a Parte 1 mostra as evidências usadas em cada sugestão e a Parte 2 mostra os termos que mais pesam na decisão.

## Relação com o conteúdo da fase

| Capítulo | Onde foi aplicado |
|---|---|
| Cap. 10 — NLP baseado em regras | estemização RSLP, *stopwords*, NER por regex, regras de negação, ontologia RDF com `rdflib` e SPARQL |
| Cap. 11 — NLP estatístico | TF-IDF (`TfidfVectorizer`), Regressão Logística, Naive Bayes, `train_test_split`, matriz de confusão, `classification_report` |
| Cap. 7 — IA Responsável | paridade demográfica, igualdade de oportunidade (TPR), teste contrafactual, mitigação por pré e pós-processamento |
| Cap. 2 — RPA com Python | leitura e escrita automatizada de arquivos `.txt` e `.csv` |
| Fase 1 | reaproveitamento do dataset `pacientes_cardiacos_simulados.csv` para gerar parte da base rotulada |

**Fase 1:** [cardioia-fase1-batimentos-de-dados](https://github.com/JeffeSouza/cardioia-fase1-batimentos-de-dados/tree/atividade-cap01)

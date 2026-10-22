# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do desafio do MBA em IA (Full Cycle): puxar um prompt de baixa qualidade do LangSmith Prompt Hub, refatorá-lo com técnicas de Prompt Engineering, publicá-lo de volta no Hub e avaliá-lo com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity e Precision), atingindo **≥ 0.8 em todas**.

Enunciado original: [devfullcycle/mba-ia-pull-evaluation-prompt](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt)

O prompt converte **relatos de bugs** em **User Stories** ágeis ("Como um… eu quero… para que…" + critérios de aceitação Dado/Quando/Então).

---

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em [`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml). As técnicas estão listadas em `techniques_applied` no YAML e publicadas como tags/readme no Hub.

### 1. Role Prompting

**Por quê:** o v1 dizia apenas "você é um assistente". Sem persona, o modelo não sabe qual vocabulário, nível de detalhe e padrão de qualidade usar. Uma persona de Product Owner sênior com repertório técnico puxa o modelo para o jargão ágil correto (persona, valor de negócio, critérios testáveis) sem perder o contexto técnico dos bugs mais complexos.

**Como apliquei:**

```text
Você é um Product Owner Sênior com 10+ anos de experiência em times ágeis (Scrum),
especialista em transformar relatos de bugs em User Stories claras, testáveis e prontas
para refinamento. Você conhece engenharia de software (APIs, banco de dados, mobile,
front-end, segurança, performance) o suficiente para preservar o contexto técnico
relevante, mas escreve sempre com foco no valor para o usuário.
```

### 2. Few-shot Learning (obrigatória)

**Por quê:** as métricas comparam a resposta com uma referência (ground truth) que segue um formato bem específico. Descrever o formato só em texto deixa margem para variações; exemplos concretos de entrada → saída fixam estrutura, tom, idioma e nível de detalhe com muito mais força.

**Como apliquei:** três exemplos **inéditos** (não copiados do dataset de avaliação, para não "vazar" as respostas), um para cada nível de complexidade:

| Exemplo | Complexidade | O que ensina |
|---|---|---|
| Botão "Salvar rascunho" do blog | Simples | Frase da história + 5 critérios Gherkin |
| Busca com acento retorna HTTP 500 | Médio | Reaproveitar endpoint/código HTTP/log nos critérios + seção "Contexto Técnico" |
| Agendamento com SQL injection, race condition e SMS | Complexo | Seções `=== ... ===`, um bloco de critérios por problema (A, B, C), tasks com `[ÁREA]` |

### 3. Chain of Thought (CoT) — silencioso

**Por quê:** transformar um bug em história exige raciocínio (quem é afetado? qual o comportamento desejado? qual o valor? quais fatos do relato precisam ser preservados?). Porém, se o raciocínio aparecer na resposta, ele é avaliado junto e derruba **Precision** (conteúdo não solicitado) e **Clarity** (concisão). Por isso o modelo é instruído a pensar passo a passo **internamente** e a entregar apenas a história.

**Como apliquei:** uma seção "PROCESSO DE RACIOCÍNIO (pense passo a passo, em silêncio)" com 6 passos: persona → comportamento desejado → benefício → inventário de fatos do relato → classificação de complexidade → escolha do esqueleto.

### 4. Skeleton of Thought

**Por quê:** o dataset tem 3 níveis de complexidade e as referências têm estruturas diferentes para cada um (bugs simples: só história + critérios; médios: + "Contexto Técnico", "Exemplo de Cálculo", "Contexto de Segurança"…; complexos: seções `=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS TÉCNICOS ===`, `=== TASKS TÉCNICAS SUGERIDAS ===` etc.). Uma resposta curta demais para um bug complexo perde **recall** (F1); uma longa demais para um bug simples perde **precision** e **clarity**. Definir um esqueleto por nível resolve as duas coisas.

**Como apliquei:** a seção "ESQUELETOS DE SAÍDA" define o esqueleto de cada nível, e o passo 5 do CoT classifica o relato para escolher qual usar.

### Outras boas práticas aplicadas

- **System vs User prompt:** o v1 repetia `{bug_report}` no system e no user. No v2 o system prompt contém só instruções/exemplos e o user prompt contém só a tarefa + `{bug_report}` delimitado por aspas triplas.
- **Regras explícitas:** responder só com a história, primeira linha sempre "Como um…", critérios em Gherkin, reaproveitar números/endpoints do relato, não inventar fatos, cobrir todos os problemas, ser conciso.
- **Edge cases:** relato vago, múltiplos problemas, bug de segurança (OWASP), bug específico de navegador/SO, relato em outro idioma, pedido de melhoria em vez de bug, relato vazio.

---

## Resultados Finais

> **Preencher após rodar a avaliação** (ver "Como Executar").

- **Dataset de avaliação público (com os experimentos):** `<link gerado por share_dataset>`
- **Prompt v2 no Hub:** `https://smith.langchain.com/hub/<seu_handle>/bug_to_user_story_v2`

### Notas da avaliação

| Métrica | v1 (original) | v2 (otimizado) |
|---|---|---|
| Helpfulness | – | – |
| Correctness | – | – |
| F1-Score | – | – |
| Clarity | – | – |
| Precision | – | – |
| **Média** | – | – |

### Iterações

| # | Mudança | Resultado |
|---|---|---|
| 1 | Versão inicial do v2 (Role + Few-shot + CoT + Skeleton) | – |

### Screenshots

Salve em `docs/` (a pasta `screenshots/` está no `.gitignore`):

- `docs/evaluate_terminal.png` – saída do `python src/evaluate.py` com STATUS APROVADO
- `docs/experiment_dashboard.png` – experimento no LangSmith com as 5 notas
- `docs/tracing_*.png` – tracing detalhado de pelo menos 3 exemplos

### Comparação v1 × v2

| Aspecto | v1 | v2 | Por quê |
|---|---|---|---|
| Persona | "assistente" genérico | Product Owner Sênior com repertório técnico | Vocabulário ágil e foco em valor |
| Variável `{bug_report}` | Duplicada no system e no user | Só no user prompt, delimitada | Separação de responsabilidades; evita ruído |
| Formato de saída | Não especificado | "Como um / eu quero / para que" + Gherkin + seções por complexidade | Alinhamento com as referências (F1/Clarity) |
| Exemplos | Nenhum | 3 exemplos (simples, médio, complexo) | Few-shot fixa estrutura e tom |
| Raciocínio | Nenhum | CoT silencioso em 6 passos | Melhor análise sem poluir a resposta |
| Fidelidade | Nenhuma regra | Reaproveitar fatos do relato, não inventar, cobrir tudo | Precision (sem alucinação) e recall |
| Edge cases | Nenhum | 7 casos tratados | Robustez |
| Metadados | version, tags | + `techniques_applied`, description, readme no Hub | Rastreabilidade |

---

## Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no [LangSmith](https://smith.langchain.com) com API Key
- **Handle público do Hub** criado (LangSmith → Prompts → abra qualquer prompt → ⋯ → *Make Public* → *Choose your public handle*). O handle é definitivo.
- API Key da OpenAI **ou** do Google Gemini

### Instalação

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env   # e preencha as variáveis
```

Variáveis do `.env`:

| Variável | Descrição |
|---|---|
| `LANGSMITH_API_KEY` | API Key do LangSmith |
| `LANGSMITH_PROJECT` | Nome do projeto (o dataset será `<projeto>-eval`) |
| `USERNAME_LANGSMITH_HUB` | Seu handle público do Hub |
| `LLM_PROVIDER` | `openai` ou `google` |
| `OPENAI_API_KEY` / `GOOGLE_API_KEY` | Chave do provider escolhido |
| `LLM_MODEL` | Modelo que gera as user stories |
| `EVAL_MODEL` | Modelo juiz (pode ser o mesmo ou um mais capaz) |

### Fases

```bash
# 1. Pull do prompt original (leonanluppi/bug_to_user_story_v1) -> prompts/bug_to_user_story_v1.yml
python src/pull_prompts.py

# 2. Otimização: editar prompts/bug_to_user_story_v2.yml

# 3. Testes de validação do prompt
pytest tests/test_prompts.py -v

# 4. Push público para <handle>/bug_to_user_story_v2 (com descrição, tags e técnicas)
python src/push_prompts.py

# 5. Avaliação (cria um experimento no LangSmith e imprime o link)
python src/evaluate.py

# 6. (uma vez) Gerar link público do dataset com os experimentos
python -c "from dotenv import load_dotenv; load_dotenv(); import os; from langsmith import Client; print(Client().share_dataset(dataset_name=os.getenv('LANGSMITH_PROJECT') + '-eval')['url'])"
```

Para iterar: edite o YAML → `pytest` → `push_prompts.py` → `evaluate.py`, e compare os experimentos lado a lado no dashboard do LangSmith.

### Estrutura

```
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt original (pull)
│   └── bug_to_user_story_v2.yml   # prompt otimizado
├── datasets/bug_to_user_story.jsonl  # 15 bugs (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py   # pull do Hub -> YAML
│   ├── push_prompts.py   # valida YAML -> push público com metadados
│   ├── evaluate.py       # avaliação (fornecido)
│   ├── metrics.py        # métricas LLM-as-judge (fornecido)
│   └── utils.py          # helpers (fornecido)
└── tests/test_prompts.py # testes de validação do prompt
```

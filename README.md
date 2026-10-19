# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto que faz o pull de um prompt de baixa qualidade (`bug_to_user_story_v1`) do LangSmith Prompt Hub, o refatora com técnicas de Prompt Engineering (v2), publica o resultado de volta no Hub e o avalia com métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity e Precision), exigindo nota mínima de **0.8 em todas**.

O prompt converte relatos de bugs em User Stories ágeis com critérios de aceitação testáveis.

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em [prompts/bug_to_user_story_v2.yml](prompts/bug_to_user_story_v2.yml). As técnicas estão listadas no campo `techniques_applied` do YAML.

### 1. Few-shot Learning (obrigatória)
**Por que:** a saída esperada tem um formato bem específico (User Story + critérios Dado/Quando/Então/E, com seções extras conforme a complexidade). Exemplos mostram esse formato melhor do que qualquer descrição.

**Como foi aplicado:** 3 exemplos de entrada/saída, um para cada nível de complexidade, escritos de forma independente do dataset de avaliação (para não "decorar" as respostas):
- Exemplo 1 (simples): botão "Esqueci minha senha" → story + 5 critérios.
- Exemplo 2 (médio): exportação de CSV com HTTP 504 → story + critérios + Critérios Técnicos + Contexto Técnico.
- Exemplo 3 (complexo): módulo de notificações com 3 problemas → estrutura completa com `=== USER STORY PRINCIPAL ===`, critérios A/B/C, critérios técnicos, contexto, impacto e tasks.

Trecho do Exemplo 1 no prompt:
```text
Entrada:
O botão de "Esqueci minha senha" não faz nada quando clico nele na tela de login.

Saída:
Como um usuário que esqueceu a senha, eu quero recuperar o acesso à minha conta pela tela de login, para que eu consiga voltar a usar o sistema sem precisar de suporte.

Critérios de Aceitação:
- Dado que estou na tela de login
- Quando clico em "Esqueci minha senha"
- Então devo ser levado ao fluxo de recuperação de senha
```

### 2. Role Prompting
**Por que:** definir uma persona com experiência e foco ajusta o tom (profissional, empático, orientado a valor) e o nível de detalhe.

**Como foi aplicado:** o system prompt começa definindo a persona e a especialidade:
```text
Você é um Product Manager sênior, com mais de 10 anos de experiência em produtos digitais e metodologias ágeis. Sua especialidade é transformar relatos de bugs, muitas vezes confusos ou técnicos demais, em User Stories claras, completas e testáveis, que desenvolvedores e QA conseguem executar sem ambiguidade.
```

### 3. Chain of Thought (interno)
**Por que:** o bug precisa ser analisado (quem é afetado, comportamento atual versus esperado, valor, complexidade) antes de virar story. Mas o raciocínio exposto na resposta prejudicaria Clarity e Precision.

**Como foi aplicado:** a seção "PROCESSO (raciocínio interno)" lista 5 passos de análise e instrui explicitamente que o raciocínio **não deve aparecer** na resposta. A saída contém só a User Story.
```text
# PROCESSO (raciocínio interno)
Antes de escrever, pense passo a passo. Esse raciocínio é interno e NÃO deve aparecer na resposta.
1. Quem é afetado? Escolha uma persona específica (...)
2. O que o relato descreve? Separe o comportamento atual (o bug) do comportamento esperado.
3. Qual é o valor para essa persona? (...)
4. Qual é a complexidade? Conte problemas distintos, dados técnicos (...) e impacto citado.
5. Que critérios de aceitação verificáveis cobrem cada um dos problemas do relato?
```

### 4. Skeleton of Thought
**Por que:** os bugs complexos têm vários problemas e a resposta precisa ser organizada e previsível.

**Como foi aplicado:** o prompt define a estrutura de saída por nível de complexidade (simples, médio e complexo), com as seções, a ordem e a nomenclatura exatas. Para bugs complexos:
```text
=== USER STORY PRINCIPAL ===
Título: [título curto]
Descrição: Como um [persona], eu quero [ação], para que [benefício].
=== CRITÉRIOS DE ACEITAÇÃO ===
Um bloco por problema, identificados com A., B., C. (...)
=== CRITÉRIOS TÉCNICOS ===
=== CONTEXTO DO BUG ===
=== IMPACTO ===
=== TASKS TÉCNICAS ===
```

### Regras e edge cases
Além das técnicas, o prompt traz regras explícitas de comportamento e uma seção de casos especiais:
- Cobrir cada problema do relato; **não inventar** números, sistemas ou endpoints, e preservar literalmente os dados fornecidos. Informação ausente fica entre colchetes (por exemplo `[nome do gateway de pagamento]`).
- Critérios específicos e mensuráveis; tom profissional e construtivo mesmo com relatos agressivos.
- Relato vago, sem persona clara (usa "Como o sistema de..."), com stack trace/logs, com vários problemas misturados ou já trazendo o resultado esperado.

### System vs. User prompt
O **system prompt** contém persona, processo, formato, regras e exemplos, sem variáveis. O **user prompt** contém só o relato (`{bug_report}`) e uma lembrança curta do formato. No v1, `{bug_report}` estava duplicado nos dois.

## Resultados Finais

### Notas do v2 (avaliação com 15 exemplos)

| Métrica | Nota | Mínimo |
|---|---|---|
| Helpfulness | 0.87 | 0.8 ✓ |
| Correctness | 0.85 | 0.8 ✓ |
| F1-Score | 0.85 | 0.8 ✓ |
| Clarity | 0.89 | 0.8 ✓ |
| Precision | 0.85 | 0.8 ✓ |
| **Média geral** | **0.8603** | 0.8 ✓ |

Status: **APROVADO**, com todas as métricas >= 0.8. Modelos usados: `gemini-3.5-flash-lite` (gera) e `gemini-3.1-flash-lite` (avalia), ambos pelo plano gratuito do Gemini.

Observação sobre as iterações: o prompt v2 atingiu a meta na primeira avaliação válida. Uma tentativa anterior foi descartada por falha de infraestrutura (cota diária de 20 requisições do modelo juiz inicial, que gerou erros 429 e notas 0.0). Depois da troca do modelo avaliador, a avaliação rodou sem erros.

### Evidências no LangSmith
- Dataset de avaliação (15 exemplos) e experimentos: https://smith.langchain.com/public/c9721a8e-61fa-453b-966f-3e60076eee6e/d
- Prompt publicado no Hub: `vanderberg/bug_to_user_story_v2`
- Screenshots (em [docs/img/](docs/img/)):
  - [x] Dataset com os 15 exemplos ([print-dataset.png](docs/img/print-dataset.png))
  - [x] Experimento do v2 com as notas >= 0.8 ([print-avaliacao-v2.png](docs/img/print-avaliacao-v2.png))
  - [x] Tracing detalhado de 3 exemplos: [app offline-first (complexo)](docs/img/print-trace-2.png), [carrinho sem estoque (médio, nota mais baixa)](docs/img/print-trace-3.png) e [lista de notificações Android](docs/img/print-trace-1.png)

### Comparação v1 × v2

| Aspecto | v1 (original) | v2 (otimizado) |
|---|---|---|
| Persona | "Assistente que ajuda a transformar relatos" (genérica) | Product Manager sênior, com especialidade e foco definidos |
| Instrução | "Crie uma user story a partir dele" (vaga) | Processo de análise em 5 passos e tarefa explícita |
| Formato de saída | Não definido | "Como um... eu quero... para que..." + critérios Dado/Quando/Então/E |
| Complexidade | Tratada igual para todo bug | Estrutura própria para bugs simples, médios e complexos |
| Exemplos | Nenhum | 3 exemplos few-shot (simples, médio e complexo) |
| Regras | Nenhuma | Não inventar dados, preservar números, critérios mensuráveis, tom profissional |
| Edge cases | Nenhum | Relato vago, sem persona, com logs, com vários problemas |
| System vs. User | `{bug_report}` duplicado nos dois | System sem variáveis; `{bug_report}` só no user prompt |

**O que mudou e por quê:** o v1 deixava o modelo livre para escolher formato, profundidade e tom, então a saída variava e não seguia o padrão das User Stories de referência. O v2 fixa o formato e adapta a profundidade à complexidade, o que melhora F1 (cobertura do que se espera), Clarity (estrutura previsível) e Precision (regra de não inventar dados).

## Como Executar

### Pré-requisitos
- Python 3.10+
- Conta no [LangSmith](https://smith.langchain.com/) e uma API Key
- Um handle público no LangSmith Hub (ver abaixo)
- API Key de um provedor de LLM: Google Gemini ([AI Studio](https://aistudio.google.com/app/apikey)) ou OpenAI

### 1. Ambiente
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Handle do LangSmith Hub
O handle só existe depois que você torna um prompt público uma vez: LangSmith → **Prompts** → crie ou abra um prompt → três pontinhos → **Make Public** → defina o handle (definitivo).

### 3. Variáveis de ambiente
Copie `.env.example` para `.env` e preencha:
```
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=mba-ia-pull-evaluation-prompt
USERNAME_LANGSMITH_HUB=<seu handle>
LLM_PROVIDER=google            # ou openai
GOOGLE_API_KEY=...             # ou OPENAI_API_KEY
LLM_MODEL=gemini-3.5-flash-lite
EVAL_MODEL=gemini-3.1-flash-lite
```
> No plano gratuito do Gemini, os limites diários variam por modelo (alguns modelos têm só 20 requisições/dia). Uma avaliação completa faz cerca de 60 chamadas (15 de geração e 45 do juiz), então confira os limites em [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit).

### 4. Fluxo
```bash
# 1) Pull do prompt inicial (salva em prompts/bug_to_user_story_v1.yml)
python src/pull_prompts.py

# 2) Editar prompts/bug_to_user_story_v2.yml (já incluso)

# 3) Testes de validação (6 testes + 1 extra)
pytest tests/test_prompts.py -v

# 4) Push do prompt otimizado (público) para o LangSmith Hub
python src/push_prompts.py

# 5) Avaliação (puxa o prompt do Hub e roda os 15 exemplos)
python src/evaluate.py
```
> **Windows:** se aparecer erro de encoding ao imprimir ✓/❌, rode antes `set PYTHONUTF8=1` (cmd) ou `$env:PYTHONUTF8=1` (PowerShell).

> O `evaluate.py` avalia o que está **publicado no Hub**, então sempre rode o push depois de alterar o YAML.

### Link público do dataset de avaliação
```python
from langsmith import Client
print(Client().share_dataset(dataset_name="<LANGSMITH_PROJECT>-eval")["url"])
```
Rode uma única vez: ao compartilhar de novo, o link muda.

## Estrutura do projeto
```
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt inicial (pull)
│   └── bug_to_user_story_v2.yml   # prompt otimizado
├── datasets/bug_to_user_story.jsonl   # 15 exemplos de bugs
├── src/
│   ├── pull_prompts.py   # pull do LangSmith Hub
│   ├── push_prompts.py   # push do v2 para o Hub
│   ├── evaluate.py       # avaliação automática
│   ├── metrics.py        # métricas LLM-as-Judge
│   └── utils.py
└── tests/test_prompts.py  # testes de validação do prompt
```

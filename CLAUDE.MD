# Projeto Kallia-Finanças

Aplicação web Django de finanças pessoais para controle de investimentos, gastos e receitas. Desenvolvida com design dark premium (glassmorphism).

---

## 1. Visão Geral da Arquitetura

Django MVT com dois apps principais: **investments** e **budget**. O projeto possui uma barra lateral de navegação fixa com 5 seções: Visão Geral, Investimentos, Carteira, Metas, Configurações.

**Stack:**
- Gerenciador de pacotes: `uv`
- Backend: `Python + Django`
- Banco de Dados: `SQLite`
- Design: Dark Glassmorphism (CSS puro, sem Tailwind)
- Ícones: Boxicons
- Gráficos: Chart.js
- Cotações: `yfinance`
- Parsing de planilhas: `pandas + openpyxl`

---

## 2. App Investments (Estado Atual — CONCLUÍDO)

### Fonte de Dados
- O usuário importa relatórios mensais da B3 no formato **XLSX** (não PDF).
- Os arquivos ficam na pasta `static/xlsx/<ano>/`.
- O script `scripts/import_b3.py` processa os XLSXs com `pandas`.
- **Não há lançamentos manuais de investimentos** — tudo vem do relatório B3.

### Models (`investments/models.py`)

#### `Asset`
Representa um ativo (ação, FII, ETF, renda fixa, etc).

Campos: `ticker`, `name`, `category (FK)`, `asset_type`, `current_price`, `is_active`.

**Properties importantes (não são campos no banco — calculados):**
- `quantity`: compras - vendas (posição líquida atual)
- `average_price`: **Preço médio da posição atual**, reconstruído transação a transação em ordem cronológica. Zera completamente quando a posição vai a zero (venda total). Isso resolve o problema de ativos que foram vendidos e recomprados (ex: TAEE4, BBAS3).
- `total_invested`: total em R$ aportado - realizado
- `total_dividends`: total histórico de proventos
- `ttm_dividends`: proventos dos últimos 12 meses
- `ttm_dividends_monthly`: média mensal dos últimos 12 meses

#### `Transaction`
Registro de compra ou venda. Tipos: `buy`, `sell`.

Campos: `asset (FK)`, `transaction_type`, `quantity`, `price`, `total_value`, `date`, `broker`, `notes`, `source`.

#### `Dividend`
Registro de provento recebido.

Campos: `asset (FK)`, `dividend_type`, `quantity`, `value_per_share`, `total_value`, `payment_date`, `source`.

#### `Category`
Categoria dos ativos (ex: Ações, FIIs, ETFs).

### Views (`investments/views.py`)

| View | URL | Descrição |
|---|---|---|
| `dashboard` | `/investments/` | Cards KPI + gráfico de pizza da carteira + lista resumida de ativos |
| `import_b3` | `/investments/import/` | Upload do XLSX mensal da B3 |
| `dividends_charts` | `/investments/dividends/` | Gráficos de dividendos com 3 abas |
| `patrimony_charts` | `/investments/patrimony/` | Gráficos de evolução de patrimônio com 2 abas |
| `asset_list` | `/investments/assets/` | Tabela detalhada de ativos por classe |
| `update_prices_yfinance` | `/investments/api/update-prices/` | Busca cotações no Yahoo Finance (manual) |

### Lógica dos KPIs do Dashboard
- **Patrimônio Total**: soma de `(quantity × current_price)` para todos os ativos com `is_active=True` e `quantity > 0`. Se `current_price = 0`, usa o `average_price` como fallback.
- **Dividendos (Último Mês)**: soma dos proventos com `payment_date` no mês anterior.
- **Dividend Yield TTM**: `(proventos dos últimos 12 meses / patrimônio total) × 100`.
- **Rentabilidade**: `patrimônio atual - total aportado (qty × PM)`.

### Lógica da Página de Ativos (`asset_list`)
Colunas: Ticket, Qtd, Preço Médio (posição atual), Preço Atual (YF), Total Aportado, Patrimônio Atual, Rentabilidade (R$ e %), DY (12m), Dividendos/mês (média 12m).

Ordenação: por patrimônio decrescente dentro de cada classe.

### Cotações (Yahoo Finance)
- Atualização **manual** via botão na página de ativos.
- Endpoint: `POST /investments/api/update-prices/`
- O ticker enviado para o YF é `ticker + ".SA"` (ex: `BBAS3.SA`).

### Ajustes Manuais Conhecidos no Banco de Dados
- **BBAS3**: Split 1:2 em 15/04/2024 registrado como compra de 10 cotas a R$0,00 com `notes='Desdobramento 1:2 (Split)'`.
- **BBSE3 e MXRF11**: Reativados manualmente (`is_active=True`) pois o importador anual os havia desativado indevidamente.
- **CDB - BANCO DO BRASIL S/A**: Ativo desativado e transações fantasmas removidas.

---

## 3. App Budget (Estado Atual — EM DESENVOLVIMENTO)

Models básicos existem (`budget/models.py`) mas sem views ou templates funcionais ainda.

---

## 4. Design System

- **Tema**: Dark (`--bg-color: #0b0f19`)
- **Glassmorphism**: panels com `backdrop-filter: blur(12px)` e borda sutil
- **Cores**: Accent primary `#6366f1` (roxo), Success `#10b981` (verde), Danger `#ef4444` (vermelho), Warning `#f59e0b` (amarelo)
- **Fontes**: Inter (corpo) + Outfit (títulos)
- **Gráficos por classe de ativo**: Azul = FIIs, Laranja = Ações, Verde = Renda Fixa, Vermelho = ETFs
- **Formatação de moeda**: `R$` colado no número, ponto para milhar, vírgula para decimal (padrão BR: `R$1.234,56`)

---

## 5. Estrutura de Arquivos Principal

```
kallia-financa/
├── core/               # Configurações Django
│   ├── settings.py
│   └── urls.py
├── investments/        # App de investimentos
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/investments/
│       ├── dashboard.html
│       ├── import.html
│       ├── asset_list.html
│       ├── dividends_charts.html
│       └── patrimony_charts.html
├── budget/             # App de budget (em construção)
├── scripts/
│   └── import_b3.py    # Motor de importação XLSX
├── static/
│   ├── css/style.css
│   └── xlsx/           # Relatórios B3 separados por ano
│       ├── 2020/
│       ├── ...
│       └── 2026/
└── templates/
    └── base.html       # Layout base com sidebar
```

---

## 6. Regras de Colaboração

- **Idioma do código**: Inglês (variáveis, funções, comentários técnicos)
- **Idioma da UI**: Português brasileiro
- **Nunca criar lançamentos manuais de investimentos** — dados vêm exclusivamente dos XLSXs da B3
- **Preço médio**: sempre usar o algoritmo de posição atual (que zera no zeragem da posição), nunca a média simples de todas as compras
- **Cotações YF**: sempre manual (botão), nunca automático no carregamento da página
- **Commits**: usar `uv run` para todos os comandos Python, PowerShell usa `;` em vez de `&&`
- **Formato de data**: brasileiro (DD/MM/AAAA)
- **Ajustes de split**: registrar como transação com `price=0` e `notes` descritivo
- **`is_active`**: só deve ser `False` se o ativo genuinamente não faz mais parte da carteira (quantidade = 0 por um longo período)
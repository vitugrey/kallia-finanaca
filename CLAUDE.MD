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
- **Importação B3**: O usuário importa relatórios mensais da B3 no formato **XLSX**. O script `scripts/import_b3.py` processa os XLSXs com `pandas` e cria os ativos/operações com `source='b3_import'`.
- **Lançamentos Manuais**: Ativos e transações que não vêm da B3 (como BTC ou a Reserva no Nubank) podem ser lançados de forma manual pela tela de Lançamento Manual, gerando registros com `source='manual'`.

### Models (`investments/models.py`)

#### `Asset`
Representa um ativo (ação, FII, ETF, renda fixa, etc).
Campos: `ticker`, `name`, `category (FK)`, `asset_type`, `current_price`, `is_active`.

**Properties importantes (calculadas):**
- `quantity`: compras - vendas (posição líquida atual).
- `average_price`: preço médio reconstruído cronologicamente (reseta se a quantidade zerar).
- `total_invested`: total investido líquido.
- `total_dividends`: proventos históricos totais.

#### `Transaction`
Operação de compra ou venda (`buy`, `sell`).
Campos: `asset (FK)`, `transaction_type`, `quantity`, `price`, `total_value`, `date`, `broker`, `notes`, `source`.

#### `Dividend`
Registro de provento recebido (`dividend`, `jcp`, `income`, `amortization`).

#### `Category`
Categorias (ex: Acoes, FIIs, ETFs, Renda Fixa).

### Views (`investments/views.py`)

| View | URL | Descrição |
|---|---|---|
| `dashboard` | `/investments/` | KPIs de investimentos + gráficos + lista resumida de ativos |
| `import_report` | `/investments/importar/` | Upload do XLSX mensal da B3 |
| `dividends_charts` | `/investments/dividendos/` | Gráficos de evolução de dividendos |
| `patrimony_charts` | `/investments/patrimonio/` | Evolução patrimonial líquida |
| `asset_list` | `/investments/ativos/` | Tabela detalhada de ativos por classe |
| `update_prices_yfinance` | `/investments/api/update-prices/` | Atualiza cotações via yfinance (manual) |
| `manual_investments` | `/investments/manual/` | Dashboard de criação de ativos e transações manuais |
| `delete_transaction` | `/investments/manual/excluir-transacao/<int:tx_id>/` | Exclusão de transação manual |
| `update_asset_price` | `/investments/manual/atualizar-preco/<int:asset_id>/` | Atualização do preço atual de ativos de forma manual |

---

## 3. App Budget (Estado Atual — CONCLUÍDO)

App de fluxo de caixa para controle financeiro pessoal de curto prazo.

### Models (`budget/models.py`)
- `Category`: Categoria de transação financeira pessoal (ex: Moradia, Alimentação, Salário).
- `Transaction`: Transação de receita (`income`) ou despesa (`expense`). Permite configurar se é despesa de crédito (`is_credit`) ou transação recorrente (`is_fixed_income` / `is_fixed_expense`).

---

## 4. Design System & Frontend

- **Tema**: Dark (`--bg-color: #0b0f19`)
- **Glassmorphism**: Painéis com `backdrop-filter: blur(12px)` e bordas sutis.
- **Cores**: Accent primary `#6366f1` (roxo), Success `#10b981` (verde), Danger `#ef4444` (vermelho), Warning `#f59e0b` (amarelo), Info `#3b82f6` (azul).
- **Separação de Código**: Estilos (CSS) e Lógicas (JS) devem ficar obrigatoriamente fora dos templates HTML, alocados nos respectivos arquivos em `static/css/` e `static/js/`.

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
│       ├── patrimony_charts.html
│       └── manual_investments.html
├── budget/             # App de budget (fluxo de caixa)
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/budget/
│       ├── dashboard.html
│       └── transaction_list.html
├── scripts/
│   └── import_b3.py    # Importador XLSX
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── budget.css
│   │   ├── investments.css
│   │   ├── goals.css
│   │   ├── overview.css
│   │   └── manual_investments.css
│   └── js/
│       ├── investments_dashboard.js
│       ├── investments_common.js
│       ├── goals.js
│       └── manual_investments.js
└── templates/
    ├── base.html       # Layout base com sidebar
    ├── overview.html   # Visão Geral consolidada
    └── goals.html      # Metas e simuladores
```

---

## 6. Regras de Colaboração

- **Idioma do código**: Inglês (variáveis, funções, tabelas, comentários técnicos).
- **Idioma da UI**: Português brasileiro.
- **Separação de Static Files**: Estilos inline (`style="..."`) e scripts inline são estritamente desencorajados. Todo CSS novo deve ir para a pasta `static/css/` e todo JS novo para `static/js/`.
- **Preço médio**: Sempre usar a propriedade `average_price` que reconstrói a carteira cronologicamente e reseta se a posição zerar.
- **Cotações yfinance**: Manual (via botão na interface), nunca de forma síncrona no carregamento da página.
- **Ambiente de Execução**: Comandos de backend usam o gerenciador de pacotes `uv` (ex: `uv run manage.py ...`).
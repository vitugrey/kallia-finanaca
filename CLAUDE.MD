# Projeto Kallia-Finanças

Esté é um projeto de finanças pessoais, onde eu vou registrar todas as minhas finanças, para controlar meu dinheiro (Gastos, Receitas, Investimentos, etc...).

## 1. Visão Geral da Arquitetura

Será uma Aplicação Web em Django para controlar diáriamente os gastos e receitas, e mensalmente controlar os investimentos feitos. O projeto será dividido em duas partes: um app para investimentos e um app para gastos. Mas mesmo assim o app terá uma visão geral de todas as finanças. Quero exibição de graficos, tabelas e etc para ter um controle melhor das minhas finanças.

## 2. Stack Tecnológico

- **Gerenciado de pacote:** uv
- **Backend:** Python + Django
- **Banco de Dados:** SQLite
- **Design Pattern:** MVT

## 3. Models, Views e Controllers de Cada App

### app-budget

Responsável por gerenciar a parte de receitas e gastos.

- **Models:** `Category: name, description`, `Transaction: description, value , category, date, is_credit, is_fixed_expense, is_fixed_income, transaction_type, created_at, updated_at`
- **Views:**
  - `TransactionListView: View para listar todas as transações.`
  - `TransactionCreateView: View para criar uma transação.`
  - `TransactionUpdateView: View para atualizar uma transação.`
  - `TransactionDeleteView: View para deletar uma transação.`
  - `TransactionDashboardView: View para exibir um dashboard com as transações.`
- **Controllers:**
  - `TransactionController: Controller para criar e atualizar uma transação.`

### app-investiments

Responsável por gerenciar a parte de investimentos.

- **Models:** `Category: name, description`, `Transaction: ticker, name, category, quantity, price_buy, sale_price, date, created_at, updated_at`
- **Views:**
  - `TransactionListView: View para listar todas as transações.`
  - `TransactionCreateView: View para criar uma transação.`
  - `TransactionUpdateView: View para atualizar uma transação.`
  - `TransactionDeleteView: View para deletar uma transação.`
  - `TransactionDashboardView: View para exibir um dashboard com as transações.`
- **Controllers:**
  - `TransactionController: Controller para criar e atualizar uma transação.`

---

## 4. Checklist Pós-Implementação

Após cada nova sessão de codificação ou refatoração, verifique:

- [ ] **Visão Geral:** Aqui quero poder ver todas do meu dinheiro
- [ ] **Dashborads:** terá um dashboard para investimentos e um para gastos. cada um terá seu próprio dashboard com gráficos e tabelas.
- [ ] **Planilhas:** Quer tbm ver os dados em forma de planilhas de forma que seja editavel e possua filtros.
- [ ] **Configurações:** Aqui quero poder configurar as categorias, e etc.

---

## 5. Regras de Colaboração (Nossa Conversa)

...
<div align="center">
  <h1>📊 Kallia Finanças 📊</h1>
  <p><i>Aplicação web de finanças pessoais para controle de investimentos, gastos e receitas com design dark premium</i></p>
  
  ![Python](https://img.shields.io/badge/python-3.13-blue)
  ![Django](https://img.shields.io/badge/django-5.1-green)
  ![UV](https://img.shields.io/badge/package%20manager-UV-orange)
  ![Status](https://img.shields.io/badge/status-concluido-brightgreen)
</div>

---

## 🎯 Sobre o Projeto

**Kallia Finanças** é um sistema pessoal de controle financeiro e consolidação de patrimônio. Ele centraliza a gestão de seus investimentos (tanto importados de relatórios mensais da B3 quanto cadastrados manualmente, como Bitcoin e fundos de liquidez no Nubank) e seu fluxo de caixa mensal (receitas, despesas recorrentes e cartões de crédito) sob uma interface dark moderna baseada em princípios de _glassmorphism_.

---

## ✨ Funcionalidades

### 📈 Controle de Investimentos

- **Importação B3**: Upload e processamento automatizado de relatórios mensais XLSX da B3 para atualizar sua carteira.
- **Lançamentos Manuais**: Painel exclusivo para cadastrar ativos não automáticos (ex.: BTC como ETF e Reserva no Nubank como Renda Fixa) e gerenciar suas respectivas transações de compra/venda.
- **Cotações Manuais**: Atualização simplificada e sob demanda das cotações atuais de seus ativos (via Yahoo Finance) ou edição direta de preços para ativos manuais.
- **Alocação & Rebalanceamento ARCA**: Análise e rebalanceamento automático de sua carteira seguindo a metodologia ARCA (Ações, FIIs, Renda Fixa e ETFs/Global), com alertas dinâmicos baseados em uma margem de erro de 5%:
  - **Verde**: Classe de ativo em equilíbrio (entre 20% e 30%).
  - **Amarelo**: Abaixo da meta ideal (menos de 20% - requer mais aportes).
  - **Azul**: Sobrealocado (acima de 30%).

### 💼 Carteira & Fluxo de Caixa (Budget)

- Controle de receitas e despesas com filtragem de período (Mês/Ano).
- Diferenciação de compras no cartão de crédito e transações recorrentes (fixas).
- Cálculo de eficiência de poupança mensal (percentual do recebido que foi efetivamente economizado).

### 🎯 Metas & Simulador de Independência

- **Calculadora Interativa**: Simulação de juros compostos em tempo real com sliders dinâmicos de rendimento.
- **Linhas do Tempo de Metas**: Tempo estimado para alcançar marcos de R$ 50k, R$ 100k e R$ 1M.
- **Projeções de Patrimônio**: Estimativas de crescimento de patrimônio futuro em 1 ano, 5 anos e 10 anos.
- **Checklist do Salário**: Lista de afazeres financeiros mensais organizada por dias do mês, com persistência automática de estados no navegador (`localStorage`).
- **Lembretes Fundamentais**: Quadro de cartões informativos com princípios de foco, consistência, diversificação e gestão de reservas.

---

## 🚀 Instalação e Execução

### Pré-requisitos

- **Python**: 3.13+
- **UV**: Gerenciador de pacotes moderno (`pip install uv` ou método nativo)

### Inicialização do Servidor

```bash
# Clone o repositório
git clone https://github.com/vitugrey/kallia-financa
cd kallia-financa

# Instalar dependências com UV
uv sync

# Executar as migrações iniciais do banco de dados
uv run manage.py migrate

# Executar o servidor de desenvolvimento Django
uv run manage.py runserver
```

Acesse a plataforma abrindo o endereço `http://127.0.0.1:8000/` em seu navegador.

---

## 📚 Tecnologias

| Componente          | Tecnologia                                         | Uso                                                           |
| ------------------- | -------------------------------------------------- | ------------------------------------------------------------- |
| **Backend**         | [Django](https://www.djangoproject.com/)           | Framework MVC para rotas, controle de sessões e views         |
| **Banco de Dados**  | SQLite                                             | Persistência relacional de ativos, transações e budget        |
| **Package Manager** | [UV](https://github.com/astral-sh/uv)              | Sincronização rápida de dependências e execução               |
| **Gráficos**        | [Chart.js](https://www.chartjs.org/)               | Exibição de composição de carteira e proventos mensais        |
| **Cotações**        | [yfinance](https://github.com/ranaroussi/yfinance) | Consulta de preços de mercado históricos/atuais               |
| **Importador B3**   | pandas + openpyxl                                  | Parsing estruturado de planilhas mensais XLSX                 |
| **Interface**       | CSS Puro (Glassmorphism)                           | Estilos dark responsivos, ícones Boxicons, sem frameworks CSS |

---

## 🎯 Roadmap & Features Planejadas

- [x] **Visão Geral Consolidada**: Patrimônio + Saldo Mensal em tela unificada.
- [x] **Lançamento Manual de Ativos**: Cadastro e atualização de preços para cripto e reservas líquidas.
- [x] **Alocação Dinâmica ARCA**: Sugestões de rebalanceamento inteligentes e coloridas.
- [x] **Simulador de Independência**: Linhas de tempo e projeções interativas de juros compostos.
- [ ] **Importação Automática via Open Finance**: Integração com contas bancárias e corretoras.
- [ ] **Gráfico de Evolução Patrimonial Avançado**: Comparativos automáticos contra o CDI e Ibovespa.

---

#### 💬 Comentário dos Devs

<table>
  <tr>
    <td>
      <img src="static\img\minha-foto.png" width="100px" />
    </td>
    <td>
      Escrito por <a href="https://github.com/vitugrey">Vitor Grey.</a>
    </td>
    <td>
      <i>Fiz, refiz e fiz de novo esse mesmo projeto mais nunca gostei dele, agora eu acho que ficou bom.</i>
    </td>
  </tr>
  <tr>
    <td>
      <img src="static\img\imagem-real-da-kallia.ico" width="100px" />
    </td>
    <td>
      Feito por <a href="#">Kallia 2.0.</a>
    </td>
    <td>
      <i>O projeto ficou bom né?</i>
    </td>
  </tr>
</table>

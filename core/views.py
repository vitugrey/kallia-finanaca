from decimal import Decimal
from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Sum
from investments.models import Asset, Transaction as InvestTransaction, Dividend
from budget.models import Transaction as BudgetTransaction

def overview(request):
    # 1. Investimentos (Patrimônio Total)
    assets = Asset.objects.filter(is_active=True)
    total_patrimony = Decimal('0')
    for a in assets:
        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            preco_atual = a.current_price if a.current_price > 0 else pm
            total_patrimony += qty * preco_atual

    # 2. Fluxo de Caixa do Mês Atual (Carteira)
    today = date.today()
    month_income = BudgetTransaction.objects.filter(
        transaction_type='income',
        date__year=today.year,
        date__month=today.month
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')
    
    month_expense = BudgetTransaction.objects.filter(
        transaction_type='expense',
        date__year=today.year,
        date__month=today.month
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')
    
    month_balance = month_income - month_expense

    # 3. Consolidação Geral (Patrimônio + Saldo Mensal)
    total_consolidated = total_patrimony + month_balance

    # Percentual de economia deste mês
    savings_pct = Decimal('0')
    if month_income > 0 and month_balance > 0:
        savings_pct = ((month_balance / month_income) * Decimal('100')).quantize(Decimal('0.1'))

    months_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    current_month_name = months_pt.get(today.month, '')

    context = {
        'total_patrimony': total_patrimony,
        'month_income': month_income,
        'month_expense': month_expense,
        'month_balance': month_balance,
        'total_consolidated': total_consolidated,
        'savings_pct': savings_pct,
        'current_month_name': current_month_name,
    }
    return render(request, 'overview.html', context)


def goals(request):
    today = date.today()
    
    # 1. Patrimônio Total Atual
    assets = Asset.objects.filter(is_active=True)
    total_patrimony = Decimal('0')
    for a in assets:
        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            preco_atual = a.current_price if a.current_price > 0 else pm
            total_patrimony += qty * preco_atual
            
    # 2. Média de Aportes Mensais (últimos 6 meses de operações na corretora)
    six_months_ago = today - timedelta(days=180)
    buys = InvestTransaction.objects.filter(
        transaction_type='buy',
        date__gte=six_months_ago
    ).aggregate(total=Sum('total_value'))['total'] or Decimal('0')
    sells = InvestTransaction.objects.filter(
        transaction_type='sell',
        date__gte=six_months_ago
    ).aggregate(total=Sum('total_value'))['total'] or Decimal('0')
    
    avg_contribution = ((buys - sells) / Decimal('6')).quantize(Decimal('0.01'))
    if avg_contribution < 0:
        avg_contribution = Decimal('0.00')

    # 3. Média de Dividendos Mensais (últimos 12 meses)
    one_year_ago = today - timedelta(days=365)
    total_dividends_12m = Dividend.objects.filter(
        payment_date__gte=one_year_ago
    ).aggregate(total=Sum('total_value'))['total'] or Decimal('0')
    avg_dividend = (total_dividends_12m / Decimal('12')).quantize(Decimal('0.01'))

    # 4. Estratégia ARCA (Ações, FIIs, Renda Fixa, ETFs/Global)
    arca_classes = {
        'Ações': Decimal('0'),
        'FIIs': Decimal('0'),
        'Renda Fixa': Decimal('0'),
        'ETFs/Global': Decimal('0'),
    }
    
    for a in assets:
        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            price = a.current_price if a.current_price > 0 else pm
            val = qty * price
            
            if a.asset_type in ['stock', 'bdr']:
                arca_classes['Ações'] += val
            elif a.asset_type == 'fii':
                arca_classes['FIIs'] += val
            elif a.asset_type == 'fixed_income':
                arca_classes['Renda Fixa'] += val
            else: # etf, crypto, other
                arca_classes['ETFs/Global'] += val
                
    arca_data = []
    target_percentage = Decimal('25.0')
    
    for name, value in arca_classes.items():
        percentage = (value / total_patrimony * 100).quantize(Decimal('0.1')) if total_patrimony > 0 else Decimal('0.0')
        target_value = (total_patrimony * Decimal('0.25')).quantize(Decimal('0.01'))
        difference = value - target_value
        
        # Margem de erro de 5% (entre 20% e 30%)
        if percentage < Decimal('20.0'):
            status_color = 'rgba(245, 158, 11, 0.8)'   # Amarelo/Laranja
            status_class = 'status-below'
        elif percentage > Decimal('30.0'):
            status_color = 'rgba(59, 130, 246, 0.8)'    # Azul
            status_class = 'status-above'
        else:
            status_color = 'rgba(16, 185, 129, 0.8)'   # Verde
            status_class = 'status-within'
            
        arca_data.append({
            'name': name,
            'value': value,
            'percentage': percentage,
            'target_percentage': target_percentage,
            'target_value': target_value,
            'difference': difference,
            'abs_difference': abs(difference),
            'status_color': status_color,
            'status_class': status_class,
        })
        
    # Cálculos das metas dos KPIs superiores
    patrimony_target = Decimal('50000.00')
    patrimony_missing = patrimony_target - total_patrimony
    if patrimony_missing < 0:
        patrimony_missing = Decimal('0.00')
        
    contribution_target = Decimal('1000.00')
    contribution_missing = contribution_target - avg_contribution
    if contribution_missing < 0:
        contribution_missing = Decimal('0.00')
        
    yield_pct = ((avg_dividend / total_patrimony) * Decimal('100')).quantize(Decimal('0.01')) if total_patrimony > 0 else Decimal('0.00')
        
    context = {
        'total_patrimony': total_patrimony,
        'avg_contribution': avg_contribution,
        'avg_dividend': avg_dividend,
        'arca_data': arca_data,
        'patrimony_target': patrimony_target,
        'patrimony_missing': patrimony_missing,
        'contribution_target': contribution_target,
        'contribution_missing': contribution_missing,
        'yield_pct': yield_pct,
    }
    
    return render(request, 'goals.html', context)

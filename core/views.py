from decimal import Decimal
from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Sum
from investments.models import Asset, Transaction as InvestTransaction, Dividend
from budget.models import Transaction as BudgetTransaction

def overview(request):
    # 1. Investimentos
    assets = Asset.objects.filter(is_active=True)
    total_patrimony = Decimal('0')
    for a in assets:
        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            preco_atual = a.current_price if a.current_price > 0 else pm
            total_patrimony += qty * preco_atual

    # 2. Carteira (Budget)
    total_income = BudgetTransaction.objects.filter(transaction_type='income').aggregate(total=Sum('value'))['total'] or Decimal('0')
    total_expense = BudgetTransaction.objects.filter(transaction_type='expense').aggregate(total=Sum('value'))['total'] or Decimal('0')
    wallet_balance = total_income - total_expense

    # 3. Consolidação Geral
    total_consolidated = total_patrimony + wallet_balance

    context = {
        'total_patrimony': total_patrimony,
        'wallet_balance': wallet_balance,
        'total_consolidated': total_consolidated,
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
        
        arca_data.append({
            'name': name,
            'value': value,
            'percentage': percentage,
            'target_percentage': target_percentage,
            'target_value': target_value,
            'difference': difference,
            'abs_difference': abs(difference),
        })
        
    context = {
        'total_patrimony': total_patrimony,
        'avg_contribution': avg_contribution,
        'avg_dividend': avg_dividend,
        'arca_data': arca_data,
    }
    
    return render(request, 'goals.html', context)

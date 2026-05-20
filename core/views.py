from decimal import Decimal
from django.shortcuts import render
from django.db.models import Sum
from investments.models import Asset
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

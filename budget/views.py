from datetime import date, datetime, timedelta
from decimal import Decimal
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Category, Transaction

def dashboard(request):
    today = date.today()
    
    # 1. Obter anos disponíveis dinamicamente com base nas transações existentes
    years_qs = Transaction.objects.dates('date', 'year', order='DESC')
    available_years = [y.year for y in years_qs]
    if not available_years:
        available_years = [today.year]
    
    # 2. Ler filtros de mês e ano da URL
    selected_month_raw = request.GET.get('month')
    selected_year_raw = request.GET.get('year')
    
    selected_year = int(selected_year_raw) if selected_year_raw else today.year
    
    if selected_month_raw == 'all':
        selected_month = 'all'
        start_date = date(selected_year, 1, 1)
        end_date = date(selected_year, 12, 31)
    else:
        if selected_month_raw and selected_month_raw.isdigit():
            selected_month = int(selected_month_raw)
        else:
            selected_month = today.month
            
        start_date = date(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = date(selected_year, 12, 31)
        else:
            end_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)
            
    # 3. Filtrar transações no período selecionado
    period_transactions = Transaction.objects.filter(date__range=(start_date, end_date))
    
    # 4. Cálculo dos novos KPIs baseados no período
    # KPIs de Receita
    income_val = period_transactions.filter(transaction_type=Transaction.TransactionType.INCOME).aggregate(total=Sum('value'))['total'] or Decimal('0')
    # Receita Extra (tudo o que não for categoria 'Salário')
    extra_income_val = period_transactions.filter(
        transaction_type=Transaction.TransactionType.INCOME
    ).exclude(category__name__iexact='Salário').aggregate(total=Sum('value'))['total'] or Decimal('0')

    # KPIs de Despesa
    expense_val = period_transactions.filter(transaction_type=Transaction.TransactionType.EXPENSE).aggregate(total=Sum('value'))['total'] or Decimal('0')
    # Despesas no Cartão de Crédito
    credit_expense_val = period_transactions.filter(
        transaction_type=Transaction.TransactionType.EXPENSE,
        is_credit=True
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')

    # KPIs de Balanço (Diferença)
    balance_val = income_val - expense_val
    # Diferença sem contar despesas no crédito
    non_credit_expense_val = period_transactions.filter(
        transaction_type=Transaction.TransactionType.EXPENSE,
        is_credit=False
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')
    balance_no_credit_val = income_val - non_credit_expense_val

    # 5. Gráfico de Rosca: Despesas por Categoria (Período Selecionado)
    category_expenses = period_transactions.filter(
        transaction_type=Transaction.TransactionType.EXPENSE
    ).values('category__name').annotate(total=Sum('value')).order_by('-total')

    category_labels = [c['category__name'] for c in category_expenses]
    category_values = [float(c['total'] or 0) for c in category_expenses]

    # 6. Gráfico de Evolução Mensal (Fluxo Mensal)
    if selected_month == 'all':
        # Mostrar os 12 meses do ano filtrado
        months_data = {}
        for m in range(1, 13):
            m_key = f"{m:02d}/{selected_year}"
            months_data[m_key] = {'income': 0.0, 'expense': 0.0}
            
        yearly_stats = Transaction.objects.filter(date__year=selected_year)\
            .annotate(month_trunc=TruncMonth('date'))\
            .values('month_trunc', 'transaction_type')\
            .annotate(total=Sum('value'))\
            .order_by('month_trunc')
            
        for stat in yearly_stats:
            if stat['month_trunc']:
                m_key = stat['month_trunc'].strftime('%m/%Y')
                if m_key in months_data:
                    months_data[m_key][stat['transaction_type']] = float(stat['total'] or 0)
    else:
        # Mostrar 6 meses terminando no mês selecionado
        start_y = selected_year
        start_m = selected_month - 5
        if start_m <= 0:
            start_m += 12
            start_y -= 1
        six_months_start = date(start_y, start_m, 1)
        
        monthly_stats = Transaction.objects.filter(date__range=(six_months_start, end_date))\
            .annotate(month_trunc=TruncMonth('date'))\
            .values('month_trunc', 'transaction_type')\
            .annotate(total=Sum('value'))\
            .order_by('month_trunc')
            
        months_data = {}
        temp_y, temp_m = start_y, start_m
        for _ in range(6):
            m_key = f"{temp_m:02d}/{temp_y}"
            months_data[m_key] = {'income': 0.0, 'expense': 0.0}
            temp_m += 1
            if temp_m > 12:
                temp_m = 1
                temp_y += 1
                
        for stat in monthly_stats:
            if stat['month_trunc']:
                m_key = stat['month_trunc'].strftime('%m/%Y')
                if m_key in months_data:
                    months_data[m_key][stat['transaction_type']] = float(stat['total'] or 0)

    evolution_labels = list(months_data.keys())
    evolution_income = [months_data[m]['income'] for m in evolution_labels]
    evolution_expense = [months_data[m]['expense'] for m in evolution_labels]

    # 7. Transações do Período Selecionado
    period_transactions_list = period_transactions.select_related('category').all().order_by('-date', '-created_at')
    categories = Category.objects.all()

    context = {
        'available_years': available_years,
        'selected_month': selected_month,
        'selected_year': selected_year,
        
        'balance_val': balance_val,
        'balance_no_credit_val': balance_no_credit_val,
        'income_val': income_val,
        'extra_income_val': extra_income_val,
        'expense_val': expense_val,
        'credit_expense_val': credit_expense_val,
        
        'recent_transactions': period_transactions_list,
        'categories': categories,
        'evolution_labels': json.dumps(evolution_labels),
        'evolution_income': json.dumps(evolution_income),
        'evolution_expense': json.dumps(evolution_expense),
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
    }

    return render(request, 'budget/dashboard.html', context)

def transaction_list(request):
    category_id = request.GET.get('category')
    tx_type = request.GET.get('type')
    search_query = request.GET.get('q')
    month_filter = request.GET.get('month') # Formato: YYYY-MM

    transactions = Transaction.objects.select_related('category').all().order_by('-date', '-created_at')

    if category_id:
        transactions = transactions.filter(category_id=category_id)
    
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
        
    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) | Q(category__name__icontains=search_query)
        )

    if month_filter:
        try:
            yr, mn = map(int, month_filter.split('-'))
            transactions = transactions.filter(date__year=yr, date__month=mn)
        except ValueError:
            pass

    # Paginação (50 por página)
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'selected_type': tx_type,
        'search_query': search_query,
        'selected_month': month_filter,
    }
    return render(request, 'budget/transaction_list.html', context)

@require_POST
def create_transaction(request):
    description = request.POST.get('description')
    value_raw = request.POST.get('value')
    category_id = request.POST.get('category')
    date_str = request.POST.get('date')
    transaction_type = request.POST.get('transaction_type')
    is_credit = request.POST.get('is_credit') == 'on'
    is_fixed_expense = request.POST.get('is_fixed_expense') == 'on'
    is_fixed_income = request.POST.get('is_fixed_income') == 'on'

    if not all([description, value_raw, category_id, date_str, transaction_type]):
        messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
        return redirect('budget:dashboard')

    try:
        value_raw = value_raw.replace('.', '').replace(',', '.')
        value = Decimal(value_raw)
        
        category = get_object_or_404(Category, id=category_id)
        tx_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        Transaction.objects.create(
            description=description,
            value=value,
            category=category,
            date=tx_date,
            is_credit=is_credit,
            is_fixed_expense=is_fixed_expense if transaction_type == Transaction.TransactionType.EXPENSE else False,
            is_fixed_income=is_fixed_income if transaction_type == Transaction.TransactionType.INCOME else False,
            transaction_type=transaction_type
        )
        messages.success(request, 'Transação registrada com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao salvar transação: {str(e)}')

    next_url = request.POST.get('next') or 'budget:dashboard'
    return redirect(next_url)

@require_POST
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    description = request.POST.get('description')
    value_raw = request.POST.get('value')
    category_id = request.POST.get('category')
    date_str = request.POST.get('date')
    transaction_type = request.POST.get('transaction_type')
    is_credit = request.POST.get('is_credit') == 'on'
    is_fixed_expense = request.POST.get('is_fixed_expense') == 'on'
    is_fixed_income = request.POST.get('is_fixed_income') == 'on'

    if not all([description, value_raw, category_id, date_str, transaction_type]):
        messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
        return redirect('budget:dashboard')

    try:
        value_raw = value_raw.replace('.', '').replace(',', '.')
        value = Decimal(value_raw)
        
        category = get_object_or_404(Category, id=category_id)
        tx_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        transaction.description = description
        transaction.value = value
        transaction.category = category
        transaction.date = tx_date
        transaction.transaction_type = transaction_type
        transaction.is_credit = is_credit
        transaction.is_fixed_expense = is_fixed_expense if transaction_type == Transaction.TransactionType.EXPENSE else False
        transaction.is_fixed_income = is_fixed_income if transaction_type == Transaction.TransactionType.INCOME else False
        transaction.save()
        messages.success(request, 'Transação atualizada com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao editar transação: {str(e)}')

    next_url = request.POST.get('next') or 'budget:dashboard'
    return redirect(next_url)

@require_POST
def create_category(request):
    name = request.POST.get('name')
    description = request.POST.get('description', '')

    if not name:
        messages.error(request, 'O nome da categoria é obrigatório.')
    else:
        try:
            Category.objects.create(name=name, description=description)
            messages.success(request, f'Categoria "{name}" criada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao criar categoria: {str(e)}')

    return redirect('budget:dashboard')

from datetime import date, datetime
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
    current_month_start = date(today.year, today.month, 1)

    # 1. KPIs principais
    total_income = Transaction.objects.filter(transaction_type=Transaction.TransactionType.INCOME).aggregate(total=Sum('value'))['total'] or Decimal('0')
    total_expense = Transaction.objects.filter(transaction_type=Transaction.TransactionType.EXPENSE).aggregate(total=Sum('value'))['total'] or Decimal('0')
    total_balance = total_income - total_expense

    month_income = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.INCOME,
        date__gte=current_month_start
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')

    month_expense = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.EXPENSE,
        date__gte=current_month_start
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')

    month_balance = month_income - month_expense

    # 2. Dados de evolução mensal (últimos 6 meses)
    # Subtrai 5 meses para ter um total de 6 meses (incluindo o atual)
    start_year = today.year
    start_month = today.month - 5
    if start_month <= 0:
        start_month += 12
        start_year -= 1
    six_months_ago = date(start_year, start_month, 1)

    monthly_stats = Transaction.objects.filter(date__gte=six_months_ago)\
        .annotate(month=TruncMonth('date'))\
        .values('month', 'transaction_type')\
        .annotate(total=Sum('value'))\
        .order_by('month')

    months_data = {}
    # Inicializar os últimos 6 meses para garantir que todos apareçam no gráfico, mesmo vazios
    temp_year, temp_month = start_year, start_month
    for _ in range(6):
        m_key = f"{temp_month:02d}/{temp_year}"
        months_data[m_key] = {'income': 0.0, 'expense': 0.0}
        temp_month += 1
        if temp_month > 12:
            temp_month = 1
            temp_year += 1

    for stat in monthly_stats:
        if stat['month']:
            m_key = stat['month'].strftime('%m/%Y')
            if m_key in months_data:
                months_data[m_key][stat['transaction_type']] = float(stat['total'] or 0)

    evolution_labels = list(months_data.keys())
    evolution_income = [months_data[m]['income'] for m in evolution_labels]
    evolution_expense = [months_data[m]['expense'] for m in evolution_labels]

    # 3. Distribuição por Categoria (Despesas do mês atual)
    category_expenses = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.EXPENSE,
        date__gte=current_month_start
    ).values('category__name').annotate(total=Sum('value')).order_by('-total')

    category_labels = [c['category__name'] for c in category_expenses]
    category_values = [float(c['total'] or 0) for c in category_expenses]

    # 4. Transações recentes e categorias
    recent_transactions = Transaction.objects.select_related('category').all().order_by('-date', '-created_at')[:10]
    categories = Category.objects.all()

    context = {
        'total_balance': total_balance,
        'month_income': month_income,
        'month_expense': month_expense,
        'month_balance': month_balance,
        'recent_transactions': recent_transactions,
        'categories': categories,
        'evolution_labels': json.dumps(evolution_labels),
        'evolution_income': json.dumps(evolution_income),
        'evolution_expense': json.dumps(evolution_expense),
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
    }

    return render(request, 'budget/dashboard.html', context)

def transaction_list(request):
    # Parâmetros de filtro
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
        # Converter valor substituindo vírgula por ponto se necessário
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

    # Retorna para a página de origem (dashboard ou lista de transações)
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

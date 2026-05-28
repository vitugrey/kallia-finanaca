import json
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import yfinance as yf
from django.contrib import messages
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth, TruncYear
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .models import Asset, Dividend, Transaction, Category

# Adiciona o diretório de scripts ao path para importar o motor de importação B3
# O import de import_b3 é feito dentro da view pois é um módulo local (não instalado)
_scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


def dashboard(request):
    assets = Asset.objects.filter(is_active=True).order_by('asset_type', 'ticker', 'name')

    portfolio = []
    total_patrimony = Decimal('0')
    total_invested = Decimal('0')
    total_dividends = Decimal('0')

    # Grupos para o grafico de pizza
    patrimony_by_type = {}

    for a in assets:
        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            preco_atual = a.current_price if a.current_price > 0 else pm
            patrimony = qty * preco_atual
            aportado = qty * pm
            rentabilidade = patrimony - aportado
            divs = a.total_dividends

            total_patrimony += patrimony
            total_invested += aportado
            total_dividends += divs

            type_name = a.get_asset_type_display()
            if type_name not in patrimony_by_type:
                patrimony_by_type[type_name] = Decimal('0')
            patrimony_by_type[type_name] += patrimony

            portfolio.append({
                'asset': a,
                'ticker': a.ticker or a.name,
                'type': type_name,
                'quantity': qty,
                'current_price': preco_atual,
                'patrimony': patrimony,
                'rentabilidade': rentabilidade,
                'rentabilidade_perc': (rentabilidade / aportado * 100) if aportado > 0 else 0
            })

    portfolio.sort(key=lambda x: x['patrimony'], reverse=True)

    allocation = []
    for t_name, t_val in patrimony_by_type.items():
        perc = (t_val / total_patrimony * 100) if total_patrimony > 0 else 0
        allocation.append({'name': t_name, 'value': t_val, 'percentage': perc})
    allocation.sort(key=lambda x: x['value'], reverse=True)

    total_rentabilidade = total_patrimony - total_invested
    total_rentabilidade_perc = (total_rentabilidade / total_invested * 100) if total_invested > 0 else 0

    last_div = Dividend.objects.order_by('-payment_date').first()
    last_month_divs = Decimal('0')
    if last_div:
        last_month_divs = Dividend.objects.filter(
            payment_date__year=last_div.payment_date.year,
            payment_date__month=last_div.payment_date.month
        ).aggregate(t=Sum('total_value'))['t'] or Decimal('0')

    one_year_ago = date.today() - timedelta(days=365)
    ttm_dividends = Dividend.objects.filter(payment_date__gte=one_year_ago).aggregate(t=Sum('total_value'))['t'] or Decimal('0')
    dividend_yield_ttm = (ttm_dividends / total_patrimony * 100) if total_patrimony > 0 else 0

    # 8. Gráfico de Proventos Mensais por Ativo (Últimos 12 meses)
    today_date = date.today()
    months = []
    for i in range(11, -1, -1):
        m = today_date.month - i
        y = today_date.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    start_date = date(months[0][0], months[0][1], 1)
    if months[-1][1] == 12:
        end_date = date(months[-1][0], 12, 31)
    else:
        end_date = date(months[-1][0], months[-1][1] + 1, 1) - timedelta(days=1)

    bar_chart_labels = [f"{m:02d}/{y}" for y, m in months]
    month_to_idx = { (y, m): idx for idx, (y, m) in enumerate(months) }

    asset_data = {}
    dividends_in_period = Dividend.objects.filter(
        payment_date__range=(start_date, end_date)
    ).select_related('asset')

    for d in dividends_in_period:
        y = d.payment_date.year
        m = d.payment_date.month
        if (y, m) in month_to_idx:
            idx = month_to_idx[(y, m)]
            ticker = d.asset.ticker or d.asset.name
            if ticker not in asset_data:
                asset_data[ticker] = [0.0] * 12
            asset_data[ticker][idx] += float(d.total_value)

    bar_chart_datasets = []
    for ticker, values in asset_data.items():
        if any(values):
            bar_chart_datasets.append({
                'label': ticker,
                'data': values
            })

    context = {
        'portfolio': portfolio,
        'total_patrimony': total_patrimony,
        'total_invested': total_invested,
        'total_rentabilidade': total_rentabilidade,
        'total_rentabilidade_perc': total_rentabilidade_perc,
        'total_dividends': total_dividends,
        'last_month_divs': last_month_divs,
        'dividend_yield_ttm': dividend_yield_ttm,
        'allocation': allocation,
        'bar_chart_labels': json.dumps(bar_chart_labels),
        'bar_chart_datasets': json.dumps(bar_chart_datasets),
    }

    return render(request, 'investments/dashboard.html', context)


def update_prices_yfinance(request):
    if request.method == 'POST':
        assets = Asset.objects.filter(is_active=True).exclude(asset_type='fixed_income')
        updated = 0
        for asset in assets:
            if asset.ticker:
                try:
                    ticker_yf = asset.ticker + ".SA"
                    info = yf.Ticker(ticker_yf).fast_info
                    current_price = info.last_price
                    if current_price and current_price > 0:
                        asset.current_price = Decimal(str(current_price))
                        asset.save()
                        updated += 1
                except Exception as e:
                    print(f"Erro ao buscar {asset.ticker}: {e}")
        return JsonResponse({'status': 'success', 'updated': updated})
    return JsonResponse({'status': 'error'}, status=400)


def dividends_charts(request):
    yearly = Dividend.objects.annotate(year=TruncYear('payment_date')).values('year').annotate(total=Sum('total_value')).order_by('year')
    yearly_labels = [str(y['year'].year) for y in yearly if y['year']]
    yearly_data = [float(y['total']) for y in yearly if y['year']]

    monthly = Dividend.objects.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('total_value')).order_by('-month')[:24]
    monthly = list(monthly)[::-1]
    monthly_labels = [f"{m['month'].month:02d}/{m['month'].year}" for m in monthly if m['month']]
    monthly_data = [float(m['total']) for m in monthly if m['month']]

    all_time = Dividend.objects.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('total_value')).order_by('month')
    all_time_labels = [f"{m['month'].month:02d}/{m['month'].year}" for m in all_time if m['month']]
    all_time_data = [float(m['total']) for m in all_time if m['month']]

    context = {
        'yearly_labels': json.dumps(yearly_labels),
        'yearly_data': json.dumps(yearly_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'all_time_labels': json.dumps(all_time_labels),
        'all_time_data': json.dumps(all_time_data),
    }
    return render(request, 'investments/dividends_charts.html', context)


def patrimony_charts(request):
    years = Transaction.objects.annotate(year=TruncYear('date')).values('year').annotate(
        buys=Sum('total_value', filter=Q(transaction_type='buy')),
        sells=Sum('total_value', filter=Q(transaction_type='sell'))
    ).order_by('year')

    yearly_labels = []
    yearly_acc_data = []
    acc = 0
    for y in years:
        if not y['year']:
            continue
        acc += float(y['buys'] or 0) - float(y['sells'] or 0)
        yearly_labels.append(str(y['year'].year))
        yearly_acc_data.append(acc)

    months = Transaction.objects.annotate(month=TruncMonth('date')).values('month').annotate(
        buys=Sum('total_value', filter=Q(transaction_type='buy')),
        sells=Sum('total_value', filter=Q(transaction_type='sell'))
    ).order_by('month')

    monthly_labels = []
    monthly_data = []
    monthly_acc = 0
    for m in months:
        if not m['month']:
            continue
        monthly_acc += float(m['buys'] or 0) - float(m['sells'] or 0)
        monthly_labels.append(f"{m['month'].month:02d}/{m['month'].year}")
        monthly_data.append(monthly_acc)

    context = {
        'yearly_labels': json.dumps(yearly_labels),
        'yearly_acc_data': json.dumps(yearly_acc_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
    }
    return render(request, 'investments/patrimony_charts.html', context)


def asset_list(request):
    assets = Asset.objects.filter(is_active=True).order_by('category__name', 'ticker')

    portfolio_by_cat = {}
    for a in assets:
        cat = a.get_asset_type_display()
        if cat not in portfolio_by_cat:
            portfolio_by_cat[cat] = []

        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            preco_atual = a.current_price if a.current_price > 0 else pm
            patrimony = qty * preco_atual
            aportado = qty * pm
            rentabilidade = patrimony - aportado
            rentabilidade_perc = (rentabilidade / aportado * 100) if aportado > 0 else 0
            ttm_divs = a.ttm_dividends
            dy_ttm = (ttm_divs / patrimony * 100) if patrimony > 0 else Decimal('0')
            divs_por_mes = a.ttm_dividends_monthly

            portfolio_by_cat[cat].append({
                'ticker': a.ticker or a.name,
                'name': a.name,
                'quantity': qty,
                'pm': pm,
                'current_price': preco_atual,
                'rentabilidade': rentabilidade,
                'rentabilidade_perc': rentabilidade_perc,
                'aportado': aportado,
                'patrimony': patrimony,
                'dy_ttm': dy_ttm,
                'divs_por_mes': divs_por_mes,
            })

    for cat in portfolio_by_cat:
        portfolio_by_cat[cat].sort(key=lambda x: x['patrimony'], reverse=True)

    return render(request, 'investments/asset_list.html', {'portfolio_by_cat': portfolio_by_cat})


def import_report(request):
    if request.method == 'POST':
        xlsx_file = request.FILES.get('xlsx_file')
        if not xlsx_file:
            messages.error(request, 'Por favor, selecione um arquivo XLSX.')
            return redirect('investments:import_report')

        if not xlsx_file.name.endswith('.xlsx'):
            messages.error(request, 'O arquivo deve ser uma planilha XLSX (.xlsx).')
            return redirect('investments:import_report')

        try:
            from import_b3 import process_monthly_report  # noqa: E402
            stats = process_monthly_report(xlsx_file)

            msg = f"Planilha importada com sucesso! Encontradas: {stats.get('buys', 0)} compras, {stats.get('sells', 0)} vendas, {stats.get('dividends', 0)} proventos."
            messages.success(request, msg)
            return redirect('investments:dashboard')

        except Exception as e:
            messages.error(request, f'Erro ao processar o arquivo Excel: {str(e)}')
            return redirect('investments:import_report')

    return render(request, 'investments/import.html')


def manual_investments(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_transaction':
            asset_choice = request.POST.get('asset_choice')
            
            if asset_choice == 'new':
                ticker = request.POST.get('new_ticker', '').strip().upper()
                name = request.POST.get('new_name', '').strip()
                asset_type = request.POST.get('new_asset_type')
                category_id = request.POST.get('new_category')
                
                if not name or not asset_type or not category_id:
                    messages.error(request, 'Nome, Tipo de Ativo e Categoria são obrigatórios para novos ativos.')
                    return redirect('investments:manual_investments')
                
                try:
                    category = Category.objects.get(id=category_id)
                    # Se tiver ticker e já existir, usa o existente, senão cria
                    if ticker and Asset.objects.filter(ticker=ticker).exists():
                        asset = Asset.objects.get(ticker=ticker)
                    else:
                        asset = Asset.objects.create(
                            ticker=ticker,
                            name=name,
                            asset_type=asset_type,
                            category=category
                        )
                except Category.DoesNotExist:
                    messages.error(request, 'Categoria inválida.')
                    return redirect('investments:manual_investments')
            else:
                asset_id = request.POST.get('asset_id')
                if not asset_id:
                    messages.error(request, 'Selecione um ativo válido.')
                    return redirect('investments:manual_investments')
                try:
                    asset = Asset.objects.get(id=asset_id)
                except Asset.DoesNotExist:
                    messages.error(request, 'Ativo não encontrado.')
                    return redirect('investments:manual_investments')
            
            # Registrar transação
            transaction_type = request.POST.get('transaction_type')
            qty_str = request.POST.get('quantity')
            price_str = request.POST.get('price')
            tx_date_str = request.POST.get('date')
            broker = request.POST.get('broker', 'Manual')
            notes = request.POST.get('notes', '')
            
            if not qty_str or not price_str or not tx_date_str:
                messages.error(request, 'Quantidade, Preço Unitário e Data são obrigatórios.')
                return redirect('investments:manual_investments')
                
            try:
                quantity = Decimal(qty_str.replace(',', '.'))
                price = Decimal(price_str.replace(',', '.'))
                tx_date = date.fromisoformat(tx_date_str)
                
                Transaction.objects.create(
                    asset=asset,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    date=tx_date,
                    broker=broker,
                    notes=notes,
                    source=Transaction.Source.MANUAL
                )
                messages.success(request, 'Operação manual registrada com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao registrar transação: {e}')
                
            return redirect('investments:manual_investments')

    assets = Asset.objects.filter(is_active=True).order_by('asset_type', 'ticker', 'name')
    categories = Category.objects.all()
    manual_transactions = Transaction.objects.filter(
        source=Transaction.Source.MANUAL
    ).select_related('asset').order_by('-date', '-id')
    
    context = {
        'assets': assets,
        'categories': categories,
        'manual_transactions': manual_transactions,
        'asset_types': Asset.AssetType.choices,
        'today': date.today(),
    }
    return render(request, 'investments/manual_investments.html', context)


def delete_transaction(request, tx_id):
    if request.method == 'POST':
        try:
            tx = Transaction.objects.get(id=tx_id, source=Transaction.Source.MANUAL)
            tx.delete()
            messages.success(request, 'Operação excluída com sucesso!')
        except Transaction.DoesNotExist:
            messages.error(request, 'Operação não encontrada ou não é manual.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir operação: {e}')
    return redirect('investments:manual_investments')


def update_asset_price(request, asset_id):
    if request.method == 'POST':
        try:
            asset = Asset.objects.get(id=asset_id)
            price_str = request.POST.get('current_price')
            if price_str:
                price = Decimal(price_str.replace(',', '.'))
                asset.current_price = price
                asset.save()
                messages.success(request, f'Preço de {asset.ticker or asset.name} atualizado para R$ {price}')
            else:
                messages.error(request, 'Preço inválido.')
        except Asset.DoesNotExist:
            messages.error(request, 'Ativo não encontrado.')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar preço: {e}')
    return redirect('investments:manual_investments')

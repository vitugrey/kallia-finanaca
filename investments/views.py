from django.shortcuts import render
from django.db.models import Sum, Q
from .models import Asset, Category, Dividend, Transaction
from decimal import Decimal

def dashboard(request):
    assets = Asset.objects.filter(is_active=True).order_by('asset_type', 'ticker', 'name')
    
    portfolio = []
    total_patrimony = Decimal('0')
    total_invested = Decimal('0') # O que foi aportado
    total_dividends = Decimal('0')
    
    # Grupos para o grafico de pizza
    patrimony_by_type = {}
    
    for a in assets:
        qty = a.quantity
        if qty > 0:
            pm = a.average_price
            
            # Fallback para preco_atual ser o pm se o preco atual for 0
            preco_atual = a.current_price if a.current_price > 0 else pm
            
            patrimony = qty * preco_atual
            aportado = qty * pm
            rentabilidade = patrimony - aportado
            divs = a.total_dividends
            
            total_patrimony += patrimony
            total_invested += aportado
            total_dividends += divs
            
            # Agrupar por tipo (Pizza)
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
            
    # Sort portfolio by patrimony descending
    portfolio.sort(key=lambda x: x['patrimony'], reverse=True)
    
    # Calcular % de cada tipo para o grafico de pizza
    allocation = []
    for t_name, t_val in patrimony_by_type.items():
        perc = (t_val / total_patrimony * 100) if total_patrimony > 0 else 0
        allocation.append({
            'name': t_name,
            'value': t_val,
            'percentage': perc,
        })
    allocation.sort(key=lambda x: x['value'], reverse=True)
    
    # Rentabilidade Total
    total_rentabilidade = total_patrimony - total_invested
    total_rentabilidade_perc = (total_rentabilidade / total_invested * 100) if total_invested > 0 else 0
    
    # Dividendos do Ultimo Mes Registrado
    last_div = Dividend.objects.order_by('-payment_date').first()
    last_month_divs = Decimal('0')
    if last_div:
        last_month_divs = Dividend.objects.filter(
            payment_date__year=last_div.payment_date.year,
            payment_date__month=last_div.payment_date.month
        ).aggregate(t=Sum('total_value'))['t'] or Decimal('0')
        
    # Dividend Yield (Ultimos 12 meses)
    from datetime import date, timedelta
    one_year_ago = date.today() - timedelta(days=365)
    ttm_dividends = Dividend.objects.filter(payment_date__gte=one_year_ago).aggregate(t=Sum('total_value'))['t'] or Decimal('0')
    dividend_yield_ttm = (ttm_dividends / total_patrimony * 100) if total_patrimony > 0 else 0
            
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
    }
    
    return render(request, 'investments/dashboard.html', context)

import yfinance as yf
from django.http import JsonResponse

def update_prices_yfinance(request):
    if request.method == 'POST':
        assets = Asset.objects.filter(is_active=True).exclude(asset_type='fixed_income')
        updated = 0
        for asset in assets:
            if asset.ticker:
                try:
                    # Para a B3, o yfinance exige o sufixo .SA
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
    import json
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth, TruncYear
    
    # Por Ano
    yearly = Dividend.objects.annotate(year=TruncYear('payment_date')).values('year').annotate(total=Sum('total_value')).order_by('year')
    yearly_labels = [str(y['year'].year) for y in yearly if y['year']]
    yearly_data = [float(y['total']) for y in yearly if y['year']]
    
    # Por Mês (Ultimos 24 meses)
    monthly = Dividend.objects.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('total_value')).order_by('-month')[:24]
    monthly = list(monthly)[::-1] # Inverter para ordem cronologica
    monthly_labels = [f"{m['month'].month:02d}/{m['month'].year}" for m in monthly if m['month']]
    monthly_data = [float(m['total']) for m in monthly if m['month']]
    
    context = {
        'yearly_labels': json.dumps(yearly_labels),
        'yearly_data': json.dumps(yearly_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data)
    }
    return render(request, 'investments/dividends_charts.html', context)

def patrimony_charts(request):
    import json
    from django.db.models import Sum
    from django.db.models.functions import TruncYear
    
    # Para o patrimônio por ano, a estimativa do que foi aportado até aquele ano
    # Isso seria a soma de (quantity * price) onde transaction_type='buy' menos 'sell' ate o ano.
    # Para simplificar, faremos um grafico de Aportes Acumulados.
    years = Transaction.objects.annotate(year=TruncYear('date')).values('year').annotate(
        buys=Sum('total_value', filter=Q(transaction_type='buy')),
        sells=Sum('total_value', filter=Q(transaction_type='sell'))
    ).order_by('year')
    
    labels = []
    data_aportado = []
    acc = 0
    for y in years:
        if not y['year']: continue
        b = float(y['buys'] or 0)
        s = float(y['sells'] or 0)
        acc += (b - s)
        labels.append(str(y['year'].year))
        data_aportado.append(acc)
        
    context = {
        'labels': json.dumps(labels),
        'data_aportado': json.dumps(data_aportado)
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
            
            divs = a.total_dividends
            yield_on_cost = (divs / aportado * 100) if aportado > 0 else 0
            
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
                'yield': yield_on_cost,
                'total_dividends': divs
            })
            
    # Sort dictionaries inside
    for cat in portfolio_by_cat:
        portfolio_by_cat[cat].sort(key=lambda x: x['patrimony'], reverse=True)
            
    return render(request, 'investments/asset_list.html', {'portfolio_by_cat': portfolio_by_cat})

from django.contrib import messages
from django.shortcuts import redirect
import os
import sys

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
            # Add scripts to path to import
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
                
            from import_b3 import process_monthly_report
            
            stats = process_monthly_report(xlsx_file)
            
            msg = f"Planilha importada com sucesso! Encontradas: {stats.get('buys', 0)} compras, {stats.get('sells', 0)} vendas, {stats.get('dividends', 0)} proventos."
            messages.success(request, msg)
            return redirect('investments:dashboard')
            
        except Exception as e:
            messages.error(request, f'Erro ao processar o arquivo Excel: {str(e)}')
            return redirect('investments:import_report')
            
    return render(request, 'investments/import.html')

"""Gera planilha ano a ano da carteira."""
import os, sys, re
from datetime import date
from decimal import Decimal
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django; django.setup()

from django.db.models import Sum
from investments.models import Asset, Transaction, Dividend

YEARS = range(2020, 2027)

def qty_at(asset, year_end):
    buys = asset.transactions.filter(transaction_type="buy", date__lte=year_end).aggregate(t=Sum("quantity"))["t"] or Decimal("0")
    sells = asset.transactions.filter(transaction_type="sell", date__lte=year_end).aggregate(t=Sum("quantity"))["t"] or Decimal("0")
    return buys - sells

def divs_in_year(asset, year):
    return asset.dividends.filter(
        payment_date__year=year
    ).aggregate(t=Sum("total_value"))["t"] or Decimal("0")

# Separar por tipo
categories = {
    "Acoes": [],
    "BDRs": [],
    "ETFs": [],
    "FIIs": [],
    "Renda Fixa": [],
}

for a in Asset.objects.all().order_by("asset_type", "ticker", "name"):
    cat = a.category.name if a.category else "Outros"
    # Normalizar
    if cat == "Acoes": categories["Acoes"].append(a)
    elif cat == "BDRs": categories["BDRs"].append(a)
    elif cat == "ETFs": categories["ETFs"].append(a)
    elif cat == "Fundos Imobiliarios": categories["FIIs"].append(a)
    elif cat == "Renda Fixa": categories["Renda Fixa"].append(a)

# Gerar output
output = []

for cat_name, assets in categories.items():
    if not assets: continue
    
    output.append(f"\n{'='*100}")
    output.append(f"  {cat_name.upper()}")
    output.append(f"{'='*100}")
    
    # Header
    header = f"{'Ativo':<15}"
    for y in YEARS:
        header += f" | {y:>8}"
    header += " | Divs Total"
    output.append(header)
    output.append("-" * len(header))
    
    totals_by_year = defaultdict(Decimal)
    total_divs = Decimal("0")
    
    for a in assets:
        ticker = a.ticker or a.name[:12]
        line = f"{ticker:<15}"
        
        has_any = False
        for y in YEARS:
            year_end = date(y, 12, 31)
            qty = qty_at(a, year_end)
            if qty > 0: has_any = True
            
            if qty > 0 and qty == int(qty):
                line += f" | {int(qty):>8}"
            elif qty > 0:
                line += f" | {float(qty):>8.2f}"
            else:
                line += f" | {'--':>8}"
        
        divs = a.total_dividends
        total_divs += divs
        if divs > 0:
            line += f" | R${divs:>9.2f}"
        else:
            line += f" | {'--':>11}"
        
        if has_any:
            output.append(line)
    
    output.append("")

# Proventos por ano
output.append(f"\n{'='*100}")
output.append(f"  PROVENTOS POR ANO")
output.append(f"{'='*100}")

header2 = f"{'Ativo':<15}"
for y in YEARS:
    header2 += f" | {y:>8}"
header2 += " |    TOTAL"
output.append(header2)
output.append("-" * len(header2))

grand_total_by_year = defaultdict(Decimal)

for cat_name, assets in categories.items():
    for a in assets:
        ticker = a.ticker or a.name[:12]
        line = f"{ticker:<15}"
        row_total = Decimal("0")
        has_any = False
        
        for y in YEARS:
            d = divs_in_year(a, y)
            grand_total_by_year[y] += d
            row_total += d
            if d > 0:
                has_any = True
                line += f" | {float(d):>8.2f}"
            else:
                line += f" | {'--':>8}"
        
        if row_total > 0:
            line += f" | R${float(row_total):>7.2f}"
        else:
            line += f" | {'--':>10}"
        
        if has_any:
            output.append(line)

# Total por ano
output.append("-" * len(header2))
total_line = f"{'TOTAL':<15}"
grand = Decimal("0")
for y in YEARS:
    t = grand_total_by_year[y]
    grand += t
    total_line += f" | {float(t):>8.2f}"
total_line += f" | R${float(grand):>7.2f}"
output.append(total_line)

# Patrimonio por ano
output.append(f"\n{'='*100}")
output.append(f"  PATRIMONIO ESTIMADO POR ANO (Qtd x Preco Medio)")
output.append(f"{'='*100}")

pat_by_year = defaultdict(Decimal)
for cat_name, assets in categories.items():
    for a in assets:
        for y in YEARS:
            year_end = date(y, 12, 31)
            qty = qty_at(a, year_end)
            if qty > 0:
                pm = a.average_price
                pat_by_year[y] += qty * pm

pat_line = f"{'PATRIMONIO':<15}"
for y in YEARS:
    p = pat_by_year[y]
    pat_line += f" | R${float(p):>7.0f}"
output.append(pat_line)

# Print tudo
for line in output:
    print(line)

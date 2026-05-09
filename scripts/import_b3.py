"""
Importador B3 v7 - Totalmente automatizado via XLSX.

Estrategia:
  1. Itera sobre os anos (2020 a 2026).
  2. Para cada ano, itera sobre as planilhas XLSX mensais.
     -> Extrai COMPRAS e VENDAS reais do "Negociações".
     -> Extrai PROVENTOS do "Proventos Recebidos".
  3. No final do ano, le a planilha anual (XLSX).
     -> Valida as posicoes das acoes/FIIs.
     -> Extrai e ajusta as posicoes de Renda Fixa (Tesouro/CDB).
     -> Zera ativos que sumiram da carteira (vendidos/vencidos).
"""
import os, sys, glob
import pandas as pd
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django; django.setup()

from django.db.models import Sum
from investments.models import Asset, Category, Dividend, Transaction

XLSX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "xlsx")

CATEGORY_MAP = {
    "stock":"Acoes","fii":"Fundos Imobiliarios","etf":"ETFs",
    "bdr":"BDRs","fixed_income":"Renda Fixa","other":"Outros",
}

KNOWN_ASSETS = {
    "AZUL4":("stock","AZUL S.A."),"BBAS3":("stock","BANCO DO BRASIL S.A."),
    "BBDC3":("stock","BANCO BRADESCO S.A."),"BBSE3":("stock","BB SEGURIDADE PARTICIPACOES S.A."),
    "B3SA3":("stock","B3 S.A."),"EGIE3":("stock","ENGIE BRASIL ENERGIA S.A."),
    "ELET6":("stock","CENTRAIS ELETRICAS BRASILEIRAS S.A."),"GRND3":("stock","GRENDENE S.A."),
    "IRBR3":("stock","IRB BRASIL RESSEGUROS S.A."),"ITSA4":("stock","ITAUSA S.A."),
    "LAME4":("stock","LOJAS AMERICANAS S.A."),"OIBR4":("stock","OI S.A."),
    "PETR4":("stock","PETROBRAS S.A."),
    "SAPR4":("stock","CIA SANEAMENTO DO PARANA"),"SAPR11":("stock","CIA SANEAMENTO DO PARANA (UNIT)"),
    "TAEE4":("stock","TRANSMISSORA ALIANCA DE ENERGIA ELETRICA S.A."),
    "TASA4":("stock","TAURUS ARMAS S.A."),
    "NUBR33":("bdr","NU HOLDINGS LTD."),"NVDC34":("bdr","NVIDIA CORP"),
    "IVVB11":("etf","ISHARES S&P 500 FDO INV COTAS FDO INDICE"),
    "COIN11":("etf","BUENA VISTA NEOS BITCOIN HIGH INCOME"),
    "QQQI11":("etf","BUENA VISTA NASDAQ-100 NEOS HIGH INCOME"),
    "AFHI11":("fii","AF INVEST CRI FII"),"HFOF11":("fii","HEDGE TOP FOFII 3 FDO INV IMOB"),
    "HGLG11":("fii","CSHG LOGISTICA FDO INV IMOB"),"HGRU11":("fii","CSHG RENDA URBANA FDO INV IMOB"),
    "HSML11":("fii","HSI MALL FDO INV IMOB"),"HSLG11":("fii","HSI LOGISTICA FDO INV IMOB"),
    "MALL11":("fii","MALLS BRASIL PLURAL FDO INV IMOB"),"MXRF11":("fii","MAXI RENDA FDO INV IMOB"),
    "PMLL11":("fii","PATRIA MALLS FII"),
    "RZTR11":("fii","RIZA TERRAX FDO INV IMOB"),
    "VGIP11":("fii","VALORA CRI INDICE DE PRECO FDO INV IMOB"),
    "VILG11":("fii","VINCI LOGISTICA FDO INV IMOB"),
    "VISC11":("fii","VINCI SHOPPING CENTERS FII"),
    "XPCI11":("fii","XP CREDITO IMOBILIARIO FDO INV IMOB"),
    "XPLG11":("fii","XP LOGISTICA FDO INV IMOB"),
    "XPML11":("fii","XP MALLS FDO INV IMOB"),
}

def safe_decimal(val):
    if pd.isna(val): return Decimal('0')
    if isinstance(val, (int, float)): 
        # Python floats are already using '.'
        return Decimal(str(val))
    s = str(val).strip()
    if not s or s == '-' or s.lower() == 'nan': return Decimal('0')
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return Decimal(s)
    except:
        return Decimal('0')

def get_or_create_asset(ticker, name=None, asset_type=None):
    if ticker in KNOWN_ASSETS:
        at, default_name = KNOWN_ASSETS[ticker]
        name = name or default_name
        asset_type = asset_type or at
    else:
        asset_type = asset_type or ("fixed_income" if "Tesouro" in (name or "") else "stock")
        name = name or ticker

    cat_name = CATEGORY_MAP.get(asset_type, "Outros")
    category, _ = Category.objects.get_or_create(name=cat_name)

    if ticker:
        asset, _ = Asset.objects.get_or_create(
            ticker=ticker,
            defaults={"name": name, "category": category, "asset_type": asset_type}
        )
    else:
        asset, _ = Asset.objects.get_or_create(
            name=name, ticker="",
            defaults={"category": category, "asset_type": asset_type}
        )
    return asset

def current_quantity(asset, up_to_date=None):
    qs = asset.transactions.all()
    if up_to_date:
        qs = qs.filter(date__lte=up_to_date)
    buys = qs.filter(transaction_type="buy").aggregate(t=Sum("quantity"))["t"] or Decimal("0")
    sells = qs.filter(transaction_type="sell").aggregate(t=Sum("quantity"))["t"] or Decimal("0")
    return buys - sells

def parse_date_pt(date_str):
    if isinstance(date_str, datetime):
        return date_str.date()
    if not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if len(date_str) == 7 and "/" in date_str: # MM/YYYY
        parts = date_str.split("/")
        return date(int(parts[1]), int(parts[0]), 28)
    if len(date_str) == 10 and "/" in date_str: # DD/MM/YYYY
        parts = date_str.split("/")
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    return None

# ═══════════════════════════════════════════════════════════════
# PROCESSAMENTO MENSAL (XLSX)
# ═══════════════════════════════════════════════════════════════

def process_monthly_report(filepath):
    filename = getattr(filepath, 'name', os.path.basename(str(filepath)))
    print(f"  [>] Lendo XLSX: {filename}")
    
    stats = {'buys': 0, 'sells': 0, 'dividends': 0}
    
    try:
        xls = pd.ExcelFile(filepath)
    except Exception as e:
        print(f"Erro ao abrir Excel: {e}")
        return stats

    if 'Negociações' in xls.sheet_names:
        df_neg = pd.read_excel(xls, sheet_name='Negociações')
        if not df_neg.empty:
            for _, row in df_neg.iterrows():
                ticker_raw = str(row.get('Código de Negociação', '')).strip()
                if not ticker_raw or ticker_raw == 'nan': continue
                
                ticker = ticker_raw[:-1] if ticker_raw.endswith('F') and ticker_raw[:-1] in KNOWN_ASSETS else ticker_raw
                if ticker not in KNOWN_ASSETS: continue
                
                col_periodo = 'Período (Inicial)' if 'Período (Inicial)' in df_neg.columns else 'Período'
                date_str = row.get(col_periodo, '')
                if isinstance(date_str, str): date_str = date_str.split(' ')[0]
                
                d = parse_date_pt(date_str)
                if not d: continue
                
                buy_qty = safe_decimal(row.get('Quantidade (Compra)', '0'))
                sell_qty = safe_decimal(row.get('Quantidade (Venda)', '0'))
                buy_price = safe_decimal(row.get('Preço Médio (Compra)', '0'))
                sell_price = safe_decimal(row.get('Preço Médio (Venda)', '0'))
                
                asset = get_or_create_asset(ticker)
                
                if buy_qty > 0:
                    if not Transaction.objects.filter(asset=asset, date=d, quantity=buy_qty, transaction_type="buy").exists():
                        Transaction.objects.create(
                            asset=asset, transaction_type=Transaction.TransactionType.BUY,
                            quantity=buy_qty, price=buy_price, total_value=buy_qty * buy_price,
                            date=d, broker="B3", source=Transaction.Source.B3_IMPORT,
                            notes="Importado mensal xlsx"
                        )
                        stats['buys'] += 1
                        print(f"      [C] {ticker}: {buy_qty} @ R${buy_price}")

                if sell_qty > 0:
                    if not Transaction.objects.filter(asset=asset, date=d, quantity=sell_qty, transaction_type="sell").exists():
                        Transaction.objects.create(
                            asset=asset, transaction_type=Transaction.TransactionType.SELL,
                            quantity=sell_qty, price=sell_price, total_value=sell_qty * sell_price,
                            date=d, broker="B3", source=Transaction.Source.B3_IMPORT,
                            notes="Importado mensal xlsx"
                        )
                        stats['sells'] += 1
                        print(f"      [V] {ticker}: {sell_qty} @ R${sell_price}")

    if 'Proventos Recebidos' in xls.sheet_names:
        df_prov = pd.read_excel(xls, sheet_name='Proventos Recebidos')
        if not df_prov.empty:
            for _, row in df_prov.iterrows():
                prod = str(row.get('Produto', ''))
                if not prod or prod == 'nan': continue
                
                ticker = prod.split(' - ')[0].strip()
                if ticker not in KNOWN_ASSETS: continue
                
                d = parse_date_pt(row.get('Pagamento', ''))
                if not d: continue
                
                dt_str = str(row.get('Tipo de Evento', '')).lower()
                if "rendimento" in dt_str: dt = Dividend.DividendType.INCOME
                elif "juros" in dt_str or "jcp" in dt_str: dt = Dividend.DividendType.JCP
                else: dt = Dividend.DividendType.DIVIDEND
                
                val_total = safe_decimal(row.get('Valor líquido', '0'))
                qty = safe_decimal(row.get('Quantidade', '0'))
                
                if val_total > 0:
                    asset = get_or_create_asset(ticker)
                    if not Dividend.objects.filter(asset=asset, payment_date=d, total_value=val_total, dividend_type=dt).exists():
                        Dividend.objects.create(
                            asset=asset, dividend_type=dt,
                            value_per_unit=val_total / qty if qty > 0 else Decimal("0"), 
                            total_value=val_total, payment_date=d
                        )
                        stats['dividends'] += 1
                        print(f"      [D] {ticker}: {dt} R${val_total}")

    return stats


# ═══════════════════════════════════════════════════════════════
# PROCESSAMENTO ANUAL (VALIDACAO XLSX)
# ═══════════════════════════════════════════════════════════════

def process_annual_report(filepath, year):
    print(f"  [>] Validando Consolidado Anual: {year} (XLSX)")
    try:
        xls = pd.ExcelFile(filepath)
    except Exception as e:
        print(f"Erro ao abrir Excel: {e}")
        return

    found_assets = set()
    
    for sheet in xls.sheet_names:
        if not sheet.startswith('Posição - '): continue
        
        df = pd.read_excel(xls, sheet_name=sheet)
        if df.empty: continue
        
        for _, row in df.iterrows():
            prod = str(row.get('Produto', ''))
            if not prod or prod == 'nan': continue
            
            if sheet == 'Posição - Tesouro Direto':
                name = prod.strip()
                asset = get_or_create_asset("", name=name, asset_type="fixed_income")
                qty = safe_decimal(row.get('Quantidade', '0'))
                val_atualizado = safe_decimal(row.get('Valor Atualizado', '0'))
                
                curr_qty = current_quantity(asset, date(year, 12, 31))
                if curr_qty != qty:
                    diff = qty - curr_qty
                    ttype = "buy" if diff > 0 else "sell"
                    price_unit = val_atualizado / qty if qty > 0 else Decimal("1")
                    Transaction.objects.create(
                        asset=asset, date=date(year, 12, 31), transaction_type=ttype,
                        quantity=abs(diff), price=price_unit, total_value=abs(diff) * price_unit,
                        broker="B3 Ajuste Anual", source=Transaction.Source.B3_IMPORT,
                        notes="Ajuste Tesouro Direto"
                    )
                
                asset.is_active = True
                asset.current_price = val_atualizado / qty if qty > 0 else Decimal("0")
                asset.save()
                found_assets.add(asset.id)
                
            elif sheet == 'Posição - Renda Fixa' or sheet == 'Posição - CDB':
                name = prod.strip()
                asset = get_or_create_asset("", name=name, asset_type="fixed_income")
                qty = safe_decimal(row.get('Quantidade', '0'))
                val_atualizado = safe_decimal(row.get('Valor Atualizado', '0'))
                
                curr_qty = current_quantity(asset, date(year, 12, 31))
                if curr_qty != qty:
                    diff = qty - curr_qty
                    ttype = "buy" if diff > 0 else "sell"
                    price_unit = val_atualizado / qty if qty > 0 else Decimal("1")
                    Transaction.objects.create(
                        asset=asset, date=date(year, 12, 31), transaction_type=ttype,
                        quantity=abs(diff), price=price_unit, total_value=abs(diff) * price_unit,
                        broker="B3 Ajuste Anual", source=Transaction.Source.B3_IMPORT,
                        notes="Ajuste CDB"
                    )
                
                asset.is_active = True
                asset.current_price = val_atualizado / qty if qty > 0 else Decimal("0")
                asset.save()
                found_assets.add(asset.id)
                
            else:
                ticker = prod.split(' - ')[0].strip()
                if ticker not in KNOWN_ASSETS: continue
                asset = get_or_create_asset(ticker)
                qty = safe_decimal(row.get('Quantidade', '0'))
                
                preco_fechamento = safe_decimal(row.get('Preço de Fechamento', '0'))
                if preco_fechamento > 0:
                    asset.current_price = preco_fechamento
                    
                curr_qty = current_quantity(asset, date(year, 12, 31))
                if curr_qty != qty:
                    diff = qty - curr_qty
                    ttype = "buy" if diff > 0 else "sell"
                    price_unit = preco_fechamento if preco_fechamento > 0 else Decimal("1")
                    Transaction.objects.create(
                        asset=asset, date=date(year, 12, 31), transaction_type=ttype,
                        quantity=abs(diff), price=price_unit, total_value=abs(diff)*price_unit,
                        broker="B3 Ajuste Anual", source=Transaction.Source.B3_IMPORT,
                        notes="Ajuste de Divergência Anual"
                    )
                    print(f"      [AVISO] {ticker}: esperado={qty}, calc={curr_qty}. Aplicando ajuste!")
                    
                asset.is_active = True
                asset.save()
                found_assets.add(asset.id)

    for asset in Asset.objects.filter(is_active=True):
        if asset.id not in found_assets:
            curr_qty = current_quantity(asset, date(year, 12, 31))
            if curr_qty > 0:
                Transaction.objects.create(
                    asset=asset, date=date(year, 12, 31), transaction_type="sell",
                    quantity=curr_qty, price=asset.current_price or asset.average_price, 
                    total_value=curr_qty * (asset.current_price or asset.average_price),
                    broker="B3 Ajuste Zerado", source=Transaction.Source.B3_IMPORT,
                    notes="Ativo nao consta no relatorio anual"
                )
            asset.is_active = False
            asset.save()


if __name__ == "__main__":
    print("=" * 60)
    print("  IMPORTADOR B3 v7 - Kallia Financas (XLSX)      ")
    print("=" * 60)

    anos = sorted([d for d in os.listdir(XLSX_DIR) if os.path.isdir(os.path.join(XLSX_DIR, d))])
    
    for ano in anos:
        print(f"\n{'#' * 60}")
        print(f"  PROCESSANDO ANO {ano}")
        print(f"{'#' * 60}")
        
        ano_dir = os.path.join(XLSX_DIR, ano)
        mensais = sorted(glob.glob(os.path.join(ano_dir, f"relatorio-consolidado-mensal-{ano}-*.xlsx")))
        anual = glob.glob(os.path.join(ano_dir, f"relatorio-consolidado-anual-{ano}.xlsx"))
        
        for mes_path in mensais:
            process_monthly_report(mes_path)
            
        if anual:
            print("")
            process_annual_report(anual[0], int(ano))
            
    print("\n" + "=" * 60)
    print("  RESUMO FINAL")
    print("=" * 60)
    print(f"  Ativos:      {Asset.objects.count()}")
    print(f"  Operacoes:   {Transaction.objects.count()}")
    print(f"  Proventos:   {Dividend.objects.count()}")
    print("\n  Sucesso!")

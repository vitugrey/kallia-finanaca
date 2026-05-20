"""
Script de migração: BudgetFlow (db antigo) → Kallia Budget (db novo).

Tabelas migradas:
  budgetflow_category  →  budget_category
  budgetflow_transaction  →  budget_transaction

Mapeamento de campos:
  budgetflow_transaction.transaction_type: 'Income' → 'income', 'Expense' → 'expense'
  is_fixed_income: campo novo, derivado de is_fixed_expense quando type == income
  Categorias: recriadas com o mesmo nome. IDs podem mudar — uso mapeamento por nome.

Uso:
  uv run python scripts/migrate_budget.py
  (execute na raiz do projeto)
"""
import os
import sys
import sqlite3
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from budget.models import Category, Transaction

OLD_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db_anterior.sqlite3')


def migrate():
    conn = sqlite3.connect(OLD_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ────────────────────────────────────────────────
    # 1. Categorias
    # ────────────────────────────────────────────────
    print("📂 Migrando categorias...")
    cursor.execute("SELECT id, name, description FROM budgetflow_category ORDER BY id")
    old_categories = cursor.fetchall()

    # Mapa: old_id → objeto Category novo
    category_map = {}
    cat_created = 0
    cat_skipped = 0

    for row in old_categories:
        cat, created = Category.objects.get_or_create(
            name=row['name'],
            defaults={'description': row['description'] or ''}
        )
        category_map[row['id']] = cat
        if created:
            cat_created += 1
        else:
            cat_skipped += 1

    print(f"   ✅ {cat_created} criadas, {cat_skipped} já existiam.")

    # ────────────────────────────────────────────────
    # 2. Transações
    # ────────────────────────────────────────────────
    print("💸 Migrando transações...")
    cursor.execute("""
        SELECT id, description, value, date, is_credit, is_fixed_expense,
               transaction_type, created_at, updated_at, category_id
        FROM budgetflow_transaction
        ORDER BY date, id
    """)
    old_transactions = cursor.fetchall()

    tx_created = 0
    tx_skipped = 0
    tx_errors = 0

    for row in old_transactions:
        # Normalizar tipo: 'Income'/'income' → 'income', 'Expense'/'expense' → 'expense'
        raw_type = (row['transaction_type'] or '').strip().lower()
        if raw_type == 'income':
            tx_type = Transaction.TransactionType.INCOME
        else:
            tx_type = Transaction.TransactionType.EXPENSE

        is_fixed_expense = bool(row['is_fixed_expense']) and tx_type == Transaction.TransactionType.EXPENSE
        is_fixed_income = bool(row['is_fixed_expense']) and tx_type == Transaction.TransactionType.INCOME

        cat = category_map.get(row['category_id'])
        if not cat:
            print(f"   ⚠️  Transação id={row['id']} sem categoria válida — pulando.")
            tx_errors += 1
            continue

        # Evita duplicatas: mesmo description + value + date + tipo
        exists = Transaction.objects.filter(
            description=row['description'],
            value=Decimal(str(row['value'])),
            date=row['date'],
            transaction_type=tx_type,
        ).exists()

        if exists:
            tx_skipped += 1
            continue

        try:
            Transaction.objects.create(
                description=row['description'],
                value=Decimal(str(row['value'])),
                category=cat,
                date=row['date'],
                is_credit=bool(row['is_credit']),
                is_fixed_expense=is_fixed_expense,
                is_fixed_income=is_fixed_income,
                transaction_type=tx_type,
            )
            tx_created += 1
        except Exception as e:
            print(f"   ❌ Erro na transação id={row['id']}: {e}")
            tx_errors += 1

    conn.close()

    print(f"   ✅ {tx_created} criadas, {tx_skipped} já existiam, {tx_errors} erros.")
    print()
    print("🎉 Migração concluída!")
    print(f"   Categorias no novo banco: {Category.objects.count()}")
    print(f"   Transações no novo banco: {Transaction.objects.count()}")


if __name__ == '__main__':
    migrate()

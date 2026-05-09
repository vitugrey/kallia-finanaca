from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "value",
        "category",
        "transaction_type",
        "date",
        "is_credit",
        "is_fixed_expense",
        "is_fixed_income",
    )
    list_filter = ("transaction_type", "category", "is_credit", "is_fixed_expense", "is_fixed_income")
    search_fields = ("description",)
    date_hierarchy = "date"
    ordering = ("-date",)

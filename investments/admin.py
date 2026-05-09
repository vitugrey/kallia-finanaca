from django.contrib import admin

from .models import Asset, Category, Dividend, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("ticker", "name", "asset_type", "category", "is_active")
    list_filter = ("asset_type", "category", "is_active")
    search_fields = ("ticker", "name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "transaction_type",
        "quantity",
        "price",
        "total_value",
        "date",
        "broker",
        "source",
    )
    list_filter = ("transaction_type", "source", "broker", "asset__asset_type")
    search_fields = ("asset__ticker", "asset__name", "notes")
    date_hierarchy = "date"
    ordering = ("-date",)


@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "dividend_type",
        "total_value",
        "value_per_unit",
        "payment_date",
        "ex_date",
    )
    list_filter = ("dividend_type", "asset__asset_type")
    search_fields = ("asset__ticker", "asset__name")
    date_hierarchy = "payment_date"
    ordering = ("-payment_date",)

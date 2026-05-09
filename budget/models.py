from django.db import models


class Category(models.Model):
    """Categoria para organizar transações (ex: Alimentação, Transporte, Salário)."""

    name = models.CharField("Nome", max_length=100, unique=True)
    description = models.TextField("Descrição", blank=True, default="")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Registro de uma transação financeira (receita ou despesa)."""

    class TransactionType(models.TextChoices):
        INCOME = "income", "Receita"
        EXPENSE = "expense", "Despesa"

    description = models.CharField("Descrição", max_length=255)
    value = models.DecimalField("Valor", max_digits=12, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Categoria",
    )
    date = models.DateField("Data")
    is_credit = models.BooleanField("É crédito?", default=False)
    is_fixed_expense = models.BooleanField("Despesa fixa?", default=False)
    is_fixed_income = models.BooleanField("Receita fixa?", default=False)
    transaction_type = models.CharField(
        "Tipo",
        max_length=10,
        choices=TransactionType.choices,
        default=TransactionType.EXPENSE,
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        sinal = "+" if self.transaction_type == self.TransactionType.INCOME else "-"
        return f"{self.description} ({sinal} R${self.value})"

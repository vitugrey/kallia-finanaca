from django.db import models
from django.db.models import Sum, Q
from decimal import Decimal


class Category(models.Model):
    """Categoria de ativo (ex: Ações, FIIs, Renda Fixa, ETFs, Criptomoedas)."""

    name = models.CharField("Nome", max_length=100, unique=True)
    description = models.TextField("Descrição", blank=True, default="")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Asset(models.Model):
    """
    Ficha de identificação de um ativo.

    A posição atual (quantidade, preço médio) é calculada
    automaticamente a partir das transações importadas da B3.
    """

    class AssetType(models.TextChoices):
        STOCK = "stock", "Ação"
        FII = "fii", "Fundo Imobiliário"
        ETF = "etf", "ETF"
        BDR = "bdr", "BDR"
        FIXED_INCOME = "fixed_income", "Renda Fixa"
        CRYPTO = "crypto", "Criptomoeda"
        OTHER = "other", "Outro"

    ticker = models.CharField(
        "Ticker",
        max_length=20,
        blank=True,
        default="",
        help_text="Código do ativo (ex: PETR4, XPLG11). Pode ficar vazio para renda fixa.",
    )
    name = models.CharField("Nome", max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="assets",
        verbose_name="Categoria",
    )
    asset_type = models.CharField(
        "Tipo do Ativo",
        max_length=15,
        choices=AssetType.choices,
        default=AssetType.STOCK,
    )
    current_price = models.DecimalField("Preço Atual", max_digits=12, decimal_places=4, default=Decimal('0'))
    is_active = models.BooleanField("Ativo em carteira?", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Ativo"
        verbose_name_plural = "Ativos"
        ordering = ["asset_type", "ticker", "name"]

    def __str__(self):
        if self.ticker:
            return f"{self.ticker} – {self.name}"
        return self.name

    @property
    def quantity(self):
        """Quantidade atual em carteira (compras - vendas)."""
        buys = self.transactions.filter(
            transaction_type=Transaction.TransactionType.BUY
        ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")
        sells = self.transactions.filter(
            transaction_type=Transaction.TransactionType.SELL
        ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")
        return buys - sells

    @property
    def average_price(self):
        """
        Preço médio da posição ATUAL.
        Reconstrói a carteira transação a transação em ordem cronológica.
        Quando a posição vai a zero (venda total), reseta o custo — 
        qualquer compra posterior começa uma nova posição.
        """
        transactions = self.transactions.order_by('date', 'id')
        position_qty = Decimal('0')
        position_cost = Decimal('0')
        for t in transactions:
            if t.transaction_type == Transaction.TransactionType.BUY:
                position_qty += t.quantity
                position_cost += t.total_value
            elif t.transaction_type == Transaction.TransactionType.SELL:
                if position_qty > 0:
                    # Reduz custo proporcionalmente à quantidade vendida
                    cost_per_unit = position_cost / position_qty
                    position_cost -= cost_per_unit * t.quantity
                position_qty -= t.quantity
                # Se zerou (ou ficou negativo por ajuste), reseta tudo
                if position_qty <= 0:
                    position_qty = Decimal('0')
                    position_cost = Decimal('0')

        if position_qty > 0:
            return (position_cost / position_qty).quantize(Decimal('0.01'))
        return Decimal('0')

    @property
    def total_invested(self):
        """Valor total investido (soma das compras - soma das vendas)."""
        buys = self.transactions.filter(
            transaction_type=Transaction.TransactionType.BUY
        ).aggregate(total=Sum("total_value"))["total"] or Decimal("0")
        sells = self.transactions.filter(
            transaction_type=Transaction.TransactionType.SELL
        ).aggregate(total=Sum("total_value"))["total"] or Decimal("0")
        return buys - sells

    @property
    def total_dividends(self):
        """Total de proventos recebidos deste ativo (histórico completo)."""
        return self.dividends.aggregate(total=Sum("total_value"))["total"] or Decimal("0")

    @property
    def ttm_dividends(self):
        """Total de proventos recebidos nos últimos 12 meses."""
        from datetime import date, timedelta
        cutoff = date.today() - timedelta(days=365)
        return self.dividends.filter(payment_date__gte=cutoff).aggregate(
            total=Sum("total_value")
        )["total"] or Decimal("0")

    @property
    def ttm_dividends_monthly(self):
        """Média mensal de proventos dos últimos 12 meses."""
        return (self.ttm_dividends / 12).quantize(Decimal("0.01"))


class Transaction(models.Model):
    """
    Registro de operação de compra ou venda.

    Pode ser lançada manualmente ou importada de extratos (B3, Rico).
    """

    class TransactionType(models.TextChoices):
        BUY = "buy", "Compra"
        SELL = "sell", "Venda"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        B3_IMPORT = "b3_import", "Importação B3"
        RICO_IMPORT = "rico_import", "Importação Rico"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Ativo",
    )
    transaction_type = models.CharField(
        "Tipo",
        max_length=5,
        choices=TransactionType.choices,
    )
    quantity = models.DecimalField(
        "Quantidade",
        max_digits=14,
        decimal_places=4,
    )
    price = models.DecimalField(
        "Preço Unitário",
        max_digits=14,
        decimal_places=4,
    )
    total_value = models.DecimalField(
        "Valor Total",
        max_digits=14,
        decimal_places=2,
        help_text="Calculado automaticamente (quantidade × preço).",
    )
    date = models.DateField("Data da Operação")
    broker = models.CharField(
        "Corretora",
        max_length=50,
        blank=True,
        default="Rico",
    )
    notes = models.TextField("Observações", blank=True, default="")
    source = models.CharField(
        "Origem",
        max_length=15,
        choices=Source.choices,
        default=Source.MANUAL,
        help_text="Como essa operação foi registrada.",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Operação"
        verbose_name_plural = "Operações"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        tipo = "C" if self.transaction_type == self.TransactionType.BUY else "V"
        return f"[{tipo}] {self.asset} – {self.quantity} × R${self.price}"

    def save(self, *args, **kwargs):
        """Calcula o valor total automaticamente antes de salvar."""
        if self.quantity and self.price:
            self.total_value = self.quantity * self.price
        super().save(*args, **kwargs)


class Dividend(models.Model):
    """
    Registro de provento recebido (dividendos, JCP, rendimentos, amortização).

    Permite acompanhar rendimentos mês a mês.
    """

    class DividendType(models.TextChoices):
        DIVIDEND = "dividend", "Dividendo"
        JCP = "jcp", "Juros sobre Capital Próprio"
        INCOME = "income", "Rendimento"
        AMORTIZATION = "amortization", "Amortização"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="dividends",
        verbose_name="Ativo",
    )
    dividend_type = models.CharField(
        "Tipo de Provento",
        max_length=15,
        choices=DividendType.choices,
        default=DividendType.DIVIDEND,
    )
    value_per_unit = models.DecimalField(
        "Valor por Unidade",
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Valor do provento por cota/ação.",
    )
    total_value = models.DecimalField(
        "Valor Total",
        max_digits=14,
        decimal_places=2,
        help_text="Valor total recebido.",
    )
    ex_date = models.DateField(
        "Data Ex",
        null=True,
        blank=True,
        help_text="Data em que o ativo fica 'ex-provento'.",
    )
    payment_date = models.DateField(
        "Data de Pagamento",
        help_text="Data em que o provento foi pago.",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Provento"
        verbose_name_plural = "Proventos"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.asset} – {self.get_dividend_type_display()} R${self.total_value}"

from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('importar/', views.import_report, name='import_report'),
    path('dividendos/', views.dividends_charts, name='dividends_charts'),
    path('patrimonio/', views.patrimony_charts, name='patrimony_charts'),
    path('ativos/', views.asset_list, name='asset_list'),
    path('api/update-prices/', views.update_prices_yfinance, name='update_prices'),
]

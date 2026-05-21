from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transacoes/', views.transaction_list, name='transaction_list'),
    path('transacoes/nova/', views.create_transaction, name='create_transaction'),
    path('transacoes/<int:transaction_id>/editar/', views.edit_transaction, name='edit_transaction'),
    path('categorias/nova/', views.create_category, name='create_category'),
]

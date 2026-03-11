from django.urls import path
from . import views

urlpatterns = [
    path('', views.llista_partides, name='llista_partides'),
    path('pujar/', views.pujar_partida, name='pujar_partida'),
    path('partida/<int:partida_id>/', views.detall_partida, name='detall_partida'),
    path('partida/<int:partida_id>/esborrar/', views.esborrar_partida, name='esborrar_partida'),
    path('nova/', views.nova_partida, name='nova_partida'),
    path('partida/<int:partida_id>/editar/', views.nova_partida, name='editar_partida'),
    path('nova/', views.nova_partida, name='nova_partida'),
    path('registre/', views.registre, name='registre'),
    path('importar/', views.importar_pgn, name='importar_pgn'),
    path('comentari/<int:comentari_id>/esborrar/', views.esborrar_comentari, name='esborrar_comentari'),
    path('comentari/<int:comentari_id>/editar/', views.editar_comentari, name='editar_comentari'),
]
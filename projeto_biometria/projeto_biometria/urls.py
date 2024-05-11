from django.urls import path
from app_biometria import views

urlpatterns = [
    #rota, view responsavel, nome de referencia
    path('home/', views.home, name='home'),
    # localhost/usuarios
    path('usuarios/', views.usuarios, name='listagem_usuarios'),
    #localhost/cadastro
    path('cadastro/', views.cadastro, name='cadastro_usuarios'),
    #localhost/login
    path('', views.login, name='login'),
    #localhost/login
    path('loginUsuario/', views.loginUsuario, name='login_usuarios')
    
]
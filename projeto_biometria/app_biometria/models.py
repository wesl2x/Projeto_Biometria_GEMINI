from django.db import models

class Usuario(models.Model):
    idUsuario = models.AutoField(primary_key=True)
    nome = models.TextField(max_length=255)
    idade = models.IntegerField()
    cpf = models.IntegerField()
    caminhoImagem = models.TextField(max_length=500)
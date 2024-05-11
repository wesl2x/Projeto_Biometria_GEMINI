from django.shortcuts import render
from .models import Usuario
from PIL import Image
import os
import cv2 as cv
import google.generativeai as genai
import time

def login(request):
    return render(request, 'biometria/login.html') 

def home(request):
    return render(request, 'biometria/home.html')
 
def cadastro(request):
    return render(request, 'biometria/cadastro.html') 

def loginUsuario(request):
    cpfLogin = request.POST.get('cpf')
    usuarioPesquisa = Usuario.objects.filter(cpf=cpfLogin)

    if usuarioPesquisa.exists():
        usuario = Usuario.objects.get(cpf=cpfLogin)
        #verifica se o usuario foi o que foi definido para ser admin e redireciona ele para a home
        if(cpfLogin == '12345678901'):
            #Redireciona papra a tela de home o usuario definido como admin 
            return render(request,'biometria/home.html')
        else:
            #Caso não valida a biometria do usuario
            #capturando a camera 0 no meu caso do notbook 
            camera = cv.VideoCapture(0)

            #verificando se a camera foi encontrada
            if not camera.isOpened():
                contexto = {'mostrar_alerta': True, 'mensagem': 'Error: Não foi possivel abrir a camera'}
                #Retornar opara a tela de login
                return render(request,'biometria/login.html', contexto)
                exit()

            rodando = True  
            #valida a biometria do usuario
            #Pasta para armazenar a imagem capturada da camera
            imagem_folder = 'screenshots/'
            jpeg_quality = 90 
            image_path = ""
            while rodando:
                # Captura um frame
                status, frame = camera.read()
                # usa a letra q para termina e capturar a imagem 
                if not status or cv.waitKey(1) & 0xff == ord('q'):
                    rodando = False
                    #monta o nome do arquivo capturado
                    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
                    folderWrite = imagem_folder+str(time.strftime('%Y-%m-%d'))
                    
                    #Verifica se possui a pasta cadastrada
                    if os.path.exists(folderWrite):
                        print(timestamp)
                    else:
                        print(f'Pasta não criada {folderWrite}')
                        #Cria a pasta
                        os.makedirs(folderWrite)
                    
                    #realizando a juncao do caminho com o nome da nova imagem usando o tempo para diferenciar uma imagem da outra
                    image_path = os.path.join(folderWrite, f'image_{timestamp}.jpg') 
                    #salvando a imagem na pasta
                    cv.imwrite(image_path, frame, [int(cv.IMWRITE_JPEG_QUALITY), jpeg_quality])
                #mostra o frame da camera na tela para visualização
                cv.imshow("Camera", frame)
            #Finaliza para nao ficar consumindo    
            camera.release()
            cv.destroyAllWindows()

            retorno = validar_imagem_GEMINI(image_path, usuario.caminhoImagem)

            #Caso a Resposta seja positiva informa que a face foi detectada na nossa base e se não pergunta se deseja cadastrar para validar novamente
            if retorno.__contains__('SIM'):
                #Redireciona papra a tela de home
                return render(request,'biometria/home.html')
            else:
                contexto = {'mostrar_alerta': True, 'mensagem': 'Poxa, infelismente não encontramos a Face em nossos cadastros'}
                return render(request,'biometria/login.html', contexto)
    else:
        contexto = {'mostrar_alerta': True, 'mensagem': 'Erro ao realizar a ação. Usuário não encontrado.'}
        #Retornar os dados para a pagina de listagem de usuarios
        return render(request,'biometria/login.html', contexto)

def usuarios(request):

    if(request.method == "POST"):
        #instancia da classe usuario
        novo_usuario = Usuario()

        #recebendo os dados da tela
        novo_usuario.nome = request.POST.get('nome')
        novo_usuario.idade = request.POST.get('idade')
        novo_usuario.cpf = request.POST.get('cpf')

        file = request.FILES['foto']
        novo_usuario.caminhoImagem = handle_uploaded_file(file, novo_usuario.cpf, novo_usuario.nome)

        #salvando no banco de dados
        novo_usuario.save()
    

    #Exibir todos os nossos usuarios
    usuarios = []

    

    for usu in Usuario.objects.all():
        link = usu.caminhoImagem.replace('projeto_biometria/app_biometria','http://127.0.0.1:8000/')
        usu.caminhoImagem = link
        usuarios.append(usu)



    context = {'usuarios': usuarios} 
    #Retornar os dados para a pagina de listagem de usuarios
    return render(request,'biometria/usuarios.html', context)

def handle_uploaded_file(f, cpf, nome):
    #carrega a imagem 
    img = Image.open(f)

    #defini onde sera salva
    imagem_folder = 'projeto_biometria/app_biometria/static/imagem/'

    #junta o local de salvar com o nome do arquivo contendo o cpf
    image_path = os.path.join(imagem_folder, f'image_{cpf}_{nome}.jpg')

    #salvav a imagem no caminho 
    img.save(image_path,format='JPEG', quality=90)

    #retorna o caminho da imagegm para ser salva no banco de dados
    return image_path

def verificar_nome_na_lista(lista_imagens, nome_procurado):
#verifica se o nome esta na lista

  for nome_imagem in lista_imagens:
    if nome_procurado.lower() in nome_imagem.lower():
      return nome_imagem  # Retorna o nome da imagem encontrado

  return None  # Retorna None se o nome não for encontrado

def validar_imagem_GEMINI(image_path_capturada, caminhoImagemCadastro):
    #Inserindo a chave da api
    GOOGLE_API_KEY = "CHAVE_API_GEMINI"
    genai.configure(api_key=GOOGLE_API_KEY)

    #Criando a lista de imagem
    lista_imagens = []

    # Configurando o GEMINI
    generation_config = {
    "candidate_count": 1,
    "temperature": 0.5
    }

    safety_settings = {
        "HARASSMENT": "BLOCK_NONE",
        "HATE": "BLOCK_NONE",
        "SEXUAL": "BLOCK_NONE",
        "DANGEROUS": "BLOCK_NONE"
    }

    #Iniciando o Modelo
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                generation_config=generation_config, 
                                safety_settings=safety_settings)
    
    #Carrega a imagem captura para ser utilizada
    imagemCapturada = Image.open(image_path_capturada)
    imagemCadastro = Image.open(caminhoImagemCadastro)

    #Carregando o historico de imagem para comparacao
    result = model.start_chat(history=[{
      "role": "user",
      "parts": [genai.upload_file(imagemCadastro.filename)]
    },{
      "role": "user",
      "parts": [genai.upload_file(imagemCapturada.filename)]
    }])

    #Realiza as solicitacao para o GEMINI para saber se nas imagens sao a mesma pessoa
    resposta = result.send_message(["verifique se as imagens enviadas sao da mesma pessoa, responda SIM caso seja a mesma ou Não se nao for."])
    resposta.resolve()

    return resposta.text
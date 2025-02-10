import os

class Config:
    # Chave secreta para sessões e CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui')
    
    # Configuração do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://bruno_master:FYdi6BeYH3jRL0YOqt4XmInNwUOJlr0S@dpg-cul7u3jv2p9s73a4ru2g-a.oregon-postgres.render.com/test_4jyn')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Desabilita o rastreamento de modificações para economizar recursos
    
    # Configuração da pasta de uploads
    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Configurações adicionais (se necessário)
    # MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de upload para arquivos de até 16MB

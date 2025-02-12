from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pytz  # Para manipulação de fusos horários
from config import Config
from flask_migrate import Migrate
from flask import send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import LargeBinary
from flask import send_file
import io
from flask import flash
from PyPDF2 import PdfFileReader
from io import BytesIO
from pytz import timezone
from datetime import datetime
# Inicializa o Flask
app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ars291576@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')  # Caminho absoluto para o diretório de uploads
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'txt'}  # Adicione as extensões permitidas, se necessário
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {"options": "-c timezone=America/Sao_Paulo"}
}

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)

# Inicializa o Migrate após a definição de app e db
migrate = Migrate(app, db)

def get_sao_paulo_time():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)  # Removendo a conversão para UTC

# Modelo do Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(14), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Senha em texto simples
    role = db.Column(db.String(10), nullable=False, default='user')  # Tipo de usuário com valor padrão
    user_type = db.Column(db.String(20))  # Adiciona a coluna 'user_type'
    regiao = db.Column(db.String(100))  # Novo campo
    

    # Relacionamento com os arquivos PDF
    pdf_files = db.relationship('PDFFile', back_populates='user', lazy=True)

    # Método de verificação de senha (sem hash)
    def check_password(self, password):
        return self.password == password  # Comparação direta com a senha em texto simples
    
    
@app.route('/send_pdf', methods=['GET', 'POST'])
def send_pdf_to_user():
    if not session.get('user_id') or not is_master(session['user_id']):
        return redirect(url_for('login'))  # Garantir que apenas o master tenha acesso

    if request.method == 'POST':
        user_id = request.form['user_id']
        file = request.files['file']

        # Verifica se um arquivo foi enviado e se a extensão é válida
        if file and file.filename.endswith('.pdf'):
            # Gerar nome seguro para o arquivo
            filename = secure_filename(file.filename)
            file_type = request.form.get("file_type")

            if not file_type:
                return "Tipo de arquivo não fornecido", 400  # Retorna um erro se o tipo não for enviado

            # Lê o conteúdo do arquivo PDF como dados binários
            file_data = file.read()
            
            tz = pytz.timezone('America/Sao_Paulo')
            uploaded_at = datetime.now(tz)  # Define o horário ajustado

            tz = pytz.timezone('America/Sao_Paulo')
    # Cria um novo registro no banco com os dados binários

            # Cria um novo objeto PDFFile com os dados binários
            new_pdf = PDFFile(
                filename=filename,
                user_id=session['user_id'],
                file_type='pdf',
                file_data=file_data,
                uploaded_at=get_sao_paulo_time()  # Define o horário de São Paulo na criação
            )
            db.session.add(new_pdf)
            db.session.commit()

            return redirect(url_for('master_dashboard'))

    # Obter todos os usuários para preencher o select
    users = User.query.all()

    return render_template('send_pdf.html', users=users)


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Se não estiver logado, redireciona para o login
    
    user = User.query.get(session['user_id'])  # Obtém o usuário da sessão
    
    if request.method == 'POST':  # Se o método for POST, significa que o usuário está tentando salvar as alterações
        # Obtém os novos valores do formulário
        user.name = request.form['name']
        user.email = request.form['email']
        user.cnpj = request.form['cnpj']
        
        # Verifica se a senha atual está correta antes de atualizar
        current_password = request.form['confirm_password']
        if user.password != current_password:  # Comparação direta com a senha em texto simples
            return "A senha atual está incorreta", 400  # Retorna um erro se a senha atual for inválida
        
        # Apenas atualiza a senha se o campo da nova senha não estiver vazio
        new_password = request.form['password']
        if new_password:
            user.password = new_password  # Atualiza a senha com a nova, se fornecida
        
        db.session.commit()  # Salva as alterações no banco de dados
        
        return redirect(url_for('perfil'))  # Redireciona de volta para o perfil
    
    return render_template('perfil.html', user=user)  # Exibe a página de perfil com as informações do usuário


# Rota de validação de senha para AJAX
@app.route('/validar-senha', methods=['POST'])
def validar_senha():
    user = User.query.get(session['user_id'])  # Obtém o usuário da sessão
    data = request.get_json()
    current_password = data.get('confirm_password')
    
    # Verifica se a senha fornecida é a mesma do usuário
    if user.password == current_password:
        return jsonify(success=True)  # Senha está correta
    else:
        return jsonify(success=False)  # Senha está incorreta
    

# Modelo de Arquivo PDF
class PDFFile(db.Model):
    __tablename__ = 'pdf_file'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    file_type = db.Column(db.String(50), nullable=False, default='pdf')
    first_viewed_at = db.Column(db.DateTime)
    file_data = db.Column(db.LargeBinary)  # Coluna para armazenar o conteúdo binário do arquivo PDF
    
    uploaded_at = db.Column(db.DateTime(timezone=True), default=get_sao_paulo_time)

    # Relacionamento com o usuário
    user = db.relationship('User', back_populates='pdf_files')

    def __init__(self, filename, user_id, file_type='pdf', file_data=None, first_viewed_at=None, uploaded_at=None):
        self.filename = filename
        self.user_id = user_id
        self.file_type = file_type
        self.file_data = file_data
        self.first_viewed_at = first_viewed_at
        self.uploaded_at = uploaded_at
        
    # Função para verificar se o usuário é um "master"
def is_master(user_id):
    # Verifica o papel do usuário no banco de dados
    user = User.query.get(user_id)
    return user and user.role == 'master'

# Criar tabelas se não existirem
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/uploads/<file_type>/<filename>')
def uploaded_file_by_type(file_type, filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_type, filename)
    print(f"Attempting to access file: {filepath}")  # Verifica o caminho do arquivo
    return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Inicializa a variável de erro

    if request.method == 'POST':
        cnpj = request.form['cnpj']
        password = request.form['password']
        user = User.query.filter_by(cnpj=cnpj).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role

            # Redireciona para o dashboard
            if user.role == 'master':
                return redirect(url_for('master_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            error = True  # Se as credenciais estiverem erradas, define o erro

    return render_template('login.html', error=error)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])

    # Se o usuário for master, redireciona para a master_dashboard
    if user.role == 'master':
        return redirect(url_for('master_dashboard'))
    
    # Filtra os arquivos do usuário comum
    pdf_files = PDFFile.query.filter_by(user_id=user.id).all()

    # Busca os arquivos enviados pelo master (agora de forma dinâmica)
    master_user = User.query.filter_by(role='master').first()
    if master_user:
        master_files = PDFFile.query.filter_by(user_id=master_user.id).all()
    else:
        master_files = []

    # Passa os dados para o template
    return render_template('dashboard.html', user=user, pdf_files=pdf_files, master_files=master_files)


@app.route('/master_dashboard', methods=['GET', 'POST'])
def master_dashboard():
    # Verifique se o usuário está logado
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redireciona para login caso não esteja autenticado
    
    user = User.query.get(session['user_id'])
    
    tz = pytz.timezone('America/Sao_Paulo')

    # Verifique se o usuário logado tem o papel "master"
    if user.role != 'master':
        return "Acesso negado", 403  # Se o usuário não for "master", retorna erro 403
    
    if request.method == 'POST':
        # Lógica de processamento de envio de arquivo
        file = request.files.get('file')  # Obtém o arquivo do formulário

        if not file:
            return "Nenhum arquivo enviado", 400  # Caso o arquivo não tenha sido enviado
        
        file_type = request.form.get('file_type')  # Obtém o tipo do arquivo
        
        if file_type not in ['adiantamento', 'comissao', 'premio']:  # Verifica se o tipo é válido
            return "Tipo de arquivo inválido", 400  # Retorna erro se o tipo for inválido
        
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], file_type)

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)  # Cria a pasta caso não exista

        filename = file.filename
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Cria o registro do arquivo no banco de dados
        new_file = PDFFile(filename=filename, user_id=session['user_id'], file_type=file_type)
        db.session.add(new_file)
        db.session.commit()

        return redirect(url_for('master_dashboard'))  # Redireciona de volta para o painel master

    # Consulta todos os usuários (exceto master) com seus arquivos PDF associados
    user_pdf_data = (
        db.session.query(User, PDFFile)
        .join(PDFFile)
        .filter(User.role != 'master')  # Exclui arquivos de usuários master
        .all()
    )

    # Organiza os dados para facilitar a renderização
    user_pdf_data_processed = {}
    for user, pdf_file in user_pdf_data:
        if user.id not in user_pdf_data_processed:
            user_pdf_data_processed[user.id] = {
                'user': user,
                'pdf_files': []
            }
        user_pdf_data_processed[user.id]['pdf_files'].append({
            'id': pdf_file.id,
            'filename': pdf_file.filename,
            'first_viewed_at': pdf_file.first_viewed_at,
            'file_type': pdf_file.file_type,
            'uploaded_at': pdf_file.uploaded_at
        })

    # Retorna a página master_dashboard com os dados dos usuários e PDFs
    return render_template('master_dashboard.html', user=user, user_pdf_data=list(user_pdf_data_processed.values()))


@app.route('/info')
def user_info():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Obtém o usuário da sessão
    
    return render_template('info.html', user=user)  # Passa o usuário para o template


@app.route('/visualizar_pdf/<int:file_id>')
def visualizar_pdf(file_id):
    pdf_file = PDFFile.query.get(file_id)

    if not pdf_file or not pdf_file.file_data:
        return "Arquivo não encontrado ou corrompido", 404

    # Atualiza o campo first_viewed_at
    if not pdf_file.first_viewed_at:  # Só registra se for a primeira vez
        fuso_horario = timezone("America/Sao_Paulo")  # Ajuste para seu fuso
        pdf_file.first_viewed_at = datetime.now(fuso_horario)
        db.session.commit()

    return send_file(
        io.BytesIO(pdf_file.file_data),
        download_name=pdf_file.filename,
        mimetype='application/pdf'
    )

@app.route('/cadastrar_usuario')
def novo_usuario():
    return render_template('cadastrar_usuario.html')

@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        cnpj = request.form['cnpj']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        user_type = request.form['user_type']
        regiao = request.form['regiao']  # Obtendo o valor da região do formulário

        # Adiciona o novo usuário no banco de dados
        new_user = User(cnpj=cnpj, name=name, email=email, password=(password), role=role, user_type=user_type,regiao=regiao)
        db.session.add(new_user)
        db.session.commit()

        # Redireciona para outra página ou perfil
        return redirect(url_for('cadastrar_usuario'))

    return render_template('cadastrar_usuario.html')


MASTER_USER_ID = 44  # Definindo o ID do usuário master

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(url_for('dashboard'))
    
    file_type = request.form['file_type']
    if file_type not in ['adiantamento', 'comissao', 'premio']:
        return redirect(url_for('dashboard'))  # Ou exibe uma mensagem de erro
    
    # Lê os dados binários do arquivo
    file_data = file.read()
    
    tz = pytz.timezone('America/Sao_Paulo')
    uploaded_at = datetime.now(tz)  # Define o horário ajustado

    tz = pytz.timezone('America/Sao_Paulo')
    # Cria um novo registro no banco com os dados binários
    new_file = PDFFile(
    filename=secure_filename(file.filename),  # Nome seguro do arquivo
    user_id=session['user_id'],  # ID do usuário a quem o arquivo pertence
    file_type=file_type,  # Tipo do arquivo
    file_data=file_data,  # Dados binários do arquivo
    uploaded_at=uploaded_at
)

    db.session.add(new_file)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redireciona para o login se não estiver logado
    
    user = User.query.get(session['user_id'])
    
    # Verifica se o usuário logado é o 'master'
    if user.role != 'master':
        return "Acesso negado", 403  # Retorna erro 403 se não for master
    
    # Obtém todos os usuários cadastrados
    usuarios = User.query.all()
    
    print(usuarios)  # Verifique se a lista de usuários está sendo retornada corretamente
    
    # Passa os dados dos usuários para o template HTML
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get(user_id)  # Exemplo de busca no banco de dados

    if request.method == 'POST':
        # Se o tipo de usuário for "master", verifique a senha do master
        if user.role == 'master':
            master_password = request.form['master_password']
            
            # Verifique se a senha do master é válida
            # Substitua 'senha_do_master' pela lógica real de verificação de senha
            if master_password != 'senha_do_master':
                flash('Senha do master incorreta!', 'danger')
                return redirect(url_for('edit_user', user_id=user_id))  # Redireciona de volta à edição

        # Atualizar os dados do usuário no banco de dados
        user.name = request.form['name']
        user.email = request.form['email']
        user.cnpj = request.form['cnpj']
        user.password = request.form['password']
        user.role = request.form['role']
        user.user_type = request.form['user_type']
        
        db.session.commit()
        
        flash('Alterações salvas com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))  # Redireciona para a lista de usuários após salvar

    return render_template('edit_user.html', user=user)  # Passa o usuário para o template


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('Usuário excluído com sucesso!', 'success')
        else:
            flash('Usuário não encontrado!', 'danger')
    except Exception as e:
        db.session.rollback()  # Garante que a transação será revertida em caso de erro
        flash('Erro ao excluir o usuário!', 'danger')
        print(e)  # Imprime o erro no console para depuração

    return redirect(url_for('listar_usuarios'))  # Redireciona de volta para a lista de usuários

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/view_pdf/<int:pdf_id>')
def view_pdf(pdf_id):
    # Recupera o arquivo PDF do banco de dados
    pdf_file = PDFFile.query.get_or_404(pdf_id)

    # Verifica se o arquivo existe e se os dados do PDF estão presentes
    if not pdf_file.file_data:
        return "Arquivo não encontrado ou corrompido", 404
    
    tz = pytz.timezone('America/Sao_Paulo')
    uploaded_at = datetime.now(tz)  # Define o horário ajustado

    tz = pytz.timezone('America/Sao_Paulo')
    # Cria um novo registro no banco com os dados binários

    # Envia o arquivo PDF diretamente para o navegador, sem forçar o download
    return send_file(
        BytesIO(pdf_file.file_data),  # Cria o arquivo em memória a partir dos dados binários
        download_name=pdf_file.filename,  # Nome do arquivo
        as_attachment=False,  # Não força o download
        mimetype='application/pdf'  # Tipo de mídia do arquivo
    )
    
if __name__ == '__main__':
    app.run(debug=True)
    
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db
import sqlite3
from datetime import datetime, timedelta
import math

app = Flask(__name__)
init_db()


def get_db():
    """Retorna conexão com Foreign Keys habilitadas"""
    conn = sqlite3.connect('biblioteca.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.route('/')
def index():
    return redirect(url_for('usuarios'))

@app.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        matricula = request.form['matricula']
        tipo = request.form['tipo']
        email = request.form.get('email', None)

        try:
            c.execute('''
                INSERT INTO usuario (nome, matricula, tipo, email) 
                VALUES (?, ?, ?, ?)
            ''', (nome, matricula, tipo, email))
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            return f"Erro: {str(e)}", 400

    c.execute('SELECT * FROM usuario ORDER BY id DESC')
    usuarios = c.fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/livros', methods=['GET', 'POST'])
def livros():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        autores = request.form['autores']
        isbn = request.form.get('isbn', None)
        edicao = request.form.get('edicao', None)
        ano = request.form.get('ano', None)
        copias = int(request.form['copiasTotal'])

        c.execute('''
            INSERT INTO livro (titulo, autores, ISBN, edicao, ano, copiasTotal, copiasDisponiveis, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (titulo, autores, isbn, edicao, ano, copias, copias, 'DISPONIVEL'))
        conn.commit()

    c.execute('SELECT * FROM livro ORDER BY bookId DESC')
    livros = c.fetchall()
    conn.close()
    return render_template('livros.html', livros=livros)

@app.route('/emprestimos', methods=['GET', 'POST'])
def emprestimos():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        userId = request.form['userId']
        bookId = request.form['bookId']
        dias = 14 if request.form['tipo'] == 'ALUNO' else 30
        
        # Usar data/hora local
        hoje = datetime.now()
        dueDate = (hoje + timedelta(days=dias)).strftime('%Y-%m-%d')
        loanDate = hoje.strftime('%Y-%m-%d %H:%M:%S')

        # Verificar disponibilidade
        c.execute('SELECT copiasDisponiveis FROM livro WHERE bookId = ?', (bookId,))
        result = c.fetchone()
        if not result or result[0] <= 0:
            conn.close()
            return "Livro indisponível", 400

        try:
            c.execute('''
                INSERT INTO emprestimo (userId, bookId, loanDate, dueDate) 
                VALUES (?, ?, ?, ?)
            ''', (userId, bookId, loanDate, dueDate))

            c.execute('UPDATE livro SET copiasDisponiveis = copiasDisponiveis - 1 WHERE bookId = ?', (bookId,))
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            return f"Erro ao registrar empréstimo: {str(e)}", 400

    c.execute('''
        SELECT e.loanId, u.nome, l.titulo, e.loanDate, e.dueDate, e.status 
        FROM emprestimo e
        JOIN usuario u ON e.userId = u.id
        JOIN livro l ON e.bookId = l.bookId
        ORDER BY e.loanId DESC
    ''')
    emprestimos = c.fetchall()
    conn.close()
    return render_template('emprestimos.html', emprestimos=emprestimos)

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

@app.route('/api/relatorio/emprestimos')
def api_emprestimos():
    conn = get_db()
    c = conn.cursor()

    start = request.args.get('start')
    end = request.args.get('end')
    page = int(request.args.get('page', 1))
    per_page = 20  

    query = '''
        SELECT e.loanId, u.matricula, l.titulo, e.loanDate, e.dueDate, e.status
        FROM emprestimo e
        JOIN usuario u ON e.userId = u.id
        JOIN livro l ON e.bookId = l.bookId
        WHERE 1=1
    '''
    params = []

    if start:
        query += ' AND date(e.loanDate) >= date(?)'
        params.append(start)
    if end:
        query += ' AND date(e.loanDate) <= date(?)'
        params.append(end)

    count_query = query.replace('SELECT e.loanId, u.matricula, l.titulo, e.loanDate, e.dueDate, e.status', 'SELECT COUNT(*)')
    c.execute(count_query, params)
    total = c.fetchone()[0]
    total_pages = math.ceil(total / per_page)

    query += ' ORDER BY e.loanDate DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    c.execute(query, params)
    rows = c.fetchall()

    result = {
        "data": [
            {
                "loanId": r[0],
                "matricula": r[1],  
                "titulo": r[2],
                "emprestimo": r[3][:10],
                "devolucao_prevista": r[4][:10],
                "status": r[5]
            } for r in rows
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    }
    conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
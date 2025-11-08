from datetime import datetime
import sqlite3

def init_db():
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()


    c.execute('''
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL CHECK(length(nome) > 0 AND length(nome) <= 100),
            matricula TEXT NOT NULL UNIQUE CHECK(length(matricula) = 5 AND matricula GLOB '[0-9][0-9][0-9][0-9][0-9]'),
            tipo TEXT NOT NULL CHECK(tipo IN ('ALUNO', 'PROFESSOR', 'FUNCIONARIO')),
            email TEXT UNIQUE CHECK(
                email IS NULL OR 
                email = '' OR 
                (email LIKE '%@%' AND length(email) >= 5)
            ),
            ativoDeRegistro TEXT NOT NULL DEFAULT (date('now')),
            status TEXT NOT NULL DEFAULT 'ATIVO' CHECK(status IN ('ATIVO', 'INATIVO', 'SUSPENSO'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS livro (
            bookId INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL CHECK(length(titulo) > 0 AND length(titulo) <= 200),
            autores TEXT NOT NULL CHECK(length(autores) > 0 AND length(autores) <= 100),
            ISBN TEXT CHECK(
                ISBN IS NULL OR 
                (length(ISBN) >= 10 AND length(ISBN) <= 13)
            ),
            edicao TEXT,
            ano INTEGER CHECK(ano IS NULL OR ano >= 0),
            copiasTotal INTEGER NOT NULL CHECK(copiasTotal > 0),
            copiasDisponiveis INTEGER NOT NULL CHECK(copiasDisponiveis >= 0),
            status TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK(status IN ('DISPONIVEL', 'INDISPONIVEL'))
        )
    ''')


    c.execute('''
        CREATE TABLE IF NOT EXISTS emprestimo (
            loanId INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER NOT NULL,
            bookId INTEGER NOT NULL,
            copyId INTEGER,
            loanDate TEXT NOT NULL DEFAULT (datetime('now')),
            dueDate TEXT NOT NULL,
            returnDate TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'RETURNED', 'OVERDUE', 'CANCEL')),
            fine REAL DEFAULT 0.0,
            FOREIGN KEY (userId) REFERENCES usuario (id),
            FOREIGN KEY (bookId) REFERENCES livro (bookId)
        )
    ''')

    conn.commit()
    conn.close()
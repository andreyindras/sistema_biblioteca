import unittest
import sqlite3
import json
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from database import init_db


class TestBiblioteca(unittest.TestCase):
    """Classe base para testes do sistema de biblioteca"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        if os.path.exists('biblioteca.db'):
            os.remove('biblioteca.db')
        init_db()
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if os.path.exists('biblioteca.db'):
            os.remove('biblioteca.db')


class TestUsuarios(TestBiblioteca):
    """Testes para o módulo de Cadastro de Usuários (Parte 1)"""
    
    def test_cadastro_usuario_valido(self):
        """Testa cadastro de usuário com dados válidos"""
        response = self.client.post('/usuarios', data={
            'nome': 'João Silva',
            'matricula': '12345',
            'tipo': 'ALUNO',
            'email': 'joao@example.com'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT * FROM usuario WHERE matricula = ?', ('12345',))
        usuario = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario[1], 'João Silva')
        self.assertEqual(usuario[3], 'ALUNO')
        
    def test_matricula_duplicada(self):
        """Testa que matrícula duplicada falha"""
        self.client.post('/usuarios', data={
            'nome': 'João Silva',
            'matricula': '12345',
            'tipo': 'ALUNO'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO usuario (nome, matricula, tipo) 
                VALUES (?, ?, ?)
            ''', ('Maria Santos', '12345', 'PROFESSOR'))
            conn.commit()
            self.fail("Deveria lançar exceção por matrícula duplicada")
        except sqlite3.IntegrityError:
            pass 
        finally:
            conn.close()
    
    def test_matricula_formato_invalido(self):
        """Testa validação de formato de matrícula (5 dígitos)"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()

        try:
            c.execute('''
                INSERT INTO usuario (nome, matricula, tipo) 
                VALUES (?, ?, ?)
            ''', ('Teste', '123', 'ALUNO'))
            conn.commit()
            self.fail("Deveria falhar com matrícula de 3 dígitos")
        except sqlite3.IntegrityError:
            pass
        
        try:
            c.execute('''
                INSERT INTO usuario (nome, matricula, tipo) 
                VALUES (?, ?, ?)
            ''', ('Teste', 'ABC12', 'ALUNO'))
            conn.commit()
            self.fail("Deveria falhar com matrícula alfanumérica")
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def test_tipo_usuario_valido(self):
        """Testa que apenas tipos válidos são aceitos"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO usuario (nome, matricula, tipo) 
                VALUES (?, ?, ?)
            ''', ('Teste', '12345', 'INVALIDO'))
            conn.commit()
            self.fail("Deveria falhar com tipo inválido")
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def test_email_formato_valido(self):
        """Testa validação de formato de email"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO usuario (nome, matricula, tipo, email) 
                VALUES (?, ?, ?, ?)
            ''', ('Teste', '12345', 'ALUNO', 'email_invalido'))
            conn.commit()
            self.fail("Deveria falhar com email sem @ e domínio")
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()


class TestLivros(TestBiblioteca):
    """Testes para o módulo de Catálogo de Livros (Parte 2)"""
    
    def test_cadastro_livro_valido(self):
        """Testa cadastro de livro com dados válidos"""
        response = self.client.post('/livros', data={
            'titulo': 'Python para Iniciantes',
            'autores': 'João Silva',
            'isbn': '1234567890',
            'edicao': '3ª edição',
            'ano': '2023',
            'copiasTotal': '5'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT * FROM livro WHERE titulo = ?', ('Python para Iniciantes',))
        livro = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(livro)
        self.assertEqual(livro[6], 5)  
        self.assertEqual(livro[7], 5)  
        self.assertEqual(livro[8], 'DISPONIVEL') 
    
    def test_copias_disponiveis_igual_total(self):
        """Testa que copiasDisponiveis inicia igual a copiasTotal"""
        self.client.post('/livros', data={
            'titulo': 'Teste',
            'autores': 'Autor',
            'copiasTotal': '10'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT copiasTotal, copiasDisponiveis FROM livro WHERE titulo = ?', ('Teste',))
        copias = c.fetchone()
        conn.close()
        
        self.assertEqual(copias[0], copias[1])
    
    def test_isbn_tamanho_invalido(self):
        """Testa validação de tamanho do ISBN"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO livro (titulo, autores, ISBN, copiasTotal, copiasDisponiveis, status) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Teste', 'Autor', '123', 10, 10, 'DISPONIVEL'))
            conn.commit()
            self.fail("Deveria falhar com ISBN de 3 dígitos")
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def test_copias_total_positivo(self):
        """Testa que copiasTotal deve ser maior que zero"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO livro (titulo, autores, copiasTotal, copiasDisponiveis, status) 
                VALUES (?, ?, ?, ?, ?)
            ''', ('Teste', 'Autor', 0, 0, 'DISPONIVEL'))
            conn.commit()
            self.fail("Deveria falhar com copiasTotal = 0")
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()


class TestEmprestimos(TestBiblioteca):
    """Testes para o módulo de Empréstimo e Devoluções (Parte 3)"""
    
    def setUp(self):
        """Configuração com usuário e livro pré-cadastrados"""
        super().setUp()
        
        self.client.post('/usuarios', data={
            'nome': 'Teste Aluno',
            'matricula': '11111',
            'tipo': 'ALUNO'
        })
        
        self.client.post('/livros', data={
            'titulo': 'Livro Teste',
            'autores': 'Autor Teste',
            'copiasTotal': '3'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT id FROM usuario WHERE matricula = ?', ('11111',))
        self.user_id = c.fetchone()[0]
        c.execute('SELECT bookId FROM livro WHERE titulo = ?', ('Livro Teste',))
        self.book_id = c.fetchone()[0]
        conn.close()
    
    def test_emprestimo_valido(self):
        """Testa realização de empréstimo válido"""
        response = self.client.post('/emprestimos', data={
            'userId': str(self.user_id),
            'bookId': str(self.book_id),
            'tipo': 'ALUNO'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT * FROM emprestimo WHERE userId = ? AND bookId = ?', 
                  (self.user_id, self.book_id))
        emprestimo = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(emprestimo)
        self.assertEqual(emprestimo[7], 'ACTIVE')
    
    def test_reducao_copias_disponiveis(self):
        """Testa que empréstimo reduz copiasDisponiveis"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT copiasDisponiveis FROM livro WHERE bookId = ?', (self.book_id,))
        copias_antes = c.fetchone()[0]
        conn.close()
        
        self.client.post('/emprestimos', data={
            'userId': str(self.user_id),
            'bookId': str(self.book_id),
            'tipo': 'ALUNO'
        })

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT copiasDisponiveis FROM livro WHERE bookId = ?', (self.book_id,))
        copias_depois = c.fetchone()[0]
        conn.close()
        
        self.assertEqual(copias_depois, copias_antes - 1)
    
    def test_emprestimo_sem_copias_disponiveis(self):
        """Testa que não é possível emprestar sem cópias disponíveis"""
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('UPDATE livro SET copiasDisponiveis = 0 WHERE bookId = ?', (self.book_id,))
        conn.commit()
        conn.close()

        response = self.client.post('/emprestimos', data={
            'userId': str(self.user_id),
            'bookId': str(self.book_id),
            'tipo': 'ALUNO'
        })
        
        self.assertEqual(response.status_code, 400)
    
    def test_prazo_aluno_14_dias(self):
        """Testa que aluno recebe prazo de 14 dias"""
        self.client.post('/emprestimos', data={
            'userId': str(self.user_id),
            'bookId': str(self.book_id),
            'tipo': 'ALUNO'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT loanDate, dueDate FROM emprestimo WHERE userId = ?', (self.user_id,))
        result = c.fetchone()
        conn.close()
        
        loan_date = datetime.strptime(result[0][:10], '%Y-%m-%d')
        due_date = datetime.strptime(result[1][:10], '%Y-%m-%d')
        diferenca = (due_date - loan_date).days
        
        self.assertEqual(diferenca, 14)
    
    def test_prazo_professor_30_dias(self):
        """Testa que professor recebe prazo de 30 dias"""
        self.client.post('/usuarios', data={
            'nome': 'Prof Teste',
            'matricula': '22222',
            'tipo': 'PROFESSOR'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT id FROM usuario WHERE matricula = ?', ('22222',))
        prof_id = c.fetchone()[0]
        conn.close()

        self.client.post('/emprestimos', data={
            'userId': str(prof_id),
            'bookId': str(self.book_id),
            'tipo': 'PROFESSOR'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT loanDate, dueDate FROM emprestimo WHERE userId = ?', (prof_id,))
        result = c.fetchone()
        conn.close()
        
        loan_date = datetime.strptime(result[0][:10], '%Y-%m-%d')
        due_date = datetime.strptime(result[1][:10], '%Y-%m-%d')
        diferenca = (due_date - loan_date).days
        
        self.assertEqual(diferenca, 30)


class TestRelatorios(TestBiblioteca):
    """Testes para o módulo de Relatórios (Parte 4)"""
    
    def setUp(self):
        """Configuração com dados de teste"""
        super().setUp()
        
        self.client.post('/usuarios', data={
            'nome': 'Usuario Relatorio',
            'matricula': '99999',
            'tipo': 'ALUNO'
        })
        
        self.client.post('/livros', data={
            'titulo': 'Livro Relatorio',
            'autores': 'Autor Relatorio',
            'copiasTotal': '5'
        })
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT id FROM usuario WHERE matricula = ?', ('99999',))
        user_id = c.fetchone()[0]
        c.execute('SELECT bookId FROM livro WHERE titulo = ?', ('Livro Relatorio',))
        book_id = c.fetchone()[0]
        conn.close()

        self.client.post('/emprestimos', data={
            'userId': str(user_id),
            'bookId': str(book_id),
            'tipo': 'ALUNO'
        })
    
    def test_relatorio_retorna_json(self):
        """Testa que relatório retorna JSON válido"""
        response = self.client.get('/api/relatorio/emprestimos')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('data', data)
        self.assertIn('pagination', data)
    
    def test_relatorio_contem_matricula(self):
        """Testa que relatório contém matrícula (privacidade)"""
        response = self.client.get('/api/relatorio/emprestimos')
        data = json.loads(response.data)
        
        self.assertGreater(len(data['data']), 0)
        primeiro = data['data'][0]
        self.assertIn('matricula', primeiro)
        self.assertEqual(primeiro['matricula'], '99999')
    
    def test_relatorio_nao_contem_email(self):
        """Testa que relatório não expõe emails (privacidade)"""
        response = self.client.get('/api/relatorio/emprestimos')
        data = json.loads(response.data)
        
        if len(data['data']) > 0:
            primeiro = data['data'][0]
            self.assertNotIn('email', primeiro)
    
    def test_paginacao_funcional(self):
        """Testa que paginação funciona corretamente"""
        response = self.client.get('/api/relatorio/emprestimos?page=1')
        data = json.loads(response.data)
        
        self.assertIn('pagination', data)
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['per_page'], 20)
    
    def test_filtro_data_inicio(self):
        """Testa filtro por data de início"""
        hoje = datetime.now().strftime('%Y-%m-%d')
        response = self.client.get(f'/api/relatorio/emprestimos?start={hoje}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data['data'], list)
    
    def test_filtro_data_fim(self):
        """Testa filtro por data de fim"""
        hoje = datetime.now().strftime('%Y-%m-%d')
        response = self.client.get(f'/api/relatorio/emprestimos?end={hoje}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data['data'], list)
    
    def test_limite_registros_paginacao(self):
        """Testa que paginação limita registros por página"""
        response = self.client.get('/api/relatorio/emprestimos?page=1')
        data = json.loads(response.data)

        self.assertLessEqual(len(data['data']), 20)


class TestIntegracao(TestBiblioteca):
    """Testes de integração entre módulos"""
    
    def test_fluxo_completo_emprestimo(self):
        """Testa fluxo completo: cadastro usuário -> cadastro livro -> empréstimo -> relatório"""

        self.client.post('/usuarios', data={
            'nome': 'Usuario Completo',
            'matricula': '88888',
            'tipo': 'ALUNO',
            'email': 'completo@test.com'
        })

        self.client.post('/livros', data={
            'titulo': 'Livro Completo',
            'autores': 'Autor Completo',
            'isbn': '1234567890123',
            'copiasTotal': '2'
        })

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute('SELECT id FROM usuario WHERE matricula = ?', ('88888',))
        user_id = c.fetchone()[0]
        c.execute('SELECT bookId FROM livro WHERE titulo = ?', ('Livro Completo',))
        book_id = c.fetchone()[0]
        conn.close()

        response = self.client.post('/emprestimos', data={
            'userId': str(user_id),
            'bookId': str(book_id),
            'tipo': 'ALUNO'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/relatorio/emprestimos')
        data = json.loads(response.data)

        self.assertGreater(len(data['data']), 0)
        
        emprestimos = [e for e in data['data'] if e['matricula'] == '88888']
        self.assertEqual(len(emprestimos), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
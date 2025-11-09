import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import os
import time
from datetime import datetime, timedelta


class TestBibliotecaSelenium(unittest.TestCase):
    """Testes Selenium para o sistema de biblioteca - Positivos + Negativos"""

    def setUp(self):
        """Configuração do WebDriver e banco limpo"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.base_url = "http://127.0.0.1:5000"
        
        # Limpar banco com tratamento de erro
        try:
            if os.path.exists('biblioteca.db'):
                os.remove('biblioteca.db')
        except PermissionError:
            time.sleep(1)
            if os.path.exists('biblioteca.db'):
                os.remove('biblioteca.db')
        
        # Recriar tabelas COM FOREIGN KEYS HABILITADAS
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL,
                email TEXT,
                ativoDeRegistro TEXT NOT NULL DEFAULT (date('now')),
                status TEXT NOT NULL DEFAULT 'ATIVO'
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS livro (
                bookId INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autores TEXT NOT NULL,
                ISBN TEXT,
                edicao TEXT,
                ano INTEGER,
                copiasTotal INTEGER NOT NULL,
                copiasDisponiveis INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'DISPONIVEL'
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS emprestimo (
                loanId INTEGER PRIMARY KEY AUTOINCREMENT,
                userId INTEGER NOT NULL,
                bookId INTEGER NOT NULL,
                loanDate TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                dueDate TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                FOREIGN KEY (userId) REFERENCES usuario (id) ON DELETE RESTRICT,
                FOREIGN KEY (bookId) REFERENCES livro (bookId) ON DELETE RESTRICT
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """Fechar navegador e limpar banco"""
        self.driver.quit()
        # Aguardar e tentar remover banco com retry
        time.sleep(0.5)
        max_tentativas = 3
        for i in range(max_tentativas):
            try:
                if os.path.exists('biblioteca.db'):
                    os.remove('biblioteca.db')
                break
            except PermissionError:
                if i < max_tentativas - 1:
                    time.sleep(1)
                else:
                    print("Aviso: Não foi possível remover biblioteca.db")


    # ========================= TESTES POSITIVOS =========================

    def test_cadastro_usuario_valido(self):
        """Testa cadastro de usuário válido e verificação na lista"""
        driver = self.driver
        driver.get(self.base_url + "/usuarios")
        
        nome = driver.find_element(By.NAME, "nome")
        nome.send_keys("João Silva")
        
        matricula = driver.find_element(By.NAME, "matricula")
        matricula.send_keys("12345")
        
        tipo = driver.find_element(By.NAME, "tipo")
        tipo.send_keys("ALUNO")
        
        email = driver.find_element(By.NAME, "email")
        email.send_keys("joao@example.com")
        
        submit = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        submit.click()
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        found = False
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[1].text == "João Silva" and cells[2].text == "12345":
                found = True
                self.assertEqual(cells[3].text, "ALUNO")
                self.assertEqual(cells[4].text, "joao@example.com")
                self.assertEqual(cells[5].text, "ATIVO")
                break
        self.assertTrue(found, "Usuário não encontrado na tabela")

    def test_cadastro_livro_valido(self):
        """Testa cadastro de livro válido e verificação na lista"""
        driver = self.driver
        driver.get(self.base_url + "/livros")
        
        titulo = driver.find_element(By.NAME, "titulo")
        titulo.send_keys("Python Avançado")
        
        autores = driver.find_element(By.NAME, "autores")
        autores.send_keys("Maria Santos")
        
        isbn = driver.find_element(By.NAME, "isbn")
        isbn.send_keys("1234567890")
        
        edicao = driver.find_element(By.NAME, "edicao")
        edicao.send_keys("2ª")
        
        ano = driver.find_element(By.NAME, "ano")
        ano.send_keys("2022")
        
        copias = driver.find_element(By.NAME, "copiasTotal")
        copias.send_keys("3")
        
        submit = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        submit.click()
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        found = False
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[1].text == "Python Avançado" and cells[2].text == "Maria Santos":
                found = True
                self.assertEqual(cells[3].text, "1234567890")
                self.assertEqual(cells[4].text, "3")
                self.assertEqual(cells[5].text, "3")
                self.assertEqual(cells[6].text, "DISPONIVEL")
                break
        self.assertTrue(found, "Livro não encontrado na tabela")

    def test_emprestimo_valido_aluno(self):
        """Testa empréstimo para ALUNO e verifica data de devolução (14 dias)"""
        driver = self.driver
        
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO usuario (nome, matricula, tipo, email) VALUES (?, ?, ?, ?)",
                  ("Aluno Teste", "54321", "ALUNO", "aluno@test.com"))
        user_id = c.lastrowid
        
        c.execute("INSERT INTO livro (titulo, autores, copiasTotal, copiasDisponiveis) VALUES (?, ?, ?, ?)",
                  ("Livro Teste", "Autor Teste", 2, 2))
        book_id = c.lastrowid
        conn.commit()
        conn.close()
        
        driver.get(self.base_url + "/emprestimos")
        
        driver.find_element(By.NAME, "userId").send_keys(str(user_id))
        driver.find_element(By.NAME, "bookId").send_keys(str(book_id))
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        found = False
        today = datetime.now().date()
        expected_due = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[1].text == "Aluno Teste" and cells[2].text == "Livro Teste":
                found = True
                # A data no banco pode ser exibida com horário, pegar só os 10 primeiros chars
                self.assertEqual(cells[3].text, today.strftime("%Y-%m-%d"))
                self.assertEqual(cells[4].text, expected_due)
                self.assertEqual(cells[5].text, "ACTIVE")
                break
        self.assertTrue(found, "Empréstimo não encontrado na tabela")

    def test_emprestimo_valido_professor(self):
        """Testa empréstimo para PROFESSOR e verifica data de devolução (30 dias)"""
        driver = self.driver
        
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO usuario (nome, matricula, tipo, email) VALUES (?, ?, ?, ?)",
                  ("Prof Teste", "67890", "PROFESSOR", "prof@test.com"))
        user_id = c.lastrowid
        
        c.execute("INSERT INTO livro (titulo, autores, copiasTotal, copiasDisponiveis) VALUES (?, ?, ?, ?)",
                  ("Livro Prof", "Autor Prof", 1, 1))
        book_id = c.lastrowid
        conn.commit()
        conn.close()
        
        driver.get(self.base_url + "/emprestimos")
        
        driver.find_element(By.NAME, "userId").send_keys(str(user_id))
        driver.find_element(By.NAME, "bookId").send_keys(str(book_id))
        driver.execute_script("document.querySelector('input[name=\"tipo\"]').value = 'PROFESSOR';")
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        found = False
        today = datetime.now().date()
        expected_due = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[1].text == "Prof Teste" and cells[2].text == "Livro Prof":
                found = True
                self.assertEqual(cells[3].text, today.strftime("%Y-%m-%d"))
                self.assertEqual(cells[4].text, expected_due)
                self.assertEqual(cells[5].text, "ACTIVE")
                break
        self.assertTrue(found, "Empréstimo não encontrado na tabela")

    def test_relatorio_emprestimos(self):
        """Testa relatório de empréstimos com filtro e verifica privacidade (sem email)"""
        driver = self.driver
        
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO usuario (nome, matricula, tipo, email) VALUES (?, ?, ?, ?)",
                  ("User Relatorio", "11111", "ALUNO", "hidden@email.com"))
        user_id = c.lastrowid
        c.execute("INSERT INTO livro (titulo, autores, copiasTotal, copiasDisponiveis) VALUES (?, ?, ?, ?)",
                  ("Livro Relatorio", "Autor Relatorio", 1, 0))
        book_id = c.lastrowid
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        due = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        c.execute("INSERT INTO emprestimo (userId, bookId, loanDate, dueDate) VALUES (?, ?, ?, ?)",
                  (user_id, book_id, today, due))
        conn.commit()
        conn.close()
        
        driver.get(self.base_url + "/relatorios")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tabela-relatorio")))
        time.sleep(1)
        
        tbody = driver.find_element(By.CSS_SELECTOR, "#tabela-relatorio tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        self.assertGreater(len(rows), 0)
        
        cells = rows[0].find_elements(By.TAG_NAME, "td")
        self.assertEqual(cells[1].text, "11111")
        self.assertEqual(cells[2].text, "Livro Relatorio")
        self.assertEqual(cells[5].text, "ACTIVE")
        
        page_source = driver.page_source
        self.assertNotIn("hidden@email.com", page_source, "Email não deve aparecer no relatório")


    # ========================= TESTES NEGATIVOS =========================

    def test_matricula_invalida_menos_5_digitos(self):
        """Matrícula com menos de 5 dígitos deve falhar (validação HTML + DB)"""
        driver = self.driver
        driver.get(self.base_url + "/usuarios")

        driver.find_element(By.NAME, "nome").send_keys("Teste")
        driver.find_element(By.NAME, "matricula").send_keys("123")
        driver.find_element(By.NAME, "tipo").send_keys("ALUNO")
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        WebDriverWait(driver, 5).until(EC.url_contains("/usuarios"))
        self.assertIn("/usuarios", driver.current_url)

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM usuario WHERE matricula = '123'")
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    def test_matricula_com_letras(self):
        """Matrícula com letras deve ser bloqueada pelo pattern HTML"""
        driver = self.driver
        driver.get(self.base_url + "/usuarios")

        matricula_input = driver.find_element(By.NAME, "matricula")
        matricula_input.send_keys("ABC12")

        driver.find_element(By.NAME, "nome").send_keys("Teste")
        driver.find_element(By.NAME, "tipo").send_keys("ALUNO")
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        time.sleep(1)
        self.assertEqual(matricula_input.get_attribute("value"), "ABC12")

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM usuario WHERE matricula = 'ABC12'")
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    def test_matricula_duplicada(self):
        """Segunda matrícula igual deve falhar (UNIQUE constraint)"""
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO usuario (nome, matricula, tipo) VALUES (?, ?, ?)", ("Primeiro", "99999", "ALUNO"))
        conn.commit()
        conn.close()

        driver = self.driver
        driver.get(self.base_url + "/usuarios")

        driver.find_element(By.NAME, "nome").send_keys("Segundo")
        driver.find_element(By.NAME, "matricula").send_keys("99999")
        driver.find_element(By.NAME, "tipo").send_keys("PROFESSOR")
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        time.sleep(2)
        page_source = driver.page_source
        self.assertNotIn("Segundo", page_source)

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM usuario WHERE matricula = '99999'")
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_emprestimo_livro_indisponivel(self):
        """Não deve permitir empréstimo se copiasDisponiveis == 0"""
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO usuario (nome, matricula, tipo) VALUES (?, ?, ?)", ("User", "11111", "ALUNO"))
        user_id = c.lastrowid
        c.execute("INSERT INTO livro (titulo, autores, copiasTotal, copiasDisponiveis) VALUES (?, ?, ?, ?)",
                  ("Indisponível", "Autor", 1, 0))
        book_id = c.lastrowid
        conn.commit()
        conn.close()

        driver = self.driver
        driver.get(self.base_url + "/emprestimos")

        driver.find_element(By.NAME, "userId").send_keys(str(user_id))
        driver.find_element(By.NAME, "bookId").send_keys(str(book_id))
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Livro indisponível")
        )
        self.assertIn("Livro indisponível", driver.page_source)

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM emprestimo WHERE bookId = ?", (book_id,))
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    def test_emprestimo_usuario_inexistente(self):
        """Empréstimo com userId inexistente deve falhar (FK)"""
        conn = sqlite3.connect('biblioteca.db')
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("INSERT INTO livro (titulo, autores, copiasTotal, copiasDisponiveis) VALUES (?, ?, ?, ?)",
                  ("Livro Válido", "Autor", 2, 2))
        book_id = c.lastrowid
        conn.commit()
        conn.close()

        driver = self.driver
        driver.get(self.base_url + "/emprestimos")

        driver.find_element(By.NAME, "userId").send_keys("999999")
        driver.find_element(By.NAME, "bookId").send_keys(str(book_id))
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        time.sleep(2)
        
        # Verificar que houve erro (página não mudou ou mostra erro)
        page_source = driver.page_source
        # O erro pode aparecer na página
        
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM emprestimo")
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0, "Empréstimo não deveria ter sido criado com userId inválido")

    def test_email_invalido_cadastro(self):
        """Email sem @ ou formato errado deve ser bloqueado pelo HTML5"""
        driver = self.driver
        driver.get(self.base_url + "/usuarios")

        driver.find_element(By.NAME, "nome").send_keys("Teste Email")
        driver.find_element(By.NAME, "matricula").send_keys("77777")
        driver.find_element(By.NAME, "tipo").send_keys("ALUNO")
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys("email-invalido")
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        time.sleep(1)
        self.assertEqual(email_input.get_attribute("value"), "email-invalido")

        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM usuario WHERE email = 'email-invalido'")
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
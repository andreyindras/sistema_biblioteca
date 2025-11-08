import unittest
import time
import os
import sqlite3
import subprocess
import sys
import signal
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Caminho base do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)


class BibliotecaSeleniumTestBase(unittest.TestCase):
    """Classe base para testes Selenium"""
    
    flask_process = None
    driver = None
    base_url = "http://localhost:5000"
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial da classe - executada uma vez"""
        print("\n=== INICIANDO TESTES SELENIUM ===")
        
        # 1. Limpar banco de dados existente
        db_path = os.path.join(BASE_DIR, 'biblioteca.db')
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("✓ Banco de dados limpo")
            except Exception as e:
                print(f"⚠ Não foi possível remover banco: {e}")
        
        # 2. Iniciar servidor Flask em processo separado
        app_path = os.path.join(BASE_DIR, 'app.py')
        cls.flask_process = subprocess.Popen(
            [sys.executable, app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=BASE_DIR
        )
        
        # Aguardar servidor iniciar
        print("⏳ Aguardando servidor Flask iniciar...")
        time.sleep(3)
        
        # 3. Configurar WebDriver do Chrome (VISÍVEL - sem headless)
        options = webdriver.ChromeOptions()
        # NÃO usar headless para ver as interações
        # options.add_argument('--headless')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        try:
            cls.driver = webdriver.Chrome(options=options)
            print("✓ Chrome iniciado")
        except Exception as e:
            print(f"✗ Erro ao iniciar Chrome: {e}")
            cls.tearDownClass()
            raise
        
        cls.driver.implicitly_wait(10)
        
        # 4. Verificar se servidor está respondendo
        try:
            cls.driver.get(cls.base_url)
            print("✓ Servidor Flask está respondendo")
        except Exception as e:
            print(f"✗ Servidor não está respondendo: {e}")
            cls.tearDownClass()
            raise
        
        print("=== SETUP COMPLETO ===\n")
        
    @classmethod
    def tearDownClass(cls):
        """Limpeza final - executada uma vez"""
        print("\n=== FINALIZANDO TESTES ===")
        
        # Fechar navegador
        if cls.driver:
            try:
                cls.driver.quit()
                print("✓ Navegador fechado")
            except Exception as e:
                print(f"⚠ Erro ao fechar navegador: {e}")
        
        # Encerrar servidor Flask (Windows requer tratamento especial)
        if cls.flask_process:
            try:
                if sys.platform == 'win32':
                    # No Windows, usar taskkill para encerrar processo
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(cls.flask_process.pid)], 
                                 capture_output=True, timeout=3)
                else:
                    cls.flask_process.terminate()
                    cls.flask_process.wait(timeout=3)
                print("✓ Servidor Flask encerrado")
            except Exception as e:
                print(f"⚠ Erro ao encerrar Flask: {e}")
        
        # Aguardar liberação do banco
        time.sleep(1)
        
        print("=== TESTES FINALIZADOS ===\n")
        
    def setUp(self):
        """Configuração antes de cada teste"""
        # Limpar dados sem remover o arquivo
        db_path = os.path.join(BASE_DIR, 'biblioteca.db')
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path, timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")  # Melhor concorrência
                c = conn.cursor()
                c.execute('DELETE FROM emprestimo')
                c.execute('DELETE FROM livro')
                c.execute('DELETE FROM usuario')
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠ Erro ao limpar banco: {e}")
        time.sleep(0.5)
        
    def wait_for_element(self, by, value, timeout=10):
        """Aguarda elemento estar presente"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            print(f"⏱ Timeout aguardando elemento: {by}={value}")
            raise
    
    def wait_for_clickable(self, by, value, timeout=10):
        """Aguarda elemento estar clicável"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            print(f"⏱ Timeout aguardando elemento clicável: {by}={value}")
            raise


class TestUsuariosUI(BibliotecaSeleniumTestBase):
    """Testes de interface para Cadastro de Usuários (Parte 1)"""
    
    def test_01_acessar_pagina_usuarios(self):
        """Testa se a página de usuários carrega corretamente"""
        self.driver.get(f"{self.base_url}/usuarios")
        
        # Verificar título
        self.assertIn("Usuários", self.driver.title)
        
        # Verificar presença do formulário
        form = self.wait_for_element(By.TAG_NAME, "form")
        self.assertIsNotNone(form)
        
        # Verificar campos do formulário
        nome_input = self.driver.find_element(By.NAME, "nome")
        matricula_input = self.driver.find_element(By.NAME, "matricula")
        tipo_select = self.driver.find_element(By.NAME, "tipo")
        
        self.assertIsNotNone(nome_input)
        self.assertIsNotNone(matricula_input)
        self.assertIsNotNone(tipo_select)
    
    def test_02_cadastrar_usuario_valido(self):
        """Testa cadastro de usuário com dados válidos"""
        self.driver.get(f"{self.base_url}/usuarios")
        
        # Preencher formulário
        nome_input = self.wait_for_element(By.NAME, "nome")
        nome_input.send_keys("João da Silva")
        
        matricula_input = self.driver.find_element(By.NAME, "matricula")
        matricula_input.send_keys("12345")
        
        tipo_select = Select(self.driver.find_element(By.NAME, "tipo"))
        tipo_select.select_by_value("ALUNO")
        
        # Email válido conforme regras: formato email válido
        email_input = self.driver.find_element(By.NAME, "email")
        email_input.send_keys("joao.silva@exemplo.com")
        
        # Submeter formulário
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar redirect
        time.sleep(1)
        table = self.wait_for_element(By.TAG_NAME, "table")
        table_text = table.text
        
        self.assertIn("João da Silva", table_text)
        self.assertIn("12345", table_text)
        self.assertIn("ALUNO", table_text)
    
    def test_03_cadastrar_professor(self):
        """Testa cadastro de professor"""
        self.driver.get(f"{self.base_url}/usuarios")
        
        self.driver.find_element(By.NAME, "nome").send_keys("Profª Maria Santos")
        self.driver.find_element(By.NAME, "matricula").send_keys("98765")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("PROFESSOR")
        self.driver.find_element(By.NAME, "email").send_keys("maria.santos@exemplo.com")
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        table_text = self.driver.find_element(By.TAG_NAME, "table").text
        self.assertIn("Maria Santos", table_text)
        self.assertIn("PROFESSOR", table_text)
    
    def test_04_cadastrar_usuario_sem_email(self):
        """Testa cadastro de usuário sem email (campo opcional)"""
        self.driver.get(f"{self.base_url}/usuarios")
        
        self.driver.find_element(By.NAME, "nome").send_keys("Carlos Souza")
        self.driver.find_element(By.NAME, "matricula").send_keys("55555")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("FUNCIONARIO")
        # Não preencher email (é opcional)
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        table_text = self.driver.find_element(By.TAG_NAME, "table").text
        self.assertIn("Carlos Souza", table_text)
        self.assertIn("FUNCIONARIO", table_text)
    
    def test_05_validacao_matricula_formato(self):
        """Testa validação de formato de matrícula no frontend"""
        self.driver.get(f"{self.base_url}/usuarios")
        
        matricula_input = self.driver.find_element(By.NAME, "matricula")
        
        # Verificar atributo pattern
        pattern = matricula_input.get_attribute("pattern")
        self.assertEqual(pattern, "[0-9]{5}")
        
        # Verificar que é required
        is_required = matricula_input.get_attribute("required")
        self.assertIsNotNone(is_required)


class TestLivrosUI(BibliotecaSeleniumTestBase):
    """Testes de interface para Catálogo de Livros (Parte 2)"""
    
    def test_01_acessar_pagina_livros(self):
        """Testa se a página de livros carrega corretamente"""
        self.driver.get(f"{self.base_url}/livros")
        
        self.assertIn("Livros", self.driver.title)
        
        # Verificar formulário
        titulo_input = self.driver.find_element(By.NAME, "titulo")
        autores_input = self.driver.find_element(By.NAME, "autores")
        copias_input = self.driver.find_element(By.NAME, "copiasTotal")
        
        self.assertIsNotNone(titulo_input)
        self.assertIsNotNone(autores_input)
        self.assertIsNotNone(copias_input)
    
    def test_02_cadastrar_livro_completo(self):
        """Testa cadastro de livro com todos os campos"""
        self.driver.get(f"{self.base_url}/livros")
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Python para Iniciantes")
        self.driver.find_element(By.NAME, "autores").send_keys("João Silva, Maria Santos")
        self.driver.find_element(By.NAME, "isbn").send_keys("9788575222485")
        self.driver.find_element(By.NAME, "edicao").send_keys("3ª Edição")
        self.driver.find_element(By.NAME, "ano").send_keys("2023")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("5")
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        table_text = self.driver.find_element(By.TAG_NAME, "table").text
        self.assertIn("Python para Iniciantes", table_text)
        self.assertIn("9788575222485", table_text)
        self.assertIn("5", table_text)
        self.assertIn("DISPONIVEL", table_text)
    
    def test_03_cadastrar_livro_campos_minimos(self):
        """Testa cadastro de livro apenas com campos obrigatórios"""
        self.driver.get(f"{self.base_url}/livros")
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro Básico")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Desconhecido")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("2")
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        table_text = self.driver.find_element(By.TAG_NAME, "table").text
        self.assertIn("Livro Básico", table_text)
        self.assertIn("2", table_text)


class TestEmprestimosUI(BibliotecaSeleniumTestBase):
    """Testes de interface para Empréstimos (Parte 3)"""
    
    def setUp(self):
        """Configuração com usuário e livro pré-cadastrados"""
        super().setUp()
        
        # Cadastrar usuário SEM email (opcional)
        self.driver.get(f"{self.base_url}/usuarios")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "nome").send_keys("Aluno Teste")
        self.driver.find_element(By.NAME, "matricula").send_keys("11111")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("ALUNO")
        # Email deixado vazio (opcional)
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Obter ID do usuário
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if len(rows) == 0:
            self.fail("Usuário não foi cadastrado")
        self.user_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Cadastrar livro
        self.driver.get(f"{self.base_url}/livros")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro para Empréstimo")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Empréstimo")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("3")
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Obter ID do livro
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if len(rows) == 0:
            self.fail("Livro não foi cadastrado")
        self.book_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
    
    def test_01_acessar_pagina_emprestimos(self):
        """Testa se a página de empréstimos carrega"""
        self.driver.get(f"{self.base_url}/emprestimos")
        
        self.assertIn("Empréstimos", self.driver.title)
        
        userId_input = self.driver.find_element(By.NAME, "userId")
        bookId_input = self.driver.find_element(By.NAME, "bookId")
        
        self.assertIsNotNone(userId_input)
        self.assertIsNotNone(bookId_input)
    
    def test_02_realizar_emprestimo_valido(self):
        """Testa realização de empréstimo válido"""
        self.driver.get(f"{self.base_url}/emprestimos")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "userId").send_keys(self.user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(self.book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(1)
        
        table_text = self.driver.find_element(By.TAG_NAME, "table").text
        self.assertIn("Aluno Teste", table_text)
        self.assertIn("Livro para Empréstimo", table_text)
        self.assertIn("ACTIVE", table_text)
    
    def test_03_verificar_reducao_copias_disponiveis(self):
        """Testa que empréstimo reduz cópias disponíveis"""
        self.driver.get(f"{self.base_url}/livros")
        time.sleep(0.5)
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        copias_antes = rows[0].find_elements(By.TAG_NAME, "td")[6].text
        
        self.driver.get(f"{self.base_url}/emprestimos")
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "userId").send_keys(self.user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(self.book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        self.driver.get(f"{self.base_url}/livros")
        time.sleep(0.5)
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        copias_depois = rows[0].find_elements(By.TAG_NAME, "td")[6].text
        
        self.assertEqual(int(copias_depois), int(copias_antes) - 1)


class TestRelatoriosUI(BibliotecaSeleniumTestBase):
    """Testes de interface para Relatórios (Parte 4)"""
    
    def setUp(self):
        """Configuração com dados de teste"""
        super().setUp()
        
        # Cadastrar usuário COM email válido
        self.driver.get(f"{self.base_url}/usuarios")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "nome").send_keys("Usuario Relatório")
        self.driver.find_element(By.NAME, "matricula").send_keys("99999")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("ALUNO")
        self.driver.find_element(By.NAME, "email").send_keys("relatorio@teste.com")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        user_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Cadastrar livro
        self.driver.get(f"{self.base_url}/livros")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro Relatório")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Relatório")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("5")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        book_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Realizar empréstimo
        self.driver.get(f"{self.base_url}/emprestimos")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "userId").send_keys(user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
    
    def test_01_carregar_relatorio_inicial(self):
        """Testa carregamento inicial do relatório"""
        self.driver.get(f"{self.base_url}/relatorios")
        time.sleep(2)  # Aguardar JavaScript
        
        tbody = self.driver.find_element(By.CSS_SELECTOR, "#tabela-relatorio tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        
        self.assertGreater(len(rows), 0)
    
    def test_02_verificar_privacidade_dados(self):
        """Testa que email não aparece no relatório (privacidade)"""
        self.driver.get(f"{self.base_url}/relatorios")
        time.sleep(2)
        
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        # Email não deve aparecer (privacidade)
        self.assertNotIn("relatorio@teste.com", page_text)
        # Mas matrícula deve estar
        self.assertIn("99999", page_text)


class TestNavegacao(BibliotecaSeleniumTestBase):
    """Testes de navegação entre páginas"""
    
    def test_01_navegacao_menu(self):
        """Testa navegação por todos os links do menu"""
        self.driver.get(f"{self.base_url}/")
        time.sleep(0.5)
        
        usuarios_link = self.driver.find_element(By.LINK_TEXT, "Usuários")
        usuarios_link.click()
        time.sleep(0.5)
        self.assertIn("usuarios", self.driver.current_url)
        
        livros_link = self.driver.find_element(By.LINK_TEXT, "Livros")
        livros_link.click()
        time.sleep(0.5)
        self.assertIn("livros", self.driver.current_url)
        
        emprestimos_link = self.driver.find_element(By.LINK_TEXT, "Empréstimos")
        emprestimos_link.click()
        time.sleep(0.5)
        self.assertIn("emprestimos", self.driver.current_url)


class TestFluxoCompleto(BibliotecaSeleniumTestBase):
    """Teste de fluxo completo end-to-end"""
    
    def test_fluxo_completo_sistema(self):
        """Testa fluxo completo: cadastro -> empréstimo -> relatório"""
        print("\n🚀 Iniciando teste de fluxo completo...")
        
        # 1. Cadastrar usuário
        print("  📝 Cadastrando usuário...")
        self.driver.get(f"{self.base_url}/usuarios")
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "nome").send_keys("João Completo")
        self.driver.find_element(By.NAME, "matricula").send_keys("88888")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("ALUNO")
        self.driver.find_element(By.NAME, "email").send_keys("joao@completo.com")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        user_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        self.assertIn("João Completo", self.driver.page_source)
        print("  ✓ Usuário cadastrado")
        
        # 2. Cadastrar livro
        print("  📚 Cadastrando livro...")
        self.driver.find_element(By.LINK_TEXT, "Livros").click()
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro Integrado")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Integrado")
        self.driver.find_element(By.NAME, "isbn").send_keys("1234567890123")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("3")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        book_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        self.assertIn("Livro Integrado", self.driver.page_source)
        print("  ✓ Livro cadastrado")
        
        # 3. Realizar empréstimo
        print("  🔄 Realizando empréstimo...")
        self.driver.find_element(By.LINK_TEXT, "Empréstimos").click()
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "userId").send_keys(user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        self.assertIn("João Completo", self.driver.page_source)
        self.assertIn("Livro Integrado", self.driver.page_source)
        print("  ✓ Empréstimo realizado")
        
        # 4. Verificar no relatório
        print("  📊 Verificando relatório...")
        self.driver.find_element(By.LINK_TEXT, "Relatórios").click()
        time.sleep(2)
        
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("88888", page_text)
        self.assertIn("Livro Integrado", page_text)
        print("  ✓ Dados no relatório")
        
        # 5. Verificar que cópias foram reduzidas
        print("  🔍 Verificando cópias disponíveis...")
        self.driver.find_element(By.LINK_TEXT, "Livros").click()
        time.sleep(0.5)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        copias_disponiveis = rows[0].find_elements(By.TAG_NAME, "td")[6].text
        
        self.assertEqual(copias_disponiveis, "2")
        print("  ✓ Cópias reduzidas (3 -> 2)")
        
        print("✅ Fluxo completo executado com sucesso!\n")


if __name__ == '__main__':
    # Executar todas as classes de teste
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar testes na ordem desejada
    print("\n" + "="*60)
    print("TESTES SELENIUM - SISTEMA BIBLIOTECA")
    print("="*60 + "\n")
    
    suite.addTests(loader.loadTestsFromTestCase(TestUsuariosUI))
    suite.addTests(loader.loadTestsFromTestCase(TestLivrosUI))
    suite.addTests(loader.loadTestsFromTestCase(TestEmprestimosUI))
    suite.addTests(loader.loadTestsFromTestCase(TestRelatoriosUI))
    suite.addTests(loader.loadTestsFromTestCase(TestNavegacao))
    suite.addTests(loader.loadTestsFromTestCase(TestFluxoCompleto))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️  Erros: {len(result.errors)}")
    print("="*60 + "\n")
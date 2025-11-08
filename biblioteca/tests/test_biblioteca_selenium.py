import unittest
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BibliotecaSeleniumTestBase(unittest.TestCase):
    """Classe base para testes Selenium"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial da classe - executada uma vez"""
        # Configurar o driver do Chrome (pode usar outros navegadores)
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        cls.base_url = "http://localhost:5000"
        
    @classmethod
    def tearDownClass(cls):
        """Limpeza final - executada uma vez"""
        cls.driver.quit()
        
    def setUp(self):
        """Configuração antes de cada teste"""
        # Limpar banco de dados se necessário
        if os.path.exists('biblioteca.db'):
            os.remove('biblioteca.db')
        time.sleep(0.5)
        
    def wait_for_element(self, by, value, timeout=10):
        """Aguarda elemento estar presente"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_clickable(self, by, value, timeout=10):
        """Aguarda elemento estar clicável"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )


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
        
        email_input = self.driver.find_element(By.NAME, "email")
        email_input.send_keys("joao.silva@exemplo.com")
        
        # Submeter formulário
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar redirect e verificar se usuário aparece na tabela
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
    
    def test_04_validacao_matricula_formato(self):
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
        self.assertIn("5", table_text)  # Cópias totais
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
    
    def test_04_validacao_copias_minimas(self):
        """Testa validação de número mínimo de cópias"""
        self.driver.get(f"{self.base_url}/livros")
        
        copias_input = self.driver.find_element(By.NAME, "copiasTotal")
        min_value = copias_input.get_attribute("min")
        
        self.assertEqual(min_value, "1")
    
    def test_05_verificar_copias_disponiveis_inicial(self):
        """Testa que cópias disponíveis iniciam igual ao total"""
        self.driver.get(f"{self.base_url}/livros")
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Teste Cópias")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Teste")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("8")
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Localizar a linha da tabela do livro recém-criado
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        first_row_text = rows[0].text if rows else ""
        
        # Verificar que tanto total quanto disponíveis mostram 8
        self.assertIn("8", first_row_text)


class TestEmprestimosUI(BibliotecaSeleniumTestBase):
    """Testes de interface para Empréstimos (Parte 3)"""
    
    def setUp(self):
        """Configuração com usuário e livro pré-cadastrados"""
        super().setUp()
        
        # Cadastrar usuário
        self.driver.get(f"{self.base_url}/usuarios")
        self.driver.find_element(By.NAME, "nome").send_keys("Aluno Teste")
        self.driver.find_element(By.NAME, "matricula").send_keys("11111")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("ALUNO")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        
        # Obter ID do usuário da tabela
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        self.user_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Cadastrar livro
        self.driver.get(f"{self.base_url}/livros")
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro para Empréstimo")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Empréstimo")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("3")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        
        # Obter ID do livro
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
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
        
        self.driver.find_element(By.NAME, "userId").send_keys(self.user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(self.book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(1)
        
        # Verificar que empréstimo aparece na tabela
        table_text = self.driver.find_element(By.TAG_NAME, "table").text
        self.assertIn("Aluno Teste", table_text)
        self.assertIn("Livro para Empréstimo", table_text)
        self.assertIn("ACTIVE", table_text)
    
    def test_03_verificar_reducao_copias_disponiveis(self):
        """Testa que empréstimo reduz cópias disponíveis"""
        # Verificar cópias antes
        self.driver.get(f"{self.base_url}/livros")
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        copias_antes = rows[0].find_elements(By.TAG_NAME, "td")[6].text  # Coluna disponíveis
        
        # Realizar empréstimo
        self.driver.get(f"{self.base_url}/emprestimos")
        self.driver.find_element(By.NAME, "userId").send_keys(self.user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(self.book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Verificar cópias depois
        self.driver.get(f"{self.base_url}/livros")
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        copias_depois = rows[0].find_elements(By.TAG_NAME, "td")[6].text
        
        self.assertEqual(int(copias_depois), int(copias_antes) - 1)
    
    def test_04_multiplos_emprestimos(self):
        """Testa realizar múltiplos empréstimos"""
        self.driver.get(f"{self.base_url}/emprestimos")
        
        # Primeiro empréstimo
        self.driver.find_element(By.NAME, "userId").send_keys(self.user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(self.book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Segundo empréstimo
        self.driver.find_element(By.NAME, "userId").clear()
        self.driver.find_element(By.NAME, "userId").send_keys(self.user_id)
        self.driver.find_element(By.NAME, "bookId").clear()
        self.driver.find_element(By.NAME, "bookId").send_keys(self.book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Verificar que há 2 empréstimos na tabela
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        self.assertEqual(len(rows), 2)


class TestRelatoriosUI(BibliotecaSeleniumTestBase):
    """Testes de interface para Relatórios (Parte 4)"""
    
    def setUp(self):
        """Configuração com dados de teste"""
        super().setUp()
        
        # Cadastrar usuário
        self.driver.get(f"{self.base_url}/usuarios")
        self.driver.find_element(By.NAME, "nome").send_keys("Usuario Relatório")
        self.driver.find_element(By.NAME, "matricula").send_keys("99999")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("ALUNO")
        self.driver.find_element(By.NAME, "email").send_keys("relatorio@teste.com")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        user_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Cadastrar livro
        self.driver.get(f"{self.base_url}/livros")
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro Relatório")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Relatório")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("5")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        book_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Realizar empréstimo
        self.driver.get(f"{self.base_url}/emprestimos")
        self.driver.find_element(By.NAME, "userId").send_keys(user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
    
    def test_01_acessar_pagina_relatorios(self):
        """Testa se a página de relatórios carrega"""
        self.driver.get(f"{self.base_url}/relatorios")
        
        self.assertIn("Relatórios", self.driver.title)
        
        # Verificar filtros de data
        start_input = self.driver.find_element(By.ID, "start")
        end_input = self.driver.find_element(By.ID, "end")
        
        self.assertIsNotNone(start_input)
        self.assertIsNotNone(end_input)
    
    def test_02_carregar_relatorio_inicial(self):
        """Testa carregamento inicial do relatório"""
        self.driver.get(f"{self.base_url}/relatorios")
        
        # Aguardar tabela carregar (via JavaScript)
        time.sleep(2)
        
        # Verificar que há dados na tabela
        tbody = self.driver.find_element(By.CSS_SELECTOR, "#tabela-relatorio tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        
        self.assertGreater(len(rows), 0)
    
    def test_03_verificar_colunas_relatorio(self):
        """Testa que relatório contém colunas corretas"""
        self.driver.get(f"{self.base_url}/relatorios")
        time.sleep(2)
        
        # Verificar cabeçalhos
        headers = self.driver.find_elements(By.CSS_SELECTOR, "#tabela-relatorio thead th")
        header_texts = [h.text for h in headers]
        
        self.assertIn("ID", header_texts)
        self.assertIn("Matrícula", header_texts)
        self.assertIn("Título", header_texts)
        self.assertIn("Status", header_texts)
    
    def test_04_filtrar_por_data(self):
        """Testa filtro por data"""
        self.driver.get(f"{self.base_url}/relatorios")
        time.sleep(2)
        
        # Preencher filtro de data
        hoje = datetime.now().strftime('%Y-%m-%d')
        start_input = self.driver.find_element(By.ID, "start")
        start_input.send_keys(hoje)
        
        # Clicar em filtrar
        filtrar_button = self.driver.find_element(By.XPATH, "//button[text()='Filtrar']")
        filtrar_button.click()
        time.sleep(2)
        
        # Verificar que ainda há dados (empréstimo foi feito hoje)
        tbody = self.driver.find_element(By.CSS_SELECTOR, "#tabela-relatorio tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        
        self.assertGreater(len(rows), 0)
    
    def test_05_verificar_paginacao(self):
        """Testa que paginação está presente"""
        self.driver.get(f"{self.base_url}/relatorios")
        time.sleep(2)
        
        # Verificar que div de paginação existe
        paginacao = self.driver.find_element(By.ID, "paginacao")
        self.assertIsNotNone(paginacao)
        
        # Verificar que há pelo menos um botão de página
        buttons = paginacao.find_elements(By.TAG_NAME, "button")
        self.assertGreater(len(buttons), 0)
    
    def test_06_verificar_privacidade_dados(self):
        """Testa que email não aparece no relatório (privacidade)"""
        self.driver.get(f"{self.base_url}/relatorios")
        time.sleep(2)
        
        # Verificar que email não está visível
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertNotIn("relatorio@teste.com", page_text)
        
        # Mas matrícula deve estar
        self.assertIn("99999", page_text)


class TestNavegacao(BibliotecaSeleniumTestBase):
    """Testes de navegação entre páginas"""
    
    def test_01_navegacao_menu(self):
        """Testa navegação por todos os links do menu"""
        self.driver.get(f"{self.base_url}/")
        
        # Verificar link Usuários
        usuarios_link = self.driver.find_element(By.LINK_TEXT, "Usuários")
        usuarios_link.click()
        time.sleep(0.5)
        self.assertIn("usuarios", self.driver.current_url)
        
        # Verificar link Livros
        livros_link = self.driver.find_element(By.LINK_TEXT, "Livros")
        livros_link.click()
        time.sleep(0.5)
        self.assertIn("livros", self.driver.current_url)
        
        # Verificar link Empréstimos
        emprestimos_link = self.driver.find_element(By.LINK_TEXT, "Empréstimos")
        emprestimos_link.click()
        time.sleep(0.5)
        self.assertIn("emprestimos", self.driver.current_url)
        
        # Verificar link Relatórios
        relatorios_link = self.driver.find_element(By.LINK_TEXT, "Relatórios")
        relatorios_link.click()
        time.sleep(0.5)
        self.assertIn("relatorios", self.driver.current_url)
    
    def test_02_redirect_root_para_usuarios(self):
        """Testa que root redireciona para usuários"""
        self.driver.get(f"{self.base_url}/")
        time.sleep(0.5)
        
        self.assertIn("usuarios", self.driver.current_url)


class TestFluxoCompleto(BibliotecaSeleniumTestBase):
    """Teste de fluxo completo end-to-end"""
    
    def test_fluxo_completo_sistema(self):
        """Testa fluxo completo: cadastro -> empréstimo -> relatório"""
        
        # 1. Cadastrar usuário
        self.driver.get(f"{self.base_url}/usuarios")
        self.driver.find_element(By.NAME, "nome").send_keys("João Completo")
        self.driver.find_element(By.NAME, "matricula").send_keys("88888")
        Select(self.driver.find_element(By.NAME, "tipo")).select_by_value("ALUNO")
        self.driver.find_element(By.NAME, "email").send_keys("joao@completo.com")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        user_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Verificar que usuário foi cadastrado
        self.assertIn("João Completo", self.driver.page_source)
        
        # 2. Cadastrar livro
        self.driver.find_element(By.LINK_TEXT, "Livros").click()
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "titulo").send_keys("Livro Integrado")
        self.driver.find_element(By.NAME, "autores").send_keys("Autor Integrado")
        self.driver.find_element(By.NAME, "isbn").send_keys("1234567890123")
        self.driver.find_element(By.NAME, "copiasTotal").send_keys("3")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        book_id = rows[0].find_elements(By.TAG_NAME, "td")[0].text
        
        # Verificar que livro foi cadastrado
        self.assertIn("Livro Integrado", self.driver.page_source)
        
        # 3. Realizar empréstimo
        self.driver.find_element(By.LINK_TEXT, "Empréstimos").click()
        time.sleep(0.5)
        
        self.driver.find_element(By.NAME, "userId").send_keys(user_id)
        self.driver.find_element(By.NAME, "bookId").send_keys(book_id)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        
        # Verificar que empréstimo foi realizado
        self.assertIn("João Completo", self.driver.page_source)
        self.assertIn("Livro Integrado", self.driver.page_source)
        
        # 4. Verificar no relatório
        self.driver.find_element(By.LINK_TEXT, "Relatórios").click()
        time.sleep(2)  # Aguardar JavaScript carregar
        
        # Verificar que dados aparecem no relatório
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("88888", page_text)  # Matrícula
        self.assertIn("Livro Integrado", page_text)
        
        # 5. Verificar que cópias foram reduzidas
        self.driver.find_element(By.LINK_TEXT, "Livros").click()
        time.sleep(0.5)
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        copias_disponiveis = rows[0].find_elements(By.TAG_NAME, "td")[6].text
        
        self.assertEqual(copias_disponiveis, "2")  # 3 - 1 = 2


if __name__ == '__main__':
    # Executar testes com verbosidade
    unittest.main(verbosity=2)
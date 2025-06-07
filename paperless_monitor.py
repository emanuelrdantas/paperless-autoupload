import time
import requests
import os
import json
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from configparser import ConfigParser
import sys
import pystray
from PIL import Image, ImageDraw


class PaperlessUploader(FileSystemEventHandler):
    def __init__(self, paperless_url, api_token, folder_path, log_callback=None):
        self.paperless_url = paperless_url.rstrip('/')
        self.api_token = api_token
        self.folder_path = folder_path
        self.log_callback = log_callback
        self.processed_files = set()  # Controle de arquivos já processados
        self.processing_files = set()  # Controle de arquivos sendo processados
        self.headers = {
            'Authorization': f'Token {api_token}',
            'User-Agent': 'PaperlessAutoUploader/1.0'
        }

        # Configurar logging
        log_file = os.path.join(os.path.dirname(
            __file__), 'paperless_uploader.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Carregar lista de arquivos já processados
        self.load_processed_files()

    def load_processed_files(self):
        """Carrega lista de arquivos já processados"""
        try:
            processed_file = os.path.join(
                os.path.dirname(__file__), 'processed_files.txt')
            if os.path.exists(processed_file):
                with open(processed_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        self.processed_files.add(line.strip())
                self.log_message(
                    f"📋 Carregados {len(self.processed_files)} arquivos já processados")
        except Exception as e:
            self.log_message(
                f"⚠️ Erro ao carregar lista de processados: {str(e)}")

    def save_processed_file(self, file_path):
        """Salva arquivo na lista de processados"""
        try:
            self.processed_files.add(file_path)
            processed_file = os.path.join(
                os.path.dirname(__file__), 'processed_files.txt')
            with open(processed_file, 'a', encoding='utf-8') as f:
                f.write(file_path + '\n')
        except Exception as e:
            self.log_message(
                f"⚠️ Erro ao salvar na lista de processados: {str(e)}")

    def is_file_processed(self, file_path):
        """Verifica se arquivo já foi processado"""
        return file_path in self.processed_files

    def is_file_processing(self, file_path):
        """Verifica se arquivo está sendo processado"""
        return file_path in self.processing_files

    def log_message(self, message):
        """Log message and update GUI if callback provided"""
        self.logger.info(message)
        if self.log_callback:
            self.log_callback(
                f"{datetime.now().strftime('%H:%M:%S')} - {message}")

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path

            # Verificar se não é arquivo da pasta processados
            if 'processados' in file_path:
                return

            # Verificar se já foi processado ou está sendo processado
            if self.is_file_processed(file_path) or self.is_file_processing(file_path):
                self.log_message(
                    f"⏭️ Arquivo já processado, ignorando: {os.path.basename(file_path)}")
                return

            self.log_message(
                f"📄 Novo arquivo detectado: {os.path.basename(file_path)}")
            time.sleep(2)
            self.upload_file(file_path)

    def on_moved(self, event):
        """Detecta quando um arquivo é movido para a pasta"""
        if not event.is_directory:
            file_path = event.dest_path

            # Verificar se não é arquivo da pasta processados
            if 'processados' in file_path:
                return

            # Verificar se já foi processado ou está sendo processado
            if self.is_file_processed(file_path) or self.is_file_processing(file_path):
                self.log_message(
                    f"⏭️ Arquivo já processado, ignorando: {os.path.basename(file_path)}")
                return

            self.log_message(
                f"📁 Arquivo movido para pasta: {os.path.basename(file_path)}")
            time.sleep(2)
            self.upload_file(file_path)

    def is_valid_document(self, file_path):
        """Verifica se o arquivo é um documento válido para o Paperless"""
        valid_extensions = {'.pdf', '.png', '.jpg',
                            '.jpeg', '.tiff', '.tif', '.txt', '.doc', '.docx'}
        file_extension = Path(file_path).suffix.lower()
        return file_extension in valid_extensions

    def upload_file(self, file_path):
        """Upload do arquivo para o Paperless"""
        try:
            # Verificar novamente se já foi processado (dupla verificação)
            if self.is_file_processed(file_path):
                self.log_message(
                    f"⏭️ Arquivo já foi processado anteriormente: {os.path.basename(file_path)}")
                return

            # Marcar como sendo processado
            self.processing_files.add(file_path)

            if not self.is_valid_document(file_path):
                self.log_message(
                    f"🚫 Arquivo ignorado (formato não suportado): {os.path.basename(file_path)}")
                self.processing_files.discard(file_path)
                return

            if not os.path.exists(file_path):
                self.log_message(f"❓ Arquivo não encontrado: {file_path}")
                self.processing_files.discard(file_path)
                return

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                self.log_message(
                    f"📭 Arquivo vazio ignorado: {os.path.basename(file_path)}")
                self.processing_files.discard(file_path)
                return

            self.log_message(
                f"⬆️ Enviando arquivo: {os.path.basename(file_path)} ({file_size} bytes)")

            with open(file_path, 'rb') as file:
                files = {'document': (os.path.basename(
                    file_path), file, 'application/octet-stream')}

                upload_url = f'{self.paperless_url}/api/documents/post_document/'

                response = requests.post(
                    upload_url,
                    files=files,
                    headers=self.headers,
                    timeout=60
                )

            if response.status_code == 200:
                self.log_message(
                    f"✅ Arquivo enviado com sucesso: {os.path.basename(file_path)}")

                # Marcar como processado ANTES de mover
                self.save_processed_file(file_path)

                # Mover arquivo
                self.move_processed_file(file_path)
            else:
                self.log_message(
                    f"❌ Erro ao enviar {os.path.basename(file_path)}: HTTP {response.status_code}")
                if response.text:
                    self.log_message(
                        f"Detalhes do erro: {response.text[:200]}")

            # Remover da lista de processamento
            self.processing_files.discard(file_path)

        except requests.exceptions.RequestException as e:
            self.log_message(
                f"❌ Erro de conexão ao enviar {os.path.basename(file_path)}: {str(e)}")
            self.processing_files.discard(file_path)
        except Exception as e:
            self.log_message(
                f"❌ Erro inesperado ao processar {os.path.basename(file_path)}: {str(e)}")
            self.processing_files.discard(file_path)

    def move_processed_file(self, file_path):
        """Move arquivo processado para subpasta"""
        try:
            processed_folder = os.path.join(
                os.path.dirname(file_path), 'processados')
            os.makedirs(processed_folder, exist_ok=True)

            filename = os.path.basename(file_path)
            new_path = os.path.join(processed_folder, filename)

            if os.path.exists(new_path):
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_path = os.path.join(
                    processed_folder, f"{name}_{timestamp}{ext}")

            os.rename(file_path, new_path)
            self.log_message(
                f"📂 Arquivo movido para: processados/{os.path.basename(new_path)}")

            # Atualizar o caminho na lista de processados
            self.processed_files.discard(file_path)  # Remove caminho antigo
            self.save_processed_file(new_path)  # Adiciona novo caminho

        except Exception as e:
            self.log_message(f"⚠️ Não foi possível mover o arquivo: {str(e)}")
            # Mesmo se não conseguir mover, mantém na lista de processados


class PaperlessMonitorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Paperless Auto Uploader - Configuração")
        self.root.geometry("650x600")
        self.root.resizable(True, True)

        self.observer = None
        self.config = ConfigParser()
        self.config_file = 'config.ini'
        self.is_background_mode = False
        self.tray_icon = None

        self.load_config()
        self.create_widgets()
        self.load_saved_config()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Título
        title_label = ttk.Label(main_frame, text="🔧 Configuração do Paperless Auto Uploader",
                                font=('TkDefaultFont', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Frame de configurações
        config_frame = ttk.LabelFrame(
            main_frame, text="Configurações", padding="15")
        config_frame.grid(row=1, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=(0, 15))

        # URL do servidor
        ttk.Label(config_frame, text="🌐 Servidor Paperless:").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value="https://docs.dantaseletro.tv")
        url_entry = ttk.Entry(
            config_frame, textvariable=self.url_var, width=55, font=('TkDefaultFont', 10))
        url_entry.grid(row=0, column=1, sticky=(
            tk.W, tk.E), pady=5, padx=(10, 0))

        # Token da API
        ttk.Label(config_frame, text="🔑 Token da API:").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(config_frame, textvariable=self.token_var,
                                show="*", width=55, font=('TkDefaultFont', 10))
        token_entry.grid(row=1, column=1, sticky=(
            tk.W, tk.E), pady=5, padx=(10, 0))

        # Pasta para monitorar
        ttk.Label(config_frame, text="📁 Pasta a monitorar:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        folder_frame = ttk.Frame(config_frame)
        folder_frame.grid(row=2, column=1, sticky=(
            tk.W, tk.E), pady=5, padx=(10, 0))

        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(
            folder_frame, textvariable=self.folder_var, width=45, font=('TkDefaultFont', 10))
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="Procurar", command=self.browse_folder).pack(
            side=tk.RIGHT, padx=(10, 0))

        # Frame de testes
        test_frame = ttk.LabelFrame(
            main_frame, text="Verificação", padding="15")
        test_frame.grid(row=2, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=(0, 15))

        test_button = ttk.Button(
            test_frame, text="🔍 Testar Conexão", command=self.test_connection)
        test_button.pack(side=tk.LEFT, padx=(0, 10))

        save_button = ttk.Button(
            test_frame, text="💾 Salvar Configurações", command=self.save_config)
        save_button.pack(side=tk.LEFT)

        # Frame de controle principal
        control_frame = ttk.LabelFrame(
            main_frame, text="Controle do Monitoramento", padding="15")
        control_frame.grid(row=3, column=0, columnspan=2,
                           sticky=(tk.W, tk.E), pady=(0, 15))

        # Botões de controle em três linhas
        buttons_frame1 = ttk.Frame(control_frame)
        buttons_frame1.pack(fill=tk.X, pady=(0, 10))

        self.start_button = ttk.Button(buttons_frame1, text="▶️ Iniciar Monitoramento",
                                       command=self.start_monitoring, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(buttons_frame1, text="⏹️ Parar Monitoramento",
                                      command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        buttons_frame2 = ttk.Frame(control_frame)
        buttons_frame2.pack(fill=tk.X, pady=(0, 10))

        self.process_existing_button = ttk.Button(buttons_frame2, text="📂 Processar Arquivos Existentes",
                                                  command=self.manual_process_existing)
        self.process_existing_button.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_processed_button = ttk.Button(buttons_frame2, text="🧹 Limpar Lista de Processados",
                                                 command=self.clear_processed_list)
        self.clear_processed_button.pack(side=tk.LEFT)

        buttons_frame3 = ttk.Frame(control_frame)
        buttons_frame3.pack(fill=tk.X)

        self.background_button = ttk.Button(buttons_frame3, text="🚀 Executar em Background",
                                            command=self.go_to_background, state=tk.DISABLED,
                                            style='Accent.TButton')
        self.background_button.pack(side=tk.LEFT, padx=(0, 10))

        self.show_button = ttk.Button(buttons_frame3, text="👁️ Mostrar Interface",
                                      command=self.show_interface, state=tk.DISABLED)
        self.show_button.pack(side=tk.LEFT)

        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, pady=10)

        self.status_var = tk.StringVar(value="⏸️ Aguardando configuração...")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                 font=('TkDefaultFont', 10, 'bold'))
        status_label.pack()

        # Log
        log_frame = ttk.LabelFrame(
            main_frame, text="Log de Atividades", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=(10, 0))

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(text_frame, height=12,
                                wrap=tk.WORD, font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        config_frame.columnconfigure(1, weight=1)

    def browse_folder(self):
        folder = filedialog.askdirectory(
            title="Escolha a pasta para monitorar")
        if folder:
            self.folder_var.set(folder)

    def log_to_gui(self, message):
        """Adiciona mensagem ao log da GUI"""
        if self.log_text:
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.root.update_idletasks()

    def test_connection(self):
        """Testa a conexão com o servidor Paperless"""
        try:
            url = self.url_var.get().strip().rstrip('/')
            token = self.token_var.get().strip()

            if not url or not token:
                messagebox.showerror(
                    "Erro", "Preencha a URL do servidor e o token da API")
                return

            self.log_to_gui("🔍 Testando conexão...")
            headers = {'Authorization': f'Token {token}'}
            response = requests.get(
                f'{url}/api/documents/', headers=headers, timeout=10)

            if response.status_code == 200:
                messagebox.showinfo(
                    "✅ Sucesso", "Conexão com o Paperless estabelecida com sucesso!")
                self.log_to_gui("✅ Teste de conexão bem-sucedido")
            else:
                messagebox.showerror(
                    "❌ Erro", f"Falha na conexão: HTTP {response.status_code}")
                self.log_to_gui(
                    f"❌ Teste de conexão falhou: HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao testar conexão: {str(e)}")
            self.log_to_gui(f"❌ Erro no teste de conexão: {str(e)}")

    def clear_processed_list(self):
        """Limpa a lista de arquivos processados"""
        try:
            response = messagebox.askyesno(
                "Limpar Lista",
                "Tem certeza que deseja limpar a lista de arquivos processados?\n\n"
                "⚠️ Isso fará com que arquivos já enviados possam ser enviados novamente."
            )

            if response:
                # Limpar arquivo de controle
                processed_file = os.path.join(
                    os.path.dirname(__file__), 'processed_files.txt')
                if os.path.exists(processed_file):
                    os.remove(processed_file)

                # Limpar lista em memória se uploader existe
                if hasattr(self, 'uploader'):
                    self.uploader.processed_files.clear()

                self.log_to_gui("🧹 Lista de arquivos processados foi limpa")
                messagebox.showinfo(
                    "Sucesso", "Lista de arquivos processados foi limpa!")

        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao limpar lista: {str(e)}")
            self.log_to_gui(f"❌ Erro ao limpar lista: {str(e)}")

    def manual_process_existing(self):
        """Processa arquivos existentes manualmente"""
        try:
            url = self.url_var.get().strip()
            token = self.token_var.get().strip()
            folder = self.folder_var.get().strip()

            if not all([url, token, folder]):
                messagebox.showerror(
                    "❌ Erro", "Preencha todos os campos obrigatórios primeiro")
                return

            if not os.path.exists(folder):
                messagebox.showerror(
                    "❌ Erro", "A pasta especificada não existe")
                return

            # Criar uploader temporário se não existir
            if not hasattr(self, 'uploader'):
                self.uploader = PaperlessUploader(
                    url, token, folder, self.log_to_gui)

            self.process_existing_files(folder)

        except Exception as e:
            messagebox.showerror(
                "❌ Erro", f"Erro ao processar arquivos: {str(e)}")
            self.log_to_gui(f"❌ Erro ao processar arquivos: {str(e)}")

    def process_existing_files(self, folder):
        """Processa arquivos que já existem na pasta"""
        try:
            self.log_to_gui("📂 Verificando arquivos existentes na pasta...")

            # Buscar arquivos na pasta principal (excluindo pasta processados)
            files_found = []
            for file_path in Path(folder).iterdir():
                if (file_path.is_file() and
                    self.uploader.is_valid_document(str(file_path)) and
                    not self.uploader.is_file_processed(str(file_path)) and
                        'processados' not in str(file_path)):
                    files_found.append(str(file_path))

            if files_found:
                self.log_to_gui(
                    f"📄 Encontrados {len(files_found)} arquivo(s) existente(s)")

                # Perguntar se quer processar arquivos existentes
                response = messagebox.askyesno(
                    "Arquivos Existentes",
                    f"Encontrei {len(files_found)} arquivo(s) na pasta.\n\n"
                    "Deseja enviar estes arquivos existentes para o Paperless?\n\n"
                    "• SIM: Envia arquivos existentes + monitora novos\n"
                    "• NÃO: Apenas monitora arquivos novos"
                )

                if response:
                    # Processar arquivos existentes em thread separada
                    def process_files():
                        for file_path in files_found:
                            self.uploader.upload_file(file_path)
                            time.sleep(1)  # Pausa entre uploads

                    process_thread = threading.Thread(
                        target=process_files, daemon=True)
                    process_thread.start()
                else:
                    self.log_to_gui(
                        "⏭️ Ignorando arquivos existentes, apenas monitorando novos")
            else:
                self.log_to_gui("📭 Nenhum arquivo válido encontrado na pasta")

        except Exception as e:
            self.log_to_gui(
                f"❌ Erro ao verificar arquivos existentes: {str(e)}")

    def start_monitoring(self):
        """Inicia o monitoramento da pasta"""
        try:
            url = self.url_var.get().strip()
            token = self.token_var.get().strip()
            folder = self.folder_var.get().strip()

            if not all([url, token, folder]):
                messagebox.showerror(
                    "❌ Erro", "Preencha todos os campos obrigatórios")
                return

            if not os.path.exists(folder):
                messagebox.showerror(
                    "❌ Erro", "A pasta especificada não existe")
                return

            self.uploader = PaperlessUploader(
                url, token, folder, self.log_to_gui)

            # Verificar e processar arquivos existentes primeiro
            self.process_existing_files(folder)

            # Configurar observer para novos arquivos
            self.observer = Observer()
            self.observer.schedule(self.uploader, folder, recursive=True)

            def start_observer():
                self.observer.start()
                self.log_to_gui(
                    f"🔍 Monitoramento de novos arquivos iniciado em: {folder}")
                self.log_to_gui(
                    "💡 Agora qualquer arquivo novo será enviado automaticamente")
                self.status_var.set("🟢 Monitoramento ATIVO")

                try:
                    while self.observer.is_alive():
                        time.sleep(1)
                except:
                    pass

            self.observer_thread = threading.Thread(
                target=start_observer, daemon=True)
            self.observer_thread.start()

            # Atualizar interface
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.background_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror(
                "❌ Erro", f"Erro ao iniciar monitoramento: {str(e)}")
            self.log_to_gui(f"❌ Erro ao iniciar: {str(e)}")

    def stop_monitoring(self):
        """Para o monitoramento"""
        try:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5)
                self.log_to_gui("🛑 Monitoramento interrompido")
                self.status_var.set("🔴 Monitoramento PARADO")

            # Atualizar interface
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.background_button.config(state=tk.DISABLED)
            self.show_button.config(state=tk.DISABLED)

        except Exception as e:
            self.log_to_gui(f"❌ Erro ao parar: {str(e)}")

    def create_tray_icon(self):
        """Cria ícone na bandeja do sistema"""
        # Criar uma imagem simples para o ícone
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        draw.text((20, 25), "P", fill='blue')

        # Menu do ícone da bandeja
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar Interface", self.show_interface),
            pystray.MenuItem("Parar Monitoramento", self.stop_monitoring),
            pystray.MenuItem("Sair", self.quit_app)
        )

        self.tray_icon = pystray.Icon("PaperlessUploader", image, menu=menu)
        return self.tray_icon

    def go_to_background(self):
        """Envia o programa para background"""
        try:
            self.is_background_mode = True
            self.log_to_gui("🚀 Executando em background...")
            self.log_to_gui("💡 Use o ícone na bandeja para acessar o programa")

            # Criar ícone na bandeja
            icon = self.create_tray_icon()

            # Ocultar janela
            self.root.withdraw()

            # Atualizar botões
            self.background_button.config(state=tk.DISABLED)
            self.show_button.config(state=tk.NORMAL)

            # Executar ícone da bandeja em thread separada
            def run_tray():
                icon.run()

            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()

            # Mostrar notificação
            if self.tray_icon:
                self.tray_icon.notify("Paperless Auto Uploader rodando em background",
                                      "Clique no ícone para acessar")

        except Exception as e:
            self.log_to_gui(f"❌ Erro ao ir para background: {str(e)}")
            messagebox.showerror(
                "Erro", f"Erro ao executar em background: {str(e)}")

    def show_interface(self):
        """Mostra a interface novamente"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.is_background_mode = False
            self.log_to_gui("👁️ Interface restaurada")

        except Exception as e:
            self.log_to_gui(f"❌ Erro ao mostrar interface: {str(e)}")

    def quit_app(self):
        """Fecha completamente o aplicativo"""
        self.stop_monitoring()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        sys.exit()

    def save_config(self):
        """Salva as configurações"""
        try:
            self.config['DEFAULT'] = {
                'paperless_url': self.url_var.get(),
                'api_token': self.token_var.get(),
                'monitor_folder': self.folder_var.get()
            }

            with open(self.config_file, 'w') as f:
                self.config.write(f)

            messagebox.showinfo(
                "✅ Sucesso", "Configurações salvas com sucesso!")
            self.log_to_gui("💾 Configurações salvas")

        except Exception as e:
            messagebox.showerror(
                "❌ Erro", f"Erro ao salvar configurações: {str(e)}")

    def load_config(self):
        """Carrega as configurações salvas"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")

    def load_saved_config(self):
        """Carrega configurações na interface"""
        try:
            if 'DEFAULT' in self.config:
                config = self.config['DEFAULT']
                self.url_var.set(config.get(
                    'paperless_url', 'https://docs.dantaseletro.tv'))
                self.token_var.set(config.get('api_token', ''))
                self.folder_var.set(config.get('monitor_folder', ''))
        except Exception as e:
            print(f"Erro ao carregar configurações na interface: {e}")

    def on_closing(self):
        """Executado quando a janela é fechada"""
        if self.is_background_mode and self.observer and self.observer.is_alive():
            # Se está em background e monitorando, apenas oculta
            self.root.withdraw()
        else:
            # Senão, fecha tudo
            self.quit_app()

    def run(self):
        """Executa a aplicação"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Mensagem inicial
        self.log_to_gui("📄 Paperless Auto Uploader iniciado")
        self.log_to_gui("📝 Configure o token da API e a pasta para monitorar")
        self.log_to_gui("🔗 Servidor: docs.dantaseletro.tv")
        self.log_to_gui("═" * 50)

        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = PaperlessMonitorGUI()
        app.run()
    except KeyboardInterrupt:
        print("Programa interrompido pelo usuário")
    except Exception as e:
        print(f"Erro fatal: {e}")
        input("Pressione Enter para sair...")

#!/bin/bash
# setup_server.sh - Script de instalação para Ubuntu na Oracle Cloud

echo "🚀 Iniciando a preparação do servidor para o Vagas Bot..."

# Atualizar pacotes do sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências básicas
sudo apt install -y python3 python3-pip python3-venv git htop

# Navegar para o diretório do projeto (assumindo que o script é rodado dentro da pasta vagas_bot)
cd "$(dirname "$0")/.."

# Criar um ambiente virtual Python
echo "🐍 Criando ambiente virtual..."
python3 -m venv venv

# Ativar o ambiente virtual e instalar dependências
echo "📦 Instalando bibliotecas..."
source venv/bin/activate
pip install -r requirements.txt

echo "✅ Servidor preparado com sucesso!"
echo "O Vagas Bot já pode ser executado manualmente com: source venv/bin/activate && python bot.py"

import subprocess
import time
import sys

def main():
    print("=========================================")
    print("🚀 INICIANDO BOT NATIVO E SERVIDOR WEB 🚀")
    print("=========================================")
    
    print("\n[1/2] Acordando o Sniper Bot (Telegram)...")
    bot_process = subprocess.Popen(
        [sys.executable, "bot.py"]
    )

    print("\n[2/2] Acordando o Servidor Web (FastAPI)...")
    app_process = subprocess.Popen(
        [sys.executable, "app.py"]
    )

    print("\n=======================================================")
    print("TUDO PRONTO! O ECOSSISTEMA NATIVO ESTÁ NO AR.")
    print("Vá no Telegram, abra seu bot e mande /start")
    print("Para DESLIGAR tudo, apenas feche esta janela preta ou pressione Ctrl+C.")
    print("=======================================================\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDesligando sistema de forma manual (Ctrl+C)...")
    except Exception as e:
        print(f"\nQueda detectada no sistema: {e}")
    finally:
        print("Encerrando subprocessos...")
        bot_process.terminate()
        app_process.terminate()
        bot_process.wait()
        app_process.wait()
        print("Serviços encerrados.")
        print("Volte sempre!")

if __name__ == "__main__":
    main()

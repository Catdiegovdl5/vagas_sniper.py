import subprocess
import time
import sys

def main():
    print("=========================================")
    print("🚀 INICIANDO BOT NATIVO DO TELEGRAM 🚀")
    print("=========================================")
    
    print("\n[1/1] Acordando o Sniper Bot (Telegram)...")
    
    bot_process = subprocess.Popen(
        [sys.executable, "bot.py"]
    )

    print("\n=======================================================")
    print("TUDO PRONTO! O ECOSSISTEMA NATIVO ESTÁ NO AR.")
    print("Vá no Telegram, abra seu bot e mande /start")
    print("Para DESLIGAR tudo, apenas feche esta janela preta.")
    print("=======================================================\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDesligando sistema de forma manual (Ctrl+C)...")
    except Exception as e:
        print(f"\nQueda detectada no sistema: {e}")
    finally:
        bot_process.terminate()
        print("Serviços encerrados.")
        print("Volte sempre!")

if __name__ == "__main__":
    main()

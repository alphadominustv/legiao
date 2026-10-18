"""Servidor da Legião Alpha no Render (só biblioteca padrão do Python).

  POST /legiao  webhook do bot da Legião: botões ✅/❌, o motivo da recusa, /agenda, /reenviar, /aprovartudo e /id
  GET  /tick    o cron-job.org abre de 5 em 5 minutos: gera o Reel/carrossel no horário (legiao.yml)
                e manda a Íris postar o que já foi aprovado e chegou a hora (iris.yml)
  GET  /        "ok" (para saber se está no ar)

Variáveis no Render: LEGIAO_TELEGRAM_TOKEN, LEGIAO_CHAT_ID, GITHUB_TOKEN (token com acesso ao repositório
alphadominustv/legiao: Contents e Actions, leitura e escrita), GITHUB_REPOSITORY=alphadominustv/legiao.
"""
import hashlib
import json
import os
import sys
import threading
import time
import urllib.request
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "legiao"))
os.environ.setdefault("GITHUB_REPOSITORY", "alphadominustv/legiao")
os.environ.setdefault("RENDER", "1")

import gatilho  # noqa: E402
import publicar  # noqa: E402

TOKEN = os.environ.get("LEGIAO_TELEGRAM_TOKEN", "")
SEGREDO = hashlib.sha256(("legiao" + TOKEN).encode()).hexdigest()[:32]
_ultimo_tick = [0.0]
_trava = threading.Lock()


def log(texto):
    print(datetime.now().strftime("%H:%M:%S"), texto, flush=True)


def postar_o_que_venceu():
    """Post aprovado cuja hora já chegou: pede para a Íris postar (ela posta e avisa no Telegram)."""
    agora = datetime.now(publicar.BRT)
    for dia in (agora.strftime("%Y-%m-%d"), (agora - timedelta(days=1)).strftime("%Y-%m-%d")):
        for pasta in (dia, f"{dia}-reel"):
            status, _ = publicar.ler_status(pasta)
            if not status or status.get("status") != "aprovado":
                continue
            hora = datetime.strptime(dia, "%Y-%m-%d").replace(hour=int(status.get("horario", 18)), tzinfo=publicar.BRT)
            if agora >= hora:
                publicar.disparar("iris.yml")
                log(f"Íris chamada para postar {pasta}.")
                return


def ciclo():
    if not _trava.acquire(blocking=False):
        return
    try:
        gatilho.main()
        postar_o_que_venceu()
    except Exception as e:
        log(f"Erro no ciclo: {e}")
    finally:
        _trava.release()


class Atendente(BaseHTTPRequestHandler):
    def _responder(self, codigo, texto="ok"):
        corpo = texto.encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.startswith("/tick"):
            if time.time() - _ultimo_tick[0] >= 240:  # no máximo 1 ciclo a cada 4 minutos
                _ultimo_tick[0] = time.time()
                threading.Thread(target=ciclo, daemon=True).start()
            self._responder(200)
            return
        self._responder(200, "Legião no ar.")

    def do_HEAD(self):
        self._responder(200)

    def do_POST(self):
        if self.path != "/legiao" or self.headers.get("X-Telegram-Bot-Api-Secret-Token") != SEGREDO:
            self._responder(403, "nao")
            return
        tamanho = int(self.headers.get("Content-Length") or 0)
        try:
            update = json.loads(self.rfile.read(tamanho) or b"{}")
        except ValueError:
            update = {}
        self._responder(200)
        try:
            publicar.tratar_update(update)
        except Exception as e:
            log(f"Erro tratando clique/mensagem: {e}")

    def log_message(self, *args):
        pass


def telegram(metodo, dados):
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{metodo}", json.dumps(dados).encode(),
                                 {"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).close()


def ligar_webhook():
    base = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not (TOKEN and base):
        log("Sem LEGIAO_TELEGRAM_TOKEN ou RENDER_EXTERNAL_URL: webhook não ligado.")
        return
    try:
        telegram("setWebhook", {"url": base.rstrip("/") + "/legiao", "secret_token": SEGREDO,
                                "allowed_updates": ["message", "callback_query"]})
        comandos = [{"command": "agenda", "description": "O que já está gerado e agendado"},
                    {"command": "reenviar", "description": "Manda de novo o que espera aprovação"},
                    {"command": "aprovartudo", "description": "Aprova tudo que espera aprovação"},
                    {"command": "id", "description": "Mostra o Id deste chat"}]
        for escopo in ({"type": "default"}, {"type": "all_group_chats"}):
            telegram("setMyCommands", {"commands": comandos, "scope": escopo})
        log(f"Webhook da Legião ligado em {base}/legiao.")
    except Exception as e:
        log(f"Não consegui ligar o webhook: {e}")


if __name__ == "__main__":
    faltam = [n for n in ("LEGIAO_TELEGRAM_TOKEN", "LEGIAO_CHAT_ID", "GITHUB_TOKEN") if not os.environ.get(n)]
    if faltam:
        log(f"ATENÇÃO: faltam as variáveis {', '.join(faltam)}.")
    ligar_webhook()
    porta = int(os.environ.get("PORT", "10000"))
    log(f"Servidor da Legião na porta {porta}.")
    ThreadingHTTPServer(("0.0.0.0", porta), Atendente).serve_forever()

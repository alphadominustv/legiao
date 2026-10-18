# Legião Alpha

Time de agentes que faz o Reel e o carrossel diários do Alpha Dominus e posta no Instagram e no Facebook,
depois que alguém do grupo aprova no Telegram.

- **legiao/**: Odin (tema), Bragi (texto), Atena (revisa), Hefesto (arte) e Íris (posta).
- **servidor.py**: roda no Render e atende os botões ✅/❌, o motivo da recusa, `/agenda`, `/reenviar` (manda de novo o que espera aprovação), `/aprovartudo` e `/id`.
  O endereço `/tick` é chamado pelo cron-job.org a cada 5 minutos: gera os posts no horário e posta o que já foi aprovado.
- **Branch legiao-posts**: cada post gerado (imagens, vídeo, texto e situação). O Instagram lê as imagens
  daqui, por isso o repositório é público. Os segredos ficam guardados nas configurações e não aparecem.

## Horários (legiao/config.json)
Reel: gera às 9h e posta às 12h. Carrossel: gera às 15h e posta às 18h. Quem aprova depois do horário vê o post sair na hora.

## Segredos do repositório (Settings > Secrets and variables > Actions)
LEGIAO_TELEGRAM_TOKEN, LEGIAO_CHAT_ID, GEMINI_LEGIAO_KEY, GOOGLE_SA_JSON, META_PAGE_TOKEN, META_PAGE_ID, IG_USER_ID.
Opcionais: ADMIN_ID (aviso de reserva se o bot da Legião falhar) e CLAUDE_CODE_OAUTH_TOKEN (reserva se o Gemini falhar).

## Render (Web Service)
Build: `pip install -r requirements.txt` · Start: `python3 servidor.py`
Variáveis: LEGIAO_TELEGRAM_TOKEN, LEGIAO_CHAT_ID, GITHUB_TOKEN (token com acesso a este repositório:
Contents e Actions, leitura e escrita), GITHUB_REPOSITORY=alphadominustv/legiao.

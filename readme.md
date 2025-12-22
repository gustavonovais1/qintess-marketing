# Qintess Marketing

Projeto para automação de coleta de métricas do LinkedIn e exposição de APIs do Instagram. Inclui:
- Bot headful do LinkedIn com VNC/noVNC para visualizar a automação em tempo real
- API FastAPI com Swagger para consultar perfil, mídia e insights do Instagram
- Banco PostgreSQL para persistência (schemas `linkedin` e `instagram`)


## Visão Geral
- Serviço `linkedin`: executa o módulo `bot.linkedin.src.main` que navega na área de analytics da empresa no LinkedIn, exporta relatórios (Excel) e faz ingestão para o banco (`docker-compose.yml:4-22`, `Dockerfile:18-25`, `bot\\linkedin\\src\\main.py:10-20`).
- Serviço `instagram`: inicializa a API FastAPI em `:8000` (`main.py:4-12`) e publica endpoints sob prefixos `/ig` e `/ll` (`api\\api.py:5-7`). O endpoint `/ll/start` aciona o bot do LinkedIn de forma programática (`api\\endpoints\\linkedin.py:6-8`).
- Interface visual: VNC no `:5900` e noVNC no `:6080` são inicializados pelo script de entrada (`start.sh:9-13`). Útil para acompanhar login e navegação do bot.


## Tecnologias
- Python (Playwright, FastAPI, SQLAlchemy, Requests, Pandas)
- Docker + Docker Compose
- PostgreSQL 13 (volume `db_data`)
- Xvfb, x11vnc, Fluxbox, noVNC, Websockify


## Pré-requisitos
- `Docker` e `Docker Compose` instalados
- Arquivo `.env` com variáveis necessárias (exemplo):

Consulte `env_example` na raiz do projeto e copie para `.env`, ajustando valores.

Os serviços leem essas variáveis via `env_file: .env` e `environment` (`docker-compose.yml:10-22`, `docker-compose.yml:26-48`).


## Executando
- Bot do LinkedIn:
```
docker compose up --build linkedin
```

- API + Swagger (Instagram + endpoint para iniciar bot):
```
docker compose up --build instagram
```

Observações:
- As portas `5900` (VNC) e `6080` (noVNC) são mapeadas em ambos os serviços; suba um de cada vez para evitar conflitos de porta (`docker-compose.yml:6-9`, `docker-compose.yml:31-34`).
- Os relatórios exportados pelo bot são salvos e montados em `./bot/linkedin/downloads` no host (`docker-compose.yml:8`, `Dockerfile:16-20`, `bot\\linkedin\\src\\profile.py:457-491`).


## Ver o Bot no VNC/noVNC
- VNC (cliente desktop): conecte em `localhost:5900` (sem senha, ambiente de dev).
- noVNC (navegador): abra `http://localhost:6080/` ou `http://localhost:6080/vnc_auto.html`.
- O ambiente gráfico é inicializado pelo `start.sh` com Xvfb, x11vnc e websockify (`start.sh:4-13`).
- Primeira execução: faça login no LinkedIn pela sessão VNC; o estado de sessão é salvo (`bot\\linkedin\\src\\auth.py:162-211`).


## Swagger da API
- Com o serviço `instagram` ativo, acesse:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

Principais endpoints:
- `GET /ig/profile` — perfil do Instagram (`api\\endpoints\\instagram.py:6-8`)
- `GET /ig/media` — lista de mídias com filtros (`api\\endpoints\\instagram.py:10-15`)
- `GET /ig/insights/profile` — métricas agregadas (perfil) (`api\\endpoints\\instagram.py:17-19`)
- `GET /ig/insights/posts` — métricas por mídia (`api\\endpoints\\instagram.py:21-32`)
- `POST /ll/start?segments=updates,visitors,...` — inicia bot do LinkedIn (`api\\endpoints\\linkedin.py:6-8`)

## Google Analytics (GA4)
- Prefixo: `/ga`. Endpoints sob `/ga/analytics/*` (autenticados).
- Variável de ambiente obrigatória: `GA4_PROPERTY_ID`.
- SDK: `google-analytics-data==0.18.0`.
- Endpoints principais:
  - `GET /ga/analytics/engagement`
    - `metrics`: `engagedSessions,engagementRate,averageSessionDuration,userEngagementDuration,eventsPerSession,sessionKeyEventRate,userKeyEventRate,scrolledUsers`
    - `dimensions`: `date,deviceCategory,country`
  - `GET /ga/analytics/users`
    - `metrics`: `activeUsers,newUsers,totalUsers,active1DayUsers,active7DayUsers,active28DayUsers,dauPerMau,dauPerWau,wauPerMau`
    - `dimensions`: `date,country,deviceCategory`
  - `GET /ga/analytics/events`
    - `metrics`: `eventCount,eventCountPerUser,eventValue,keyEvents`
    - `dimensions`: `date,eventName,pagePath`
  - `GET /ga/analytics/content`
    - `metrics`: `screenPageViews,screenPageViewsPerSession,screenPageViewsPerUser,bounceRate`
    - `dimensions`: `date,pageTitle,pagePath`
  - `GET /ga/analytics/ads` (advertiser)
    - `metrics`: `advertiserAdClicks,advertiserAdImpressions,advertiserAdCost,advertiserAdCostPerClick`
    - `dimensions`: `date,campaignName,campaignId`
    - Compatibilidade: métricas `publisher*` e dimensões de inventário não são permitidas aqui.
  - `GET /ga/analytics/promotions`
    - `metrics`: `promotionViews,promotionClicks,itemPromotionClickThroughRate,itemsClickedInPromotion,itemsViewedInPromotion,itemListViewEvents,itemListClickEvents,itemListClickThroughRate,itemsClickedInList`
    - `dimensions`: `date,sessionDefaultChannelGroup`
  - `GET /ga/analytics/ecommerce/items`
    - `metrics`: `itemsPurchased,itemsViewed,itemsAddedToCart,itemsCheckedOut,itemRevenue,itemDiscountAmount,grossItemRevenue`
    - `dimensions`: `date,itemId,itemName,itemCategory`
  - `GET /ga/analytics/ecommerce/revenue`
    - `metrics`: `ecommercePurchases,purchaseRevenue,grossPurchaseRevenue,totalRevenue,transactions,transactionsPerPurchaser,averagePurchaseRevenue,averagePurchaseRevenuePerPayingUser,averagePurchaseRevenuePerUser,averageRevenuePerUser,purchaserRate,firstTimePurchasers,firstTimePurchaserRate,firstTimePurchasersPerNewUser`
    - `dimensions`: `date,sessionDefaultChannelGroup`
  - `GET /ga/analytics/ecommerce/funnel`
    - `metrics`: `addToCarts,checkouts,ecommercePurchases,cartToViewRate,purchaseToViewRate`
    - `dimensions`: `date,sessionDefaultChannelGroup`
- Parâmetros comuns:
  - `start_date`, `end_date` (ISO `YYYY-MM-DD`, default: últimos 30 dias)
  - `limit` (default `1000`), `offset` (default `0`)
- Compatibilidade e batching:
  - Validação de combinações métricas/dimensões conforme schema GA4.
  - GA impõe até 10 métricas por requisição; o serviço quebra em lotes e mescla os resultados.
- Rotas removidas:
  - `/ga/analytics/ecommerce` (genérica) e `/ga/analytics/report` (genérica).
  - `/ga/analytics/search` removida por ausência de vínculo Search Console (erros `organicGoogleSearch*`).
- Exemplos:
```
# Engajamento
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/ga/analytics/engagement?metrics=engagedSessions,engagementRate&dimensions=date,deviceCategory&start_date=2025-11-01&end_date=2025-12-01"

# E-commerce Itens
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/ga/analytics/ecommerce/items?metrics=itemsPurchased,itemsViewed&dimensions=date,itemId,itemName"

# Ads (advertiser)
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/ga/analytics/ads?metrics=advertiserAdClicks,advertiserAdImpressions&dimensions=date,campaignName,campaignId"
```


## RD Station Marketing
- Prefixo: `/rd`. Endpoints sob `/rd/*` (autenticados, exceto callback).
- Variáveis de ambiente obrigatórias: `RD_ACCOUNT_ID`, `RD_CLIENT_SECRET`.
- Fluxo OAuth 2.0:
  1. Acesse `GET /rd/auth` no navegador. Isso redirecionará para o login do RD Station.
  2. Após autorizar, o RD Station redirecionará para `http://localhost:8000/rd/oauth/callback` com o código.
  3. O sistema captura o `code`, troca pelo `access_token` e salva no banco de dados (`rd_station.rd_tokens`).
- Endpoints principais:
  - `GET /rd/auth` — Inicia o processo de autenticação (redirecionamento).
  - `GET /rd/oauth/callback` — Recebe o código de autorização do RD Station (automático).
  - `GET /rd/analytics/emails` — Métricas de performance de e-mail (envios, aberturas, cliques). Os dados são persistidos no banco (`rd_station.email_analytics`).
  - `GET /rd/analytics/conversions` — Métricas de conversão e geração de leads por período. Os dados são persistidos no banco (`rd_station.conversion_analytics`).
  - `GET /rd/segmentations` — Lista todas as segmentações de contatos. Os dados são persistidos no banco (`rd_station.segmentations`).
  - `GET /rd/landing_pages` — Lista as Landing Pages ativas. Os dados são persistidos no banco (`rd_station.landing_pages`).
  - `GET /rd/workflows` — Lista os fluxos de automação. Os dados são persistidos no banco (`rd_station.workflows`).
- Exemplos:
```
# Analytics de E-mail
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/rd/analytics/emails?start_date=2025-10-01&end_date=2025-10-31"

# Listar Segmentações
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/rd/segmentations"
```


## Usuários e Autenticação
- Registro: `POST /user/register` cria usuário com `name`, `email`, `password`, `role` (`api\\endpoints\\user.py:16-25`).
- Token para Swagger: `POST /user/token` usa `OAuth2PasswordRequestForm` (`username`=email, `password`) e retorna JWT (`api\\endpoints\\user.py:33-46`).
- Perfil autenticado: `GET /user/me`.
- Lista de usuários: `GET /user/` (requer `role=admin`).
- JWT: gerado e validado em `core\\auth.py` com algoritmo `HS256` e segredo `AUTH_SECRET`.

Fluxo no Swagger:
- Clique em “Authorize”, informe `username` e `password` para obter o token.
- As rotas com cadeado passam o `Authorization: Bearer <jwt>` automaticamente.

Exemplos:
```
# Registrar admin
curl -X POST "http://localhost:8000/user/register" -H "Content-Type: application/json" -d "{\"name\":\"Admin\",\"email\":\"admin@example.com\",\"password\":\"pass\",\"role\":\"admin\"}"

# Obter token (form OAuth2)
curl -X POST "http://localhost:8000/user/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@example.com&password=pass"

# Usar token nas rotas protegidas
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/ig/profile"
curl -H "Authorization: Bearer <jwt>" -X POST "http://localhost:8000/ll/start?segments=updates,visitors"

# Somente admin
curl -H "Authorization: Bearer <jwt>" "http://localhost:8000/user/"
```

### Exemplos rápidos:
```
# Swagger
open http://localhost:8000/docs

# Perfil IG
curl "http://localhost:8000/ig/profile"

# Mídias IG (vídeos entre datas)
curl "http://localhost:8000/ig/media?fields=id,media_type,timestamp&media_type=VIDEO&limit=25&since=1730428800&until=1733110800"

# Insights de perfil IG (janela customizada)
curl "http://localhost:8000/ig/insights/profile?since=1730428800&until=1733110800"

# Iniciar bot LinkedIn para segmentos
curl -X POST "http://localhost:8000/ll/start?segments=updates,visitors,followers,competitors"
```


## Persistência de Dados
- Volume do banco: `db_data` (`docker-compose.yml:62-67`)
- Schemas criados na inicialização: `instagram` e `linkedin` (`db.py:18-22`)
- Exports do LinkedIn ficam em `./bot/linkedin/downloads` e são ingeridos para tabelas como `linkedin.visitors`, `linkedin.followers`, etc. (`models\\models_linkedin.py:18-30`, `models\\models_linkedin.py:59-91`)


## Dicas e Solução de Problemas
- `HEADLESS=false` mantém o navegador visível (VNC) para depuração (`Dockerfile:13-20`, `docker-compose.yml:14`, `docker-compose.yml:46-48`).
- Se `:8000/docs` não abrir, verifique se o serviço `instagram` está ativo (`docker-compose.yml:26-48`, `main.py:13-20`).
- Captcha: opcionalmente configure `ANTI_CAPTCHA_KEY` para auxiliar resolução de reCAPTCHA (`bot\\linkedin\\src\\auth.py:186-211`, `bot\\linkedin\\src\\auth.py:436-450`, `bot\\linkedin\\src\\auth.py:494-568`).


## Licença
Uso interno Qintess. Desenvolvedor responsável pela implementação e manutenção do projeto: Gustavo Novais.

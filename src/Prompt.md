/brainstorming  
Eu quero construir um mapeador de eventos, mais voltado para o mercado brasileito no contexto de viagens corporativas. 

O objetivo principal é que a API retorne todos os eventos dos próximos 6 meses (parametrizável). Precisamos do:
Nome do Evento
Data
Localização
Site ou plataforma para a compra do ingresso

Essa API deve ter um crawler para buscar os eventos além de integrar com APIs de agregadores de eventos como Ticketmaster, [ETC]
Nossa stack será python com fast API rodando numa cloud run. Salvaremos os dados no supabase. E precisamos levantar os seguintes endpoints para o consumo do frontend:

GET /api/health
GET /api/events
GET /api/events/{event_id}
POST /api/events/sync



GET /api/events and GET /api/events/{event_id} already read from SQLite and do not query the web.
GET /api/events returns a full normalized Event array, not summaries.
GET /api/events/{event_id} returns a single Event object with the same granularity as the list.
POST /api/events/sync triggers synchronization and returns an operational summary, not event data.
No pagination currently exists.
Default GET /api/events behavior assumes status=upcoming when status is not provided.
Default sorting is networkingRelevance desc, then startDate asc.

A ideia é que o viajante de uma empresa deseja ir para um determinado evento relacionado ou negócio da empresa. Exemplo:
Os devs de uma empresa viajarão para São Paulo (capital) no evento Campus Party. Ele precisa planejar a viagem na data próxima do evento.

Além disso use como base os codigos de backend (eventnexus_v1)  e front (eventnexus) da pasta old/


Além disso saiba que essa deve ser a conexão do supabase:
# Connect to Supabase via connection pooling
DATABASE_URL="postgresql://postgres.prvljsmnyxvvgzmvsgzz:[YOUR-PASSWORD]@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true"

# Direct connection to the database. Used for migrations
DIRECT_URL="postgresql://postgres.prvljsmnyxvvgzmvsgzz:[YOUR-PASSWORD]@aws-1-sa-east-1.pooler.supabase.com:5432/postgres"
# Auditoria UAN

Aplicação web para **Auditoria Sanitária em Unidades de Alimentação e Nutrição (UAN)**.  
Usada **in loco durante visitas de inspeção** por estagiários de nutrição diretamente no celular.

Substitui planilhas e papéis por um formulário digital inteligente com 65 perguntas, lógica condicional, upload de fotos, cálculo automático de pontuação e geração de relatórios.

---

## Funcionalidades

### Questionário inteligente
- **65 perguntas** distribuídas em **6 módulos**
- **Lógica condicional**: campos aparecem/desaparecem conforme as respostas
- **7 Red Flags** (Falhas Graves) com alerta visual e bloqueio de finalização sem observação
- Navegação entre módulos por abas com indicador de progresso

### Upload de fotos
- Captura diretamente pela câmera do celular
- Preview imediato da imagem
- Upload automático via AJAX

### Salvamento automático
- Auto-save a cada **30 segundos** via AJAX
- Indicador visual "Salvo"
- Recuperação automática ao recarregar

### Pontuação automática
- Cada pergunta tem peso 1 a 5
- Cálculo em tempo real com barra de progresso
- Classificação: Excelente (≥90%), Bom (≥70%), Regular (≥50%), Crítico (<50%)
- **Rebaixamento automático** se houver Red Flag ativa (máximo: Regular)

### Relatórios
- **PDF** (WeasyPrint no Docker; fallback HTML com "Imprimir/Salvar PDF" no Windows)
- **CSV** (UTF-8 BOM, delimitador `;`) compatível com Excel

### Admin
- Dashboard com métricas (total auditorias, média, distribuição por classificação)
- **CRUD usuários** com instituição e endereço
- **Gerenciar perguntas**: criar, editar, excluir, configurar condicionais e Red Flags
- **Editar respostas** de qualquer auditoria (admin reedit)
- **Excluir auditorias** finalizadas ou em andamento
- **Excluir estagiários** (remove auditorias vinculadas)

### Estagiário
- **Nova Auditoria**: um clique — dados da instituição vêm do cadastro
- **Reeditar**: pode alterar respostas mesmo após finalizar (recalcula pontuação)
- **Data automática**: registrada no momento da finalização

### Deploy facilitado
- Docker + Docker Compose prontos para uso

---

## Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+ / Flask |
| Frontend | Jinja2 + HTML5 + JavaScript puro |
| Estilo | Bootstrap 5.3 + CSS customizado mobile-first |
| Banco | SQLite via Flask-SQLAlchemy |
| Autenticação | JWT (Flask-JWT-Extended) em cookies |
| PDF | WeasyPrint (fallback HTML) |
| Upload | Werkzeug FileStorage |
| Deploy | Docker + Docker Compose |
| Server | Gunicorn |

---

## Como executar

### Desenvolvimento

```bash
git clone https://github.com/gustavocaffaro/app-auditoria-uan.git
cd app-auditoria-uan
pip install -r requirements.txt
python run.py
```

Acesse **http://localhost:5000**

### Docker

```bash
docker compose up -d
```

Acesse **http://localhost:8090**

---

## Credenciais padrão

| Tipo | Email | Senha |
|------|-------|-------|
| Admin | admin@uan.com | admin123 |
| Estagiário | estagiario@uan.com | estag123 |

O banco SQLite com seed é criado automaticamente na primeira execução.

---

## Estrutura do Projeto

```
uan-auditoria/
├── run.py                    # Entrypoint dev
├── requirements.txt          # Dependências Python
├── Dockerfile                # Build Docker
├── docker-compose.yml        # Orquestração
├── data/                     # SQLite (auto)
├── app/
│   ├── __init__.py           # Factory + seed
│   ├── config.py             # Configurações
│   ├── extensions.py         # Flask extensions
│   ├── version.py            # Versão do app
│   ├── models/               # User, Module, Question, AuditSession, Response
│   ├── routes/               # auth, audit, admin, export
│   ├── templates/            # Jinja2 (base, login, audit/, admin/, pdf/)
│   └── static/
│       ├── css/app.css
│       ├── js/               # app.js, condicionais.js, fotos.js, score.js
│       ├── uploads/
│       └── logo.png
```

---

## Sistema de Red Flags

| Código | Falha | Módulo |
|--------|-------|--------|
| RF1 | Porta de banheiro abre diretamente para área de preparo | M1 |
| RF2 | Água da torneira sem tratamento para consumo dos residentes | M3 |
| RF3 | Presença de pragas na área de manipulação | M3 |
| RF4 | Animais com acesso à cozinha da instituição | M3 |
| RF5 | Lixo cruza fluxo de preparo dos alimentos | M3 |
| RF6 | Manipuladores usando adornos durante preparo | M4 |
| RF7 | Higienização inadequada de hortifrúti | M5 |

---

## Histórico de Versões

| Versão | Descrição |
|--------|-----------|
| 1.0.0 | App completo com 65 perguntas, 6 módulos, auto-save, PDF, CSV |
| 1.1.0 | Admin gerencia perguntas (criar/editar/excluir), condicionais editáveis |
| 1.2.0 | Force delete perguntas com respostas, admin exclui auditorias |
| 1.3.0 | Admin edita respostas de qualquer auditoria |
| 1.4.0 | Estagiários reeditam próprias auditorias |
| 1.5.0 | Instituição no cadastro do estagiário, nav simplificada |
| 1.5.1 | Excluir estagiário (com auditorias vinculadas) |
| 1.6.0 | Nova auditoria em 1 clique, data automática na finalização |
| 1.6.1 | Logo personalizada no header |

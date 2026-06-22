# 🏥 Auditoria UAN

Aplicação web para **Auditoria Sanitária em Unidades de Alimentação e Nutrição (UAN)**.  
Usada **in loco durante visitas de inspeção** por estagiários de nutrição diretamente no celular.

Substitui planilhas e papéis por um formulário digital inteligente com 65 perguntas, lógica condicional, upload de fotos, cálculo automático de pontuação e geração de relatórios.

---

## ✨ Funcionalidades

### 📋 Questionário inteligente
- **65 perguntas** distribuídas em **6 módulos** (Estrutura Física, Equipamentos, Água/Pragas/Resíduos, Higiene da Equipe, Processo de Alimentos, Gestão/Documentação)
- **Lógica condicional**: campos aparecem/desaparecem conforme as respostas (ex: selecionar "Outro" exibe campo de observação)
- **7 Red Flags** (Falhas Graves) com alerta visual e bloqueio de finalização sem observação
- Navegação entre módulos por abas com indicador de progresso

### 📸 Upload de fotos
- Captura diretamente pela câmera do celular (`capture="environment"`)
- Preview imediato da imagem
- Upload automático via AJAX

### 💾 Salvamento automático
- Auto-save a cada **30 segundos** via AJAX
- Indicador visual "Salvo ✓"
- Recuperação automática ao recarregar a página

### 📊 Pontuação automática
- Cada pergunta tem peso 1 a 5
- Cálculo em tempo real com barra de progresso
- Classificação: Excelente (≥90%), Bom (≥70%), Regular (≥50%), Crítico (<50%)
- **Rebaxamento automático** se houver qualquer Red Flag ativa (máximo: Regular)

### 📄 Relatórios
- **PDF profissional** com header, dados da UAN, pontuação por módulo, lista de respostas, fotos embutidas e red flags em destaque
- **CSV** (UTF-8 BOM, delimitador `;`) compatível com Excel

### 👥 Autenticação e níveis de acesso
- Login com email + senha
- JWT armazenado em cookie HttpOnly
- **Admin**: dashboard com métricas, CRUD de usuários, visualização de todas as auditorias
- **Estagiário**: criar auditorias, responder questionário, ver histórico próprio

### 🐳 Deploy facilitado
- Docker + Docker Compose prontos para uso
- Gunicorn + Nginx (via reverse proxy)
- Imagem otimizada com suporte a WeasyPrint

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+ / Flask |
| Frontend | Jinja2 + HTML5 + JavaScript puro |
| Estilo | Bootstrap 5.3 + CSS customizado mobile-first |
| Banco | SQLite via Flask-SQLAlchemy |
| Autenticação | JWT (Flask-JWT-Extended) em cookies |
| PDF | WeasyPrint |
| Upload | Werkzeug FileStorage |
| Deploy | Docker + Docker Compose |
| Server | Gunicorn |

---

## 🚀 Como executar

### Desenvolvimento

```bash
# Clonar
git clone https://github.com/gustavocaffaro/app-auditoria-uan.git
cd app-auditoria-uan

# Instalar dependências
pip install -r requirements.txt

# Executar
python run.py
```

Acesse **http://localhost:5000**

### Docker

```bash
docker compose up -d
```

Acesse **http://localhost:8090**

---

## 🔑 Credenciais padrão

| Tipo | Email | Senha |
|------|-------|-------|
| Admin | admin@uan.com | admin123 |
| Estagiário | estagiario@uan.com | estag123 |

O banco SQLite com seed é criado automaticamente na primeira execução.

---

## 📁 Estrutura do Projeto

```
uan-auditoria/
├── run.py                  # Entrypoint de desenvolvimento
├── requirements.txt        # Dependências Python
├── Dockerfile              # Build da imagem Docker
├── docker-compose.yml      # Orquestração Docker
├── data/                   # Banco SQLite (criado automaticamente)
├── app/
│   ├── __init__.py         # Factory + seed database
│   ├── config.py           # Configurações
│   ├── extensions.py       # Flask extensions (db, jwt, migrate)
│   ├── models/             # Modelos SQLAlchemy
│   │   ├── user.py         # User
│   │   ├── module.py       # Module (6 módulos)
│   │   ├── question.py     # Question (65 perguntas)
│   │   ├── session.py      # AuditSession
│   │   └── response.py     # Response
│   ├── routes/             # Rotas Flask
│   │   ├── auth.py         # Login/logout
│   │   ├── audit.py        # Questionário, auto-save, finalizar
│   │   ├── admin.py        # Dashboard, CRUD, listagens
│   │   └── export.py       # PDF e CSV
│   ├── templates/          # Jinja2 templates
│   │   ├── base.html       # Layout base
│   │   ├── login.html      # Tela de login
│   │   ├── audit/          # Questionário, resultado, histórico
│   │   ├── admin/          # Dashboard, usuários, detalhes
│   │   └── pdf/            # Template do relatório PDF
│   └── static/
│       ├── css/app.css     # Estilos customizados
│       └── js/             # JavaScript
│           ├── app.js      # Core: auto-save, navegação, logout
│           ├── condicionais.js  # Lógica condicional
│           ├── fotos.js    # Captura e upload de fotos
│           └── score.js    # Cálculo de pontuação em tempo real
```

---

## 🧠 Sistema de Red Flags

| Código | Falha | Módulo |
|--------|-------|--------|
| RF1 | Porta de banheiro abre diretamente para área de preparo | M1 |
| RF2 | Água da torneira sem tratamento para consumo dos residentes | M3 |
| RF3 | Presença de pragas na área de manipulação | M3 |
| RF4 | Animais com acesso à cozinha da instituição | M3 |
| RF5 | Lixo cruza fluxo de preparo dos alimentos | M3 |
| RF6 | Manipuladores usando adornos durante preparo | M4 |
| RF7 | Higienização inadequada de hortifrúti | M5 |

Cada Red Flag ativa exibe barra vermelha no topo da tela e o questionário **não pode ser finalizado** sem que o auditor registre uma observação.

---

## 📡 API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/auth/login` | Página de login |
| POST | `/auth/login` | Autenticação |
| POST | `/auth/logout` | Logout |
| GET | `/audit/nova` | Formulário nova auditoria |
| POST | `/audit/nova` | Criar auditoria |
| GET | `/audit/<id>/questionario` | Questionário |
| POST | `/audit/<id>/save` | Salvar respostas (AJAX) |
| POST | `/audit/<id>/upload-foto` | Upload de foto |
| POST | `/audit/<id>/finalizar` | Finalizar e calcular |
| GET | `/audit/<id>/resultado` | Página de resultado |
| GET | `/audit/historico` | Histórico do usuário |
| GET | `/admin/dashboard` | Dashboard admin |
| GET | `/admin/usuarios` | CRUD usuários |
| GET | `/admin/auditorias` | Listagem admin |
| GET | `/export/<id>/csv` | Download CSV |
| GET | `/export/<id>/pdf` | Download PDF |

---

## 📝 Licença

Este projeto é de uso interno e educacional.

import os
from datetime import datetime, date
from flask import Flask, request, redirect, url_for
from flask_jwt_extended import decode_token, verify_jwt_in_request
from app.config import Config
from app.extensions import db, jwt, migrate
from app.models import User, Module, Question, AuditSession, Response


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from app.routes.auth import auth_bp
    from app.routes.audit import audit_bp
    from app.routes.admin import admin_bp
    from app.routes.export import export_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(export_bp, url_prefix='/export')

    @app.context_processor
    def inject_globals():
        current_user = None
        try:
            verify_jwt_in_request(optional=True)
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                current_user = User.query.get(int(user_id))
        except Exception:
            pass
        from app.version import VERSION, VERSION_NAME
        return dict(current_user=current_user, now=datetime.now, app_version=VERSION, app_version_name=VERSION_NAME)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return redirect(url_for('auth.login'))

    with app.app_context():
        db.create_all()
        if not User.query.first():
            seed_database()

    return app


def seed_database():
    admin = User(
        nome='Administrador',
        email='admin@uan.com',
        tipo='admin',
        ativo=True
    )
    admin.set_senha('admin123')
    db.session.add(admin)

    estag = User(
        nome='Estagiario Padrao',
        email='estagiario@uan.com',
        tipo='estagiario',
        ativo=True
    )
    estag.set_senha('estag123')
    db.session.add(estag)
    db.session.flush()

    modulos = [
        {'nome': 'Estrutura Física e Edificações', 'ordem': 1, 'descricao': 'Avaliação da infraestrutura física da UAN, incluindo pisos, paredes, tetos, portas, janelas, iluminação e instalações sanitárias.'},
        {'nome': 'Equipamentos, Móveis e Utensílios', 'ordem': 2, 'descricao': 'Avaliação do estado de conservação e adequação dos equipamentos, móveis e utensílios utilizados na produção de alimentos.'},
        {'nome': 'Controle de Água, Pragas e Resíduos', 'ordem': 3, 'descricao': 'Avaliação do abastecimento de água, controle de vetores e pragas, e gestão de resíduos sólidos e efluentes.'},
        {'nome': 'Higiene e Saúde da Equipe', 'ordem': 4, 'descricao': 'Avaliação das condições de saúde, higiene pessoal, uniformes e capacitação dos manipuladores de alimentos.'},
        {'nome': 'Processo e Produção de Alimentos', 'ordem': 5, 'descricao': 'Avaliação do recebimento, armazenamento, preparo, higienização e distribuição dos alimentos.'},
        {'nome': 'Gestão, Documentação e Controle de Qualidade', 'ordem': 6, 'descricao': 'Avaliação da documentação obrigatória, POPs, manuais e registros de controle.'},
    ]

    modules = {}
    for m in modulos:
        mod = Module(**m)
        db.session.add(mod)
        db.session.flush()
        modules[m['ordem']] = mod

    perguntas = [
        # === MÓDULO 1 ===
        {'module_ordem': 1, 'codigo': 'M1Q1', 'pergunta': 'A área externa possui focos de insalubridade (lixo acumulado, água parada, mato alto)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 1, 'condicao': '{"extra":{"trigger":"Sim","fields":[{"type":"foto","required":false},{"type":"observacao","required":false}]}}'},
        {'module_ordem': 1, 'codigo': 'M1Q2', 'pergunta': 'O acesso à cozinha é independente e livre do trânsito de pessoas não autorizadas?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 3, 'ordem': 2},
        {'module_ordem': 1, 'codigo': 'M1Q3', 'pergunta': 'Qual é o material do piso da área de preparo?', 'tipo': 'select', 'opcoes': '["Cerâmica","Porcelanato","Epóxi","Cimento queimado","Outro"]', 'peso': 2, 'ordem': 3, 'condicao': '{"extra":{"trigger":"Outro","fields":[{"type":"foto","required":false},{"type":"observacao","required":false}]}}'},
        {'module_ordem': 1, 'codigo': 'M1Q4', 'pergunta': 'Qual é o estado de conservação do piso?', 'tipo': 'select', 'opcoes': '["Íntegro","Rachaduras leves","Quebrado ou com infiltração"]', 'peso': 4, 'ordem': 4},
        {'module_ordem': 1, 'codigo': 'M1Q5', 'pergunta': 'Os ralos possuem sistema de fechamento (tampa abre/fecha) para evitar pragas?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 5},
        {'module_ordem': 1, 'codigo': 'M1Q6', 'pergunta': 'A área de manipulação possui pia exclusiva para lavagem das mãos, desobstruída e dotada de sabonete líquido neutro e papel-toalha?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Sim, mas obstruída ou sem sabonete/papel"]', 'peso': 5, 'ordem': 6, 'condicao': '{"extra":{"trigger":"Sim, mas obstruída ou sem sabonete/papel","fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 1, 'codigo': 'M1Q7', 'pergunta': 'As paredes possuem revestimento liso, lavável e de cor clara?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 3, 'ordem': 7},
        {'module_ordem': 1, 'codigo': 'M1Q8', 'pergunta': 'Qual é o estado do teto/forro?', 'tipo': 'select', 'opcoes': '["Sem danos","Com umidade ou mofo","Com goteiras","Descascando","Outro"]', 'peso': 4, 'ordem': 8, 'condicao': '{"extra":{"trigger":["Com umidade ou mofo","Com goteiras","Descascando","Outro"],"fields":[{"type":"foto","required":true}]}}'},
        {'module_ordem': 1, 'codigo': 'M1Q9', 'pergunta': 'As janelas e aberturas possuem telas milimétricas para evitar insetos?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Parcialmente"]', 'peso': 4, 'ordem': 9},
        {'module_ordem': 1, 'codigo': 'M1Q10', 'pergunta': 'As portas possuem fechamento automático (mola)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 3, 'ordem': 10},
        {'module_ordem': 1, 'codigo': 'M1Q11', 'pergunta': 'As lâmpadas sobre a área de preparo possuem proteção contra quedas/explosão (calhas ou globos)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 11},
        {'module_ordem': 1, 'codigo': 'M1Q12', 'pergunta': 'A ventilação garante renovação do ar e evita acúmulo de fumaça/calor?', 'tipo': 'select', 'opcoes': '["Adequada – natural","Adequada – exaustores","Inadequada"]', 'peso': 4, 'ordem': 12},
        {'module_ordem': 1, 'codigo': 'M1Q13', 'pergunta': 'As portas dos banheiros abrem diretamente para a área de preparo de alimentos? (Atenção: a Anvisa proíbe isso.)', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 13, 'condicao': '{"red_flag":{"code":"RF1","label":"Porta de banheiro abre diretamente para área de preparo","trigger":"Sim","require_observacao":true}}'},
        {'module_ordem': 1, 'codigo': 'M1Q14', 'pergunta': 'Existe pia exclusiva para lavagem das mãos na área de produção?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 14},
        {'module_ordem': 1, 'codigo': 'M1Q15', 'pergunta': 'A pia para higienização das mãos possui sabonete líquido inodoro, papel-toalha não reciclado e lixeira com pedal?', 'tipo': 'select', 'opcoes': '["Completo","Faltam itens","Inexistente"]', 'peso': 5, 'ordem': 15},

        # === MÓDULO 2 ===
        {'module_ordem': 2, 'codigo': 'M2Q1', 'pergunta': 'As bancadas de preparo são de material liso, lavável, impermeável e resistente (ex.: aço inox, granito)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 1},
        {'module_ordem': 2, 'codigo': 'M2Q2', 'pergunta': 'Qual é o estado de conservação das bancadas?', 'tipo': 'select', 'opcoes': '["Íntegro","Com ranhuras profundas","Rachado ou quebrado"]', 'peso': 4, 'ordem': 2, 'condicao': '{"extra":{"trigger":["Com ranhuras profundas","Rachado ou quebrado"],"fields":[{"type":"foto","required":false},{"type":"observacao","required":false}]}}'},
        {'module_ordem': 2, 'codigo': 'M2Q3', 'pergunta': 'A cozinha possui armários com portas ou despensa exclusiva para alimentos, em número compatível com a demanda e construídos em material liso e impermeável?', 'tipo': 'select', 'opcoes': '["Sim","Não","Outro"]', 'peso': 4, 'ordem': 3, 'condicao': '{"extra":{"trigger":"Outro","fields":[{"type":"foto","required":true},{"type":"observacao","required":true}]}}'},
        {'module_ordem': 2, 'codigo': 'M2Q4', 'pergunta': 'Qual é o estado de conservação dos equipamentos de refrigeração (sem ferrugem, prateleiras limpas e borrachas de vedação íntegras)?', 'tipo': 'select', 'opcoes': '["Bom estado","Com ferrugem","Borrachas danificadas","Outros danos"]', 'peso': 5, 'ordem': 4, 'condicao': '{"extra":{"trigger":["Com ferrugem","Borrachas danificadas","Outros danos"],"fields":[{"type":"foto","required":true}]}}'},
        {'module_ordem': 2, 'codigo': 'M2Q5', 'pergunta': 'Os equipamentos possuem termômetro para controle diário de temperatura?', 'tipo': 'radio', 'opcoes': '["Sim, em todos","Sim, em alguns","Não possuem"]', 'peso': 5, 'ordem': 5},
        {'module_ordem': 2, 'codigo': 'M2Q6', 'pergunta': 'O fogão e o forno estão em bom estado, limpos e sem crostas de gordura carbonizada?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 6},
        {'module_ordem': 2, 'codigo': 'M2Q7', 'pergunta': 'Existe coifa ou exaustor instalado acima da área de cocção?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 3, 'ordem': 7},
        {'module_ordem': 2, 'codigo': 'M2Q8', 'pergunta': 'Se "Sim" na pergunta anterior: qual é o estado de limpeza e conservação da coifa/exaustor?', 'tipo': 'select', 'opcoes': '["Limpo e funcionando","Com muito acúmulo de gordura","Quebrado","— Não se aplica"]', 'peso': 3, 'ordem': 8, 'condicao': '{"depends":{"question":"M2Q7","value":"Sim"},"extra":{"trigger":["Com muito acúmulo de gordura","Quebrado"],"fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 2, 'codigo': 'M2Q9', 'pergunta': 'Qual é o material predominante das tábuas de corte?', 'tipo': 'select', 'opcoes': '["Plástico","Polietileno","Vidro","Madeira","Outro"]', 'peso': 3, 'ordem': 9},
        {'module_ordem': 2, 'codigo': 'M2Q10', 'pergunta': 'Panelas, assadeiras e utensílios estão em bom estado (sem amassados profundos, sem ferrugem e sem cabos soltos)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 3, 'ordem': 10, 'condicao': '{"extra":{"trigger":"Não","fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 2, 'codigo': 'M2Q11', 'pergunta': 'A instituição possui registros (planilhas, laudos ou notas fiscais) de manutenção preventiva dos equipamentos?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Desconhece"]', 'peso': 4, 'ordem': 11},

        # === MÓDULO 3 ===
        {'module_ordem': 3, 'codigo': 'M3Q1', 'pergunta': 'Qual é a origem do abastecimento de água do imóvel?', 'tipo': 'select', 'opcoes': '["Rede pública","Poço artesiano","Outro"]', 'peso': 3, 'ordem': 1, 'condicao': '{"extra":{"trigger":"Outro","fields":[{"type":"observacao","required":true}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q2', 'pergunta': 'O reservatório de água (caixa-d\'água) está em bom estado de conservação (sem rachaduras, vazamentos ou infiltrações)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 2},
        {'module_ordem': 3, 'codigo': 'M3Q3', 'pergunta': 'O reservatório está devidamente tampado/vedado?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 3},
        {'module_ordem': 3, 'codigo': 'M3Q4', 'pergunta': 'Existe comprovante (laudo ou certificado) de higienização do reservatório de água realizada nos últimos 6 meses?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Documento vencido"]', 'peso': 4, 'ordem': 4, 'condicao': '{"extra":{"trigger":["Sim","Documento vencido"],"fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q5', 'pergunta': 'Como é garantida a segurança da água utilizada para consumo dos residentes?', 'tipo': 'select', 'opcoes': '["Água mineral","Filtro de água","Fervura da água","Água da torneira"]', 'peso': 5, 'ordem': 5, 'condicao': '{"red_flag":{"code":"RF2","label":"Água da torneira sem tratamento para consumo dos residentes","trigger":"Água da torneira","require_observacao":true}}'},
        {'module_ordem': 3, 'codigo': 'M3Q6', 'pergunta': 'Nos sistemas de filtração de água e bebedouros, as trocas de filtros são monitoradas e registradas conforme instruções do fabricante?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Sim, mas atualmente vencido"]', 'peso': 4, 'ordem': 6, 'condicao': '{"extra":{"trigger":["Sim","Sim, mas atualmente vencido"],"fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q7', 'pergunta': 'A instituição possui contrato vigente ou declaração de empresa que efetua o recolhimento do óleo saturado de frituras (ou declaração formal de que não realiza frituras no local)?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Não realiza frituras no local"]', 'peso': 3, 'ordem': 7, 'condicao': '{"extra":{"trigger":["Sim","Não realiza frituras no local"],"fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q8', 'pergunta': 'Há evidências ou sinais de presença de pragas (baratas, roedores, formigas, moscas) na área de manipulação ou armazenamento?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 8, 'condicao': '{"red_flag":{"code":"RF3","label":"Presença de pragas na área de manipulação","trigger":"Sim","require_observacao":true}}'},
        {'module_ordem': 3, 'codigo': 'M3Q9', 'pergunta': 'A instituição possui certificado de controle químico de pragas (dedetização/desratização) emitido por empresa especializada e regularizada?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Documento vencido"]', 'peso': 4, 'ordem': 9, 'condicao': '{"extra":{"trigger":"Sim","fields":[{"type":"date","required":false,"label":"Data de validade do certificado"}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q10', 'pergunta': 'Há animais de estimação na instituição?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 2, 'ordem': 10, 'condicao': '{"extra":{"trigger":"Sim","fields":[{"type":"subquestions","questions":["M3Q10a","M3Q10b"]}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q10a', 'pergunta': 'As vacinas e vermifugações são realizadas e devidamente comprovadas no cartão de vacinas?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 0, 'ordem': 11, 'condicao': '{"depends":{"question":"M3Q10","value":"Sim"}}'},
        {'module_ordem': 3, 'codigo': 'M3Q10b', 'pergunta': 'Eles têm acesso à cozinha da instituição?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 0, 'ordem': 12, 'condicao': '{"depends":{"question":"M3Q10","value":"Sim"},"red_flag":{"code":"RF4","label":"Animais com acesso à cozinha da instituição","trigger":"Sim","require_observacao":true}}'},
        {'module_ordem': 3, 'codigo': 'M3Q11', 'pergunta': 'As lixeiras da área de preparo possuem tampa com acionamento por pedal e sacos plásticos adequados?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 13},
        {'module_ordem': 3, 'codigo': 'M3Q12', 'pergunta': 'O lixo é retirado frequentemente e armazenado em local fechado, fora da área de preparo, até a coleta pública?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 14, 'condicao': '{"extra":{"trigger":"Não","fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 3, 'codigo': 'M3Q13', 'pergunta': 'O trajeto/horário de retirada do lixo cruza com o fluxo de preparo ou distribuição dos alimentos (risco de contaminação cruzada)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 15, 'condicao': '{"red_flag":{"code":"RF5","label":"Lixo cruza fluxo de preparo dos alimentos (contaminação cruzada)","trigger":"Sim","require_observacao":true}}'},

        # === MÓDULO 4 ===
        {'module_ordem': 4, 'codigo': 'M4Q1', 'pergunta': 'Os manipuladores de alimentos possuem exames médicos admissionais/periódicos válidos (Atestado de Saúde Ocupacional – ASO)?', 'tipo': 'select', 'opcoes': '["Sim, todos válidos","Alguns vencidos","Não possuem"]', 'peso': 5, 'ordem': 1, 'condicao': '{"extra":{"trigger":["Alguns vencidos","Não possuem"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 4, 'codigo': 'M4Q2', 'pergunta': 'Existe procedimento claro para afastar manipuladores que apresentem lesões ou sintomas de enfermidades (ex.: diarreia, gripe forte, feridas nas mãos)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 2},
        {'module_ordem': 4, 'codigo': 'M4Q3', 'pergunta': 'Os manipuladores utilizam adornos durante o preparo dos alimentos (anéis, alianças, brincos, relógios, pulseiras)? (Atenção: a Anvisa proíbe totalmente.)', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 3, 'condicao': '{"red_flag":{"code":"RF6","label":"Manipuladores usando adornos durante preparo","trigger":"Sim","require_observacao":true}}'},
        {'module_ordem': 4, 'codigo': 'M4Q4', 'pergunta': 'Os manipuladores estão com unhas curtas, limpas, sem esmalte ou base?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Parcialmente"]', 'peso': 4, 'ordem': 4, 'condicao': '{"extra":{"trigger":["Não","Parcialmente"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 4, 'codigo': 'M4Q5', 'pergunta': 'Os manipuladores utilizam uniformes adequados, de cor clara, conservados e limpos?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Incompleto"]', 'peso': 4, 'ordem': 5},
        {'module_ordem': 4, 'codigo': 'M4Q6', 'pergunta': 'Qual é o estado da proteção dos cabelos?', 'tipo': 'select', 'opcoes': '["Cabelos totalmente protegidos","Cabelos parcialmente expostos"]', 'peso': 3, 'ordem': 6},
        {'module_ordem': 4, 'codigo': 'M4Q7', 'pergunta': 'Qual é o estado do uso de calçados?', 'tipo': 'select', 'opcoes': '["Sapatos fechados","Calçados abertos"]', 'peso': 3, 'ordem': 7},
        {'module_ordem': 4, 'codigo': 'M4Q8', 'pergunta': 'Existe registro (certificados ou listas de presença) de participação periódica da equipe em capacitação sobre Boas Práticas de Manipulação de Alimentos?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 8},
        {'module_ordem': 4, 'codigo': 'M4Q9', 'pergunta': 'Se "Sim" na pergunta anterior: quando foi realizado o último treinamento?', 'tipo': 'date', 'opcoes': None, 'peso': 0, 'ordem': 9, 'condicao': '{"depends":{"question":"M4Q8","value":"Sim"}}'},

        # === MÓDULO 5 ===
        {'module_ordem': 5, 'codigo': 'M5Q1', 'pergunta': 'Como os alimentos secos estão organizados na despensa?', 'tipo': 'select', 'opcoes': '["Em prateleiras/estrados afastados do piso e das paredes","Apoiados diretamente no chão","Junto com produtos de limpeza"]', 'peso': 5, 'ordem': 1, 'condicao': '{"extra":{"trigger":["Apoiados diretamente no chão","Junto com produtos de limpeza"],"fields":[{"type":"foto","required":true}]}}'},
        {'module_ordem': 5, 'codigo': 'M5Q2', 'pergunta': 'A instituição adota o sistema PVPS (Primeiro que Vence, Primeiro que Sai) para organização dos produtos?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 4, 'ordem': 2},
        {'module_ordem': 5, 'codigo': 'M5Q3', 'pergunta': 'Qual é o método utilizado para higienização das embalagens comerciais antes de serem armazenadas na despensa ou na geladeira?', 'tipo': 'select', 'opcoes': '["Álcool 70%","Lavagem com água e sabão","Apenas pano úmido","Não são higienizadas"]', 'peso': 3, 'ordem': 3, 'condicao': '{"extra":{"trigger":["Apenas pano úmido","Não são higienizadas"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 5, 'codigo': 'M5Q4', 'pergunta': 'Como é realizada a desinfecção de hortifrutigranjeiros (frutas, legumes e verduras) que serão consumidos crus?', 'tipo': 'select', 'opcoes': '["Imersão em solução clorada + enxágue","Apenas lavagem em água corrente","Uso de vinagre apenas"]', 'peso': 5, 'ordem': 4, 'condicao': '{"red_flag":{"code":"RF7","label":"Higienização inadequada de hortifrúti","trigger":["Apenas lavagem em água corrente","Uso de vinagre apenas"],"require_observacao":true}}'},
        {'module_ordem': 5, 'codigo': 'M5Q5', 'pergunta': 'Existe Procedimento Operacional Padronizado (POP) específico detalhando o envase, a conservação e a administração higiênica de fórmulas para alimentação por sonda?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 5},
        {'module_ordem': 5, 'codigo': 'M5Q6', 'pergunta': 'Como é realizado o descongelamento de carnes e produtos congelados?', 'tipo': 'select', 'opcoes': '["Sob refrigeração na geladeira","Em forno micro-ondas","Em temperatura ambiente","Embaixo de água corrente"]', 'peso': 4, 'ordem': 6, 'condicao': '{"extra":{"trigger":["Em temperatura ambiente","Embaixo de água corrente"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 5, 'codigo': 'M5Q7', 'pergunta': 'Alimentos abertos ou preparados e guardados na geladeira recebem etiqueta de identificação?', 'tipo': 'select', 'opcoes': '["Sim, com nome e validade","Sim, mas incompletas","Não são etiquetados"]', 'peso': 4, 'ordem': 7, 'condicao': '{"extra":{"trigger":["Sim, mas incompletas","Não são etiquetados"],"fields":[{"type":"foto","required":false}]}}'},
        {'module_ordem': 5, 'codigo': 'M5Q8', 'pergunta': 'São guardadas amostras das refeições servidas aos residentes (para análise em caso de surto alimentar)?', 'tipo': 'radio', 'opcoes': '["Sim","Não"]', 'peso': 5, 'ordem': 8},

        # === MÓDULO 6 ===
        {'module_ordem': 6, 'codigo': 'M6Q1', 'pergunta': 'O Manual de Boas Práticas está impresso e acessível aos manipuladores e aos órgãos de fiscalização na cozinha?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Desatualizado"]', 'peso': 5, 'ordem': 1, 'condicao': '{"extra":{"trigger":["Não","Desatualizado"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 6, 'codigo': 'M6Q2', 'pergunta': 'Os Procedimentos Operacionais Padronizados (POPs) estão impressos e acessíveis aos manipuladores na cozinha?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Desatualizados"]', 'peso': 5, 'ordem': 2, 'condicao': '{"extra":{"trigger":["Não","Desatualizados"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 6, 'codigo': 'M6Q3', 'pergunta': 'O documento contém todos os POPs obrigatórios previstos nas resoluções normativas?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Desatualizado"]', 'peso': 5, 'ordem': 3, 'condicao': '{"extra":{"trigger":["Não","Desatualizado"],"fields":[{"type":"observacao","required":false}]}}'},
        {'module_ordem': 6, 'codigo': 'M6Q4', 'pergunta': 'O alvará do Corpo de Bombeiros está dentro da validade e exposto ao público?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Desatualizado"]', 'peso': 5, 'ordem': 4, 'condicao': '{"extra":{"trigger":"Desatualizado","fields":[{"type":"observacao","required":false,"label":"Data de vencimento"}]}}'},
        {'module_ordem': 6, 'codigo': 'M6Q5', 'pergunta': 'O alvará sanitário está dentro da validade e exposto ao público?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Desatualizado"]', 'peso': 5, 'ordem': 5, 'condicao': '{"extra":{"trigger":"Desatualizado","fields":[{"type":"observacao","required":false,"label":"Data de vencimento"}]}}'},
        {'module_ordem': 6, 'codigo': 'M6Q6', 'pergunta': 'O cardápio vigente (semanal/mensal) está afixado em local visível na cozinha e/ou área de distribuição, com identificação de semana/período e validade?', 'tipo': 'radio', 'opcoes': '["Sim","Não","Parcialmente"]', 'peso': 4, 'ordem': 6, 'condicao': '{"extra":{"trigger":["Não","Parcialmente"],"fields":[{"type":"foto","required":false},{"type":"observacao","required":false}]}}'},
        {'module_ordem': 6, 'codigo': 'M6Q7', 'pergunta': 'As planilhas de registro diário (controle de temperatura de geladeiras, resfriamento/aquecimento de alimentos e rotinas de limpeza) estão sendo preenchidas corretamente pelos funcionários?', 'tipo': 'select', 'opcoes': '["Sim, todas em dia","Algumas em atraso","Não são preenchidas"]', 'peso': 5, 'ordem': 7, 'condicao': '{"extra":{"trigger":["Algumas em atraso","Não são preenchidas"],"fields":[{"type":"foto","required":false},{"type":"observacao","required":false}]}}'},
    ]

    for p in perguntas:
        mod = modules[p['module_ordem']]
        cond = p.get('condicao')
        depends = False
        if cond:
            try:
                import json as _json
                c = _json.loads(cond)
                if 'depends' in c:
                    depends = True
            except Exception:
                pass

        q = Question(
            module_id=mod.id,
            codigo=p['codigo'],
            pergunta=p['pergunta'],
            tipo=p['tipo'],
            opcoes=p.get('opcoes'),
            peso=p['peso'],
            ordem=p['ordem'],
            obrigatoria=(p['peso'] > 0 and not depends),
            condicao=cond
        )
        db.session.add(q)

    db.session.commit()

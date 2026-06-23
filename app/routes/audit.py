import json
import os
from datetime import datetime, date
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, Module, Question, AuditSession, Response

audit_bp = Blueprint('audit', __name__)


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})


@audit_bp.route('/nova', methods=['GET', 'POST'])
@jwt_required()
def nova():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if request.method == 'GET':
        return render_template('audit/nova.html', user=user)

    session = AuditSession(
        user_id=user_id,
        uan_nome=user.instituicao or 'UAN sem nome',
        uan_endereco=user.endereco or '',
        data_auditoria=None,
        status='andamento'
    )
    db.session.add(session)
    db.session.commit()

    if request.is_json:
        return jsonify({'ok': True, 'redirect': url_for('audit.questionario', id=session.id),
                        'session_id': session.id})

    return redirect(url_for('audit.questionario', id=session.id))


@audit_bp.route('/<int:id>/questionario')
@jwt_required()
def questionario(id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    is_admin = user and user.tipo == 'admin'

    if is_admin:
        session = AuditSession.query.get_or_404(id)
    else:
        session = AuditSession.query.filter_by(id=id, user_id=user_id).first_or_404()

    reeditando = session.status == 'finalizado'

    modules = Module.query.order_by(Module.ordem).all()
    all_questions = Question.query.order_by(Question.module_id, Question.ordem).all()

    responses = {r.question_id: r for r in session.responses.all()}

    modules_data = []
    for mod in modules:
        qs = [q for q in all_questions if q.module_id == mod.id]
        questions_data = []
        for q in qs:
            resp = responses.get(q.id)
            extra = _get_extra_responses(session.id, q.codigo)
            questions_data.append({
                'question': q,
                'resposta': resp.resposta if resp else None,
                'observacao': resp.observacao if resp else None,
                'foto_path': resp.foto_path if resp else None,
                'extra': extra
            })
        modules_data.append({'module': mod, 'questions': questions_data})

    return render_template('audit/questionario.html',
                           session=session,
                           modules=modules_data,
                           all_questions_json=_questions_json(all_questions),
                           reeditando=reeditando)


def _get_extra_responses(session_id, codigo):
    extra = {}
    for suffix in ['foto', 'observacao']:
        key = f'{codigo}_{suffix}'
        q = Question.query.filter_by(codigo=key).first()
        if q:
            r = Response.query.filter_by(session_id=session_id, question_id=q.id).first()
            if r:
                extra[suffix] = r.resposta
    return extra


def _questions_json(questions):
    data = []
    for q in questions:
        d = q.to_dict()
        d['module_id'] = q.module_id
        data.append(d)
    return json.dumps(data, ensure_ascii=False)


@audit_bp.route('/<int:id>/save', methods=['POST'])
@jwt_required()
def save(id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    is_admin = user and user.tipo == 'admin'

    if is_admin:
        session = AuditSession.query.get_or_404(id)
    else:
        session = AuditSession.query.filter_by(id=id, user_id=user_id).first_or_404()

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    respostas = data.get('respostas', [])

    for item in respostas:
        q_id = item.get('question_id')
        resposta = item.get('resposta')
        observacao = item.get('observacao', '')
        foto_path = item.get('foto_path', '')

        if not q_id:
            continue

        existing = Response.query.filter_by(session_id=id, question_id=q_id).first()
        if existing:
            existing.resposta = resposta
            existing.observacao = observacao if observacao else existing.observacao
            if foto_path:
                existing.foto_path = foto_path
        else:
            resp = Response(
                session_id=id,
                question_id=q_id,
                resposta=resposta,
                observacao=observacao,
                foto_path=foto_path
            )
            db.session.add(resp)

    db.session.commit()
    return jsonify({'ok': True, 'saved_at': datetime.utcnow().isoformat()})


@audit_bp.route('/<int:id>/upload-foto', methods=['POST'])
@jwt_required()
def upload_foto(id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user and user.tipo == 'admin':
        session = AuditSession.query.get_or_404(id)
    else:
        session = AuditSession.query.filter_by(id=id, user_id=user_id).first_or_404()

    if 'foto' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['foto']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Arquivo inválido'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"foto_{id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.{ext}"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, secure_filename(filename))
    file.save(filepath)

    relative_path = f'uploads/{filename}'
    return jsonify({'ok': True, 'path': relative_path})


@audit_bp.route('/<int:id>/finalizar', methods=['POST'])
@jwt_required()
def finalizar(id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    is_admin = user and user.tipo == 'admin'

    if is_admin:
        session = AuditSession.query.get_or_404(id)
    else:
        session = AuditSession.query.filter_by(id=id, user_id=user_id).first_or_404()
    session_db = db.session

    all_questions = Question.query.order_by(Question.module_id, Question.ordem).all()
    responses = {r.question_id: r for r in session.responses.all()}

    respostas_positivas = {
        'Sim', 'Íntegro', 'Bom estado', 'Completo', 'Limpo e funcionando',
        'Sim, em todos', 'Sim, todos válidos', 'Cabelos totalmente protegidos',
        'Sapatos fechados', 'Adequada – natural', 'Adequada – exaustores',
        'Sim, com nome e validade', 'Sim, todas em dia',
        'Em prateleiras/estrados afastados do piso e das paredes',
        'Sob refrigeração na geladeira', 'Imersão em solução clorada + enxágue',
        'Álcool 70%', 'Lavagem com água e sabão', 'Rede pública', 'Poço artesiano',
        'Água mineral', 'Filtro de água', 'Fervura da água',
        'Sim, em todos', 'Sim, em alguns'
    }

    total_peso = 0
    soma_pontos = 0
    red_flags_ativas = []

    for q in all_questions:
        if q.peso == 0:
            continue

        cond = q.get_condicao()
        if cond and 'depends' in cond:
            parent = Question.query.filter_by(codigo=cond['depends']['question']).first()
            if parent:
                parent_resp = responses.get(parent.id)
                if not parent_resp or parent_resp.resposta != cond['depends']['value']:
                    continue

        resp = responses.get(q.id)
        if not resp or not resp.resposta:
            continue

        total_peso += q.peso

        if resp.resposta in respostas_positivas:
            soma_pontos += q.peso

        if resp.resposta == '— Não se aplica':
            total_peso -= q.peso

        if cond and 'red_flag' in cond:
            rf = cond['red_flag']
            trigger = rf['trigger']
            if (isinstance(trigger, list) and resp.resposta in trigger) or resp.resposta == trigger:
                red_flags_ativas.append(rf)

    pontuacao = (soma_pontos / total_peso * 100) if total_peso > 0 else 0
    session.pontuacao = round(pontuacao, 1)

    if red_flags_ativas:
        session.classificacao = 'Regular'
        if session.pontuacao > 70:
            session.pontuacao = 70.0
    else:
        session.classificacao = session.calcular_classificacao()

    if not session.data_auditoria:
        session.data_auditoria = date.today()
    session.status = 'finalizado'
    session_db.commit()

    return jsonify({
        'ok': True,
        'redirect': url_for('audit.resultado', id=id),
        'pontuacao': session.pontuacao,
        'classificacao': session.classificacao,
        'red_flags': red_flags_ativas
    })


@audit_bp.route('/<int:id>/resultado')
@jwt_required()
def resultado(id):
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    session = AuditSession.query.filter_by(id=id).first_or_404()
    if user.tipo != 'admin':
        session = AuditSession.query.filter_by(id=id, user_id=user_id).first_or_404()

    if session.status != 'finalizado':
        return redirect(url_for('audit.questionario', id=id))

    modules_data = []
    all_questions = Question.query.order_by(Question.module_id, Question.ordem).all()
    responses = {r.question_id: r for r in session.responses.all()}

    red_flags_ativas = []

    for mod in Module.query.order_by(Module.ordem).all():
        qs = [q for q in all_questions if q.module_id == mod.id]
        questions_data = []
        for q in qs:
            resp = responses.get(q.id)
            cond = q.get_condicao()
            is_red_flag = False
            if cond and 'red_flag' in cond:
                rf = cond['red_flag']
                trigger = rf['trigger']
                if resp and resp.resposta and \
                   ((isinstance(trigger, list) and resp.resposta in trigger) or resp.resposta == trigger):
                    is_red_flag = True
                    red_flags_ativas.append(rf)

            questions_data.append({
                'question': q,
                'response': resp,
                'is_red_flag': is_red_flag
            })
        modules_data.append({'module': mod, 'questions': questions_data})

    return render_template('audit/resultado.html',
                           session=session,
                           modules=modules_data,
                           red_flags=red_flags_ativas,
                           auditor=session.auditor)


@audit_bp.route('/historico')
@jwt_required()
def historico():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user and user.tipo == 'admin':
        sessions = AuditSession.query.order_by(AuditSession.created_at.desc()).all()
    else:
        sessions = AuditSession.query.filter_by(user_id=user_id)\
            .order_by(AuditSession.created_at.desc()).all()
    return render_template('audit/historico.html', sessions=sessions)

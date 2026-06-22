from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import User, Module, Question, AuditSession, Response

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        if claims.get('tipo') != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_auditorias = AuditSession.query.count()
    finalizadas = AuditSession.query.filter_by(status='finalizado').count()
    andamento = AuditSession.query.filter_by(status='andamento').count()

    sessions_finalizadas = AuditSession.query.filter_by(status='finalizado').all()
    if sessions_finalizadas:
        media_pontuacao = sum(s.pontuacao for s in sessions_finalizadas if s.pontuacao) / len(sessions_finalizadas)
    else:
        media_pontuacao = 0

    classificacoes = {'Excelente': 0, 'Bom': 0, 'Regular': 0, 'Critico': 0}
    for s in sessions_finalizadas:
        if s.classificacao in classificacoes:
            classificacoes[s.classificacao] += 1

    total_usuarios = User.query.count()
    estagiarios = User.query.filter_by(tipo='estagiario').count()

    ultimas_auditorias = AuditSession.query.order_by(
        AuditSession.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_auditorias=total_auditorias,
                           finalizadas=finalizadas,
                           andamento=andamento,
                           media_pontuacao=round(media_pontuacao, 1),
                           classificacoes=classificacoes,
                           total_usuarios=total_usuarios,
                           estagiarios=estagiarios,
                           ultimas_auditorias=ultimas_auditorias)


@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/usuarios.html', users=users)


@admin_bp.route('/usuarios/criar', methods=['POST'])
@admin_required
def criar_usuario():
    data = request.get_json() or request.form
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '').strip()
    tipo = data.get('tipo', 'estagiario')

    if not nome or not email or not senha:
        return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já cadastrado'}), 400

    user = User(nome=nome, email=email, tipo=tipo, ativo=True)
    user.set_senha(senha)
    db.session.add(user)
    db.session.commit()

    return jsonify({'ok': True, 'user': user.to_dict()})


@admin_bp.route('/usuarios/<int:id>/editar', methods=['POST'])
@admin_required
def editar_usuario(id):
    user = User.query.get_or_404(id)
    data = request.get_json() or request.form

    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '').strip()
    tipo = data.get('tipo')

    if nome:
        user.nome = nome
    if email and email != user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
        user.email = email
    if senha:
        user.set_senha(senha)
    if tipo:
        user.tipo = tipo

    db.session.commit()
    return jsonify({'ok': True, 'user': user.to_dict()})


@admin_bp.route('/usuarios/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_usuario(id):
    user = User.query.get_or_404(id)
    user.ativo = not user.ativo
    db.session.commit()
    return jsonify({'ok': True, 'ativo': user.ativo})


@admin_bp.route('/auditorias')
@admin_required
def auditorias():
    sessions = AuditSession.query.order_by(
        AuditSession.created_at.desc()).all()
    return render_template('admin/auditorias_lista.html', sessions=sessions)


@admin_bp.route('/auditorias/<int:id>')
@admin_required
def auditoria_detalhe(id):
    session = AuditSession.query.get_or_404(id)
    all_questions = Question.query.order_by(Question.module_id, Question.ordem).all()
    responses = {r.question_id: r for r in session.responses.all()}

    modules_data = []
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

    return render_template('admin/auditoria_detalhe.html',
                           session=session,
                           modules=modules_data,
                           red_flags=red_flags_ativas,
                           auditor=session.auditor)

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')

    user = User.query.filter_by(email=email, ativo=True).first()
    if not user or not user.check_senha(senha):
        if request.is_json:
            return jsonify({'error': 'Email ou senha inválidos'}), 401
        return render_template('login.html', erro='Email ou senha inválidos')

    token = create_access_token(identity=str(user.id), additional_claims={
        'tipo': user.tipo, 'nome': user.nome
    })

    if request.is_json:
        resp = jsonify({'ok': True, 'redirect': url_for('admin.dashboard' if user.tipo == 'admin' else 'audit.nova')})
        set_access_cookies(resp, token)
        return resp

    resp = redirect(url_for('admin.dashboard' if user.tipo == 'admin' else 'audit.nova'))
    set_access_cookies(resp, token)
    return resp


@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'ok': True, 'redirect': url_for('auth.login')})
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user.to_dict())

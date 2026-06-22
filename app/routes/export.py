import csv
import io
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, make_response, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import User, Module, Question, AuditSession, Response

export_bp = Blueprint('export', __name__)


def _get_session_data(session):
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

    return modules_data, red_flags_ativas


@export_bp.route('/<int:id>/csv')
@jwt_required()
def download_csv(id):
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    session = AuditSession.query.get_or_404(id)
    if user.tipo != 'admin' and session.user_id != user_id:
        return jsonify({'error': 'Acesso negado'}), 403

    modules_data, red_flags = _get_session_data(session)

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')

    writer.writerow(['UAN Auditoria - Relatório CSV'])
    writer.writerow(['UAN:', session.uan_nome])
    writer.writerow(['Endereço:', session.uan_endereco or ''])
    writer.writerow(['Data:', session.data_auditoria.isoformat() if session.data_auditoria else ''])
    writer.writerow(['Auditor:', session.auditor.nome])
    writer.writerow(['Pontuação:', f"{session.pontuacao:.1f}%" if session.pontuacao else 'N/A'])
    writer.writerow(['Classificação:', session.classificacao or 'N/A'])
    writer.writerow([])

    writer.writerow(['Módulo', 'Código', 'Pergunta', 'Resposta', 'Observação', 'Red Flag', 'Foto'])

    for md in modules_data:
        for qd in md['questions']:
            q = qd['question']
            resp = qd['response']
            writer.writerow([
                md['module'].nome,
                q.codigo,
                q.pergunta,
                resp.resposta if resp else '',
                resp.observacao if resp else '',
                'SIM' if qd['is_red_flag'] else '',
                resp.foto_path if resp and resp.foto_path else ''
            ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename=auditoria_{id}_{datetime.now().strftime("%Y%m%d")}.csv'
    return response


@export_bp.route('/<int:id>/pdf')
@jwt_required()
def download_pdf(id):
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    session = AuditSession.query.get_or_404(id)
    if user.tipo != 'admin' and session.user_id != user_id:
        return jsonify({'error': 'Acesso negado'}), 403

    modules_data, red_flags = _get_session_data(session)

    static_folder = os.path.join(current_app.root_path, 'static')
    html = render_template('pdf/relatorio.html',
                           session=session,
                           modules=modules_data,
                           red_flags=red_flags,
                           auditor=session.auditor,
                           static_folder=static_folder)

    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=auditoria_{id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response
    except Exception:
        rendered = render_template('pdf/relatorio_print.html',
                                   session=session,
                                   modules=modules_data,
                                   red_flags=red_flags,
                                   auditor=session.auditor,
                                   static_folder=static_folder)
        response = make_response(rendered)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Content-Disposition'] = f'inline; filename=auditoria_{id}_{datetime.now().strftime("%Y%m%d")}.html'
        return response

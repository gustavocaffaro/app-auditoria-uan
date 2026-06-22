import json
from app.extensions import db


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    codigo = db.Column(db.String(20), nullable=False)
    pergunta = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    opcoes = db.Column(db.Text)
    peso = db.Column(db.Integer, nullable=False, default=1)
    ordem = db.Column(db.Integer, nullable=False)
    condicao = db.Column(db.Text)

    responses = db.relationship('Response', backref='question', lazy='dynamic')

    def get_opcoes(self):
        if self.opcoes:
            return json.loads(self.opcoes)
        return None

    def get_condicao(self):
        if self.condicao:
            return json.loads(self.condicao)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'module_id': self.module_id,
            'codigo': self.codigo,
            'pergunta': self.pergunta,
            'tipo': self.tipo,
            'opcoes': self.get_opcoes(),
            'peso': self.peso,
            'ordem': self.ordem,
            'condicao': self.get_condicao()
        }

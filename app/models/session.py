from datetime import datetime
from app.extensions import db


class AuditSession(db.Model):
    __tablename__ = 'audit_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uan_nome = db.Column(db.String(300), nullable=False)
    uan_endereco = db.Column(db.String(500))
    data_auditoria = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='andamento')
    pontuacao = db.Column(db.Float)
    classificacao = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    responses = db.relationship('Response', backref='session', lazy='dynamic',
                                cascade='all, delete-orphan')

    def calcular_classificacao(self):
        if self.pontuacao is None:
            return None
        if self.pontuacao >= 90:
            return 'Excelente'
        if self.pontuacao >= 70:
            return 'Bom'
        if self.pontuacao >= 50:
            return 'Regular'
        return 'Critico'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'uan_nome': self.uan_nome,
            'uan_endereco': self.uan_endereco,
            'data_auditoria': self.data_auditoria.isoformat() if self.data_auditoria else None,
            'status': self.status,
            'pontuacao': self.pontuacao,
            'classificacao': self.classificacao,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

from app.extensions import db


class Response(db.Model):
    __tablename__ = 'responses'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('audit_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    resposta = db.Column(db.Text)
    observacao = db.Column(db.Text)
    foto_path = db.Column(db.String(500))

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'resposta': self.resposta,
            'observacao': self.observacao,
            'foto_path': self.foto_path
        }

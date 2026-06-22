from app.extensions import db


class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    ordem = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.Text)

    questions = db.relationship('Question', backref='module', lazy='dynamic',
                                order_by='Question.ordem')

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'ordem': self.ordem,
            'descricao': self.descricao,
            'total_questions': self.questions.count()
        }

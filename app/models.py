from app import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    phone = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<User: {self.phone}>'


class ChannelChain(db.Model):
    __tablename__ = 'channelchain'

    id = db.Column(db.Integer, primary_key=True)
    from_title = db.Column(db.String)
    from_id = db.Column(db.String)
    from_access_hash = db.Column(db.String)
    to_title = db.Column(db.String)
    to_id = db.Column(db.String)
    to_access_hash = db.Column(db.String)
    last_message = db.Column(db.BigInteger)

    def __repr__(self):
        return f'ChannelChain: {self.id}'

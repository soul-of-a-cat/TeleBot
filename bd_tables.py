from sqlalchemy import Integer, String, Column, ForeignKey, Float
from bd_session import SqlAlchemyBase


class Users(SqlAlchemyBase):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    money = Column(Float, nullable=False)
    images = Column(Integer, nullable=False)
    creatkey = Column(String, nullable=False, )

    def __repr__(self):
        return f'<User> {self.id} {self.name}'


class Pictures(SqlAlchemyBase):
    __tablename__ = 'pictures'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    picture = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    description = Column(String, nullable=False)

    def __repr__(self):
        return f'<Picture> {self.id} {self.user_id}'


class UseKeys(SqlAlchemyBase):
    __tablename__ = 'useKeys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    key = Column(String, nullable=False)

    def __repr__(self):
        return f'<Picture> {self.id} {self.user_id}'


class BuyPictures(SqlAlchemyBase):
    __tablename__ = 'buyPictures'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'))
    picture = Column(String, nullable=False)

    def __repr__(self):
        return f'<Picture> {self.id} {self.user_id}'

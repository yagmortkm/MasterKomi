import datetime
import sqlalchemy
from sqlalchemy import orm, UniqueConstraint

from .db_session import SqlAlchemyBase


class EventSignup(SqlAlchemyBase):
    __tablename__ = 'event_signups'
    __table_args__ = (
        UniqueConstraint('user_id', 'event_id', name='uq_event_signup_user_event'),
    )

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    event_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('events.id'), nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User', back_populates='event_signups')
    event = orm.relationship('Event', back_populates='signups')

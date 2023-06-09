from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class User:
    _id: str
    email: str
    password: str
    role: str
    movies: list[str] = field(default_factory=list)
    ratings: dict[str:int] = field(default_factory=dict)
    

'''class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer, index=True)
    address = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), index=True)'''
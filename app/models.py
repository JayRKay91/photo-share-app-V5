from app.extensions import db
from flask_login import UserMixin
from datetime import datetime
from app.extensions import login_manager

# ──────────────── SharedAccess ────────────────
class SharedAccess(db.Model):
    __tablename__ = 'shared_access'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_sharedaccess_owner_id'),
        nullable=False
    )
    shared_user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_sharedaccess_shared_user_id'),
        nullable=False
    )
    alias = db.Column(db.String(80), nullable=False)
    can_upload = db.Column(db.Boolean, default=True)
    can_comment = db.Column(db.Boolean, default=True)
    require_upload_approval = db.Column(db.Boolean, default=False)
    require_comment_approval = db.Column(db.Boolean, default=False)

    owner = db.relationship('User', foreign_keys=[owner_id], back_populates='shared_users')
    shared_user = db.relationship('User', foreign_keys=[shared_user_id], back_populates='granted_access')


# ──────────────── Album ────────────────
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_album_user_id'),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='albums')
    photos = db.relationship('Photo', back_populates='album', lazy=True, cascade='all, delete-orphan')


# ──────────────── User ────────────────
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    albums = db.relationship('Album', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    photos = db.relationship('Photo', back_populates='owner', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    shared_users = db.relationship('SharedAccess', foreign_keys='SharedAccess.owner_id', back_populates='owner', cascade='all, delete-orphan', passive_deletes=True)
    granted_access = db.relationship('SharedAccess', foreign_keys='SharedAccess.shared_user_id', back_populates='shared_user', cascade='all, delete-orphan', passive_deletes=True)


# ──────────────── Photo ────────────────
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_photo_user_id'),
        nullable=False
    )
    album_id = db.Column(
        db.Integer,
        db.ForeignKey('album.id', ondelete='SET NULL', name='fk_photo_album_id'),
        nullable=True
    )
    uploader_alias = db.Column(db.String(80), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', back_populates='photos')
    album = db.relationship('Album', back_populates='photos')
    comments = db.relationship('Comment', backref='photo', lazy=True, cascade='all, delete-orphan', passive_deletes=True)


# ──────────────── Comment ────────────────
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(
        db.Integer,
        db.ForeignKey('photo.id', ondelete='CASCADE', name='fk_comment_photo_id'),
        nullable=False
    )
    commenter_alias = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────── Login Manager ────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

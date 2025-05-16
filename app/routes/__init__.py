from .auth_routes import auth_bp
from .gallery_routes import gallery_bp
from .upload_routes import upload_bp
from .album_routes import album_bp
from .comment_routes import comment_bp
from .tag_routes import tag_bp
from .share_routes import share_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(album_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(tag_bp)
    app.register_blueprint(share_bp)

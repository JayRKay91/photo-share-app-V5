from app import create_app, db

app = create_app()

# Ensure the app context is active before accessing the database
with app.app_context():
    from app.models import User, SharedAccess, Photo, Comment
    db.create_all()
    print("✅ Database checked/created successfully.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

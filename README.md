📸 Photo Share App — Version 4.5 (In Progress)
A personal and private photo- and video-sharing app built with Flask.
Upload, manage, tag, and comment on photos with support for user accounts, albums, and more — all stored locally.

🚀 Current Features (v4.5)
✅ Core Functionality
User account creation, login, logout

Per-user photo and video storage

Description fields per image

Optional image resizing & thumbnail generation

Image and video preview with lightbox (keyboard + click navigation)

✅ Tag System
Add tags to images

Rename tags (with confirmation message)

Delete tags:

Instant AJAX-based deletion

No page reload

Form fallback included

✅ Comments
Add comments to each image

Display name of commenter

Comments persist across reloads

✅ Download & Delete
One-click image/video download

Delete images (with confirmation prompt)

✅ Gallery Search
Search by filename, tag, or description

✅ UI/UX
Sticky search bar

Responsive mobile layout

Polished lightbox arrow navigation (keyboard & button support)

Feedback messages for most user actions

🧱 Project Setup
✅ Requirements
Python 3.9+

Flask

Jinja2

SQLite (used by default)

venv for virtual environment

📦 Setup Instructions
bash
Copy
Edit
# Clone the repo
git clone https://github.com/your-username/photo-share-app.git
cd photo-share-app

# Set up a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
App runs at:
📍 http://127.0.0.1:5000

Optional: set debug=True in run.py for development

🔄 Remaining 4.5 Features (To Be Completed)

Feature	Status
🛠 Fix Tag Delete (Basic)	✅ Done
⚡ Upgrade Tag Delete to AJAX	✅ Done
➕ Album Creation (custom names)	⏳ In Progress
📂 Default Album Suggestions (e.g., Vacation, Family, Pets)	⏳ Planned
🖼 Show album name in gallery	⏳ Planned
🔮 Looking Ahead (v5+)
Shared access (allow “Mom” to upload to your gallery)

Upload and comment permission settings per user

Email verification & password reset

Admin panel for user and content moderation

Album filtering and gallery views

Upload approval toggle for shared users

Native mobile companion app
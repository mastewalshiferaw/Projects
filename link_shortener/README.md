# 🚀 High-Performance URL Shortener

A professional URL shortening service built with Django that focuses on database integrity, analytics, and defensive programming.

## 🛠 Tech Stack
- **Backend:** Python 3.x, Django 5.x
- **Frontend:** Bootstrap 5, Vanilla JavaScript
- **Database:** SQLite (Development)
- **Security:** Python-Dotenv for environment variables

## ✨ Key Features
- **Collision-Proof Logic:** Implemented a validation loop to ensure 100% uniqueness for generated short codes.
- **Real-Time Analytics:** Tracks click counts for every link generated.
- **Defensive Validation:** Prevents "self-shortening" (infinite loops) and sanitizes user input.
- **Session-Based History:** Allows anonymous users to view their last 5 created links without needing an account.
- **Clipboard Integration:** One-click "Copy to Clipboard" functionality for better UX.

## 🧠 The Engineering Challenge
The biggest challenge was handling **Database Collisions**. In a system like this, two different long URLs could theoretically generate the same short code. 

**My Solution:** I overrode the Django Model `save()` method to implement a recursive-style check. The system generates a code, queries the database to see if it exists, and if so, tries again until a unique code is found. This ensures the system remains reliable even as the database grows.

## ⚙️ Installation
1. Clone the repo: `git clone https://github.com/mastewalshiferaw/Projects`
2. Create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file based on `.env.example`.
5. Run migrations: `python manage.py migrate`
6. Start the server: `python manage.py runserver`
# GradeSense AI

A role-based student grade management web app built with Streamlit and MongoDB.

## Features

- Role-based login: Admin, Teacher and Student
- Grade calculator with PDF report, Excel export and print support
- Student records and results saved in MongoDB
- Admin dashboard: user statistics, create / edit / disable / delete users, password reset
- Teacher dashboard: generated results, class overview, PASS/FAIL analytics
- Student dashboard: personal results and marksheet download
- Light and dark theme
- Passwords stored as bcrypt hashes

## Tech Stack

Python, Streamlit, MongoDB (PyMongo), bcrypt, Plotly, ReportLab, OpenPyXL

## Setup

1. Clone the repository

```bash
git clone https://github.com/waqarhussainoffcial-sudo/GradeSense_AI.git
cd GradeSense_AI
```

2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your MongoDB connection string

```
MONGO_URI=your-mongodb-connection-string
```

5. Create the first accounts

```bash
python create_admin.py
python create_teacher.py
python create_student.py
```

6. Run the app

```bash
streamlit run app.py
```

## Project Structure

- `app.py` : startup, login, session and navigation
- `auth.py` : authentication and user management
- `database.py`, `config.py` : MongoDB connection and settings
- `student_operations.py` : saving and reading student results
- `dashboard/` : Admin, Teacher and Student dashboards
- `create_admin.py`, `create_teacher.py`, `create_student.py` : helper scripts to create accounts

## Notes

- The `.env` file is not part of the repository. Never commit your database credentials.
- A free MongoDB Atlas cluster pauses after a period of inactivity. Resume it from the Atlas dashboard if the app cannot reach the database.

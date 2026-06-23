import sqlite3

conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()


def register_user(username, password):
    try:
        c.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (username, password)
        )
        conn.commit()
        return True
    except:
        return False


def login_user(username, password):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    return c.fetchone()
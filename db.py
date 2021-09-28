import sqlite3
import hashlib

connect = sqlite3.connect('databases/users.db', check_same_thread=False)


def register_user(tg_id, key, geo):
    hash_id = hashlib.md5(str(tg_id).encode()).hexdigest()
    cursor = connect.cursor()
    userdata = (hash_id, key, geo)
    try:
        cursor.execute("INSERT INTO users VALUES (NULL, ?, ?, ?)", userdata)
    except sqlite3.IntegrityError:
        pass
    connect.commit()
    cursor.close()


def get_user_key(tg_id):
    key = None
    hash_id = hashlib.md5(str(tg_id).encode()).hexdigest()
    cursor = connect.cursor()
    try:
        cursor.execute("SELECT owa_key FROM users WHERE tgid = ?", [hash_id])
        records = cursor.fetchall()
        for row in records:
            key = row[0]
        cursor.close()
        return key

    except Exception as e:
        cursor.close()
        print(e)
        return key


def get_user_geo(tg_id):
    geo = None
    hash_id = hashlib.md5(str(tg_id).encode()).hexdigest()
    cursor = connect.cursor()
    try:
        cursor.execute("SELECT geo FROM users WHERE tgid = ?", [hash_id])
        records = cursor.fetchall()
        for row in records:
            geo = row[0]
        cursor.close()
        return geo

    except Exception as e:
        cursor.close()
        print(e)
        return geo

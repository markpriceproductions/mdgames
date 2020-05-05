from flask import Flask, request, render_template, redirect, flash, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt   
from datetime import datetime 
import re
app = Flask(__name__)
app.secret_key = "thebubble"
bcrypt = Bcrypt(app) 
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route("/")
def lr_landing():
    return render_template("home.html")

@app.route("/register", methods=["POST"])
def process():
    is_valid = True

    if len(request.form['first_name']) < 2:
        flash("First name must be at least 2 characters")
        is_valid = False
    if len(request.form['last_name']) < 2:
        flash("Last name must be at least 2 characters")
        is_valid = False
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Email address must be a valid format")
        is_valid = False
    else:
        db = connectToMySQL("users")
        data = {
            "em": request.form['email']
        }
        result = db.query_db("SELECT * FROM users WHERE email = %(em)s",data)
        
        if len(result) > 0:
            flash("This email address is already registered.")
            is_valid = False
    if len(request.form['password']) < 8:
        flash("Password must be at least 8 characters")
        is_valid = False
    elif request.form['password'] != request.form['confirm_password']:
        flash("Password confirmation must match Password")
        is_valid = False

    if is_valid:
        db = connectToMySQL("users")
        query = "INSERT INTO users (first_name,last_name, email, password, created_at, updated_at) VALUES (%(fn)s,%(ln)s,%(em)s,%(pw)s, NOW(), NOW());"
        hashed_pw = bcrypt.generate_password_hash(request.form['password'])
        data = {
            "fn": request.form['first_name'],
            "ln": request.form['last_name'],
            "em": request.form['email'],
            "pw": hashed_pw, 
        }
        result = db.query_db(query,data) 
        if result:
            session['user_id'] = result
        else:
            return redirect("/")

        return redirect("/success")
    else:
        return redirect("/")

@app.route('/login', methods=["POST"])
def login():
    is_valid = True
    db = connectToMySQL("users")
    data = {
        "em": request.form['email']
    }
    result = db.query_db("SELECT * FROM users WHERE email = %(em)s",data)
    
    if len(result) > 0:
        user = result[0]
        if bcrypt.check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id_users']
            return redirect("/success")
        else:
            flash("Please enter a valid password.")
            return redirect("/")
    else:
        flash("Email address has not been registered.")
        return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route('/games')
def games():
    return render_template ("games.html")

@app.route('/snake')
def snake():
    return render_template ("web.html")

@app.route('/tetris')
def tetris():
    return render_template ("index.html")

@app.route('/bird')
def bird():
    return render_template ("bird.html")

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect("/")
    
    db = connectToMySQL("users")
    query = "SELECT users.first_name FROM users WHERE id_users = %(uid)s"
    data = {'uid': session['user_id'] }
    result = db.query_db(query, data)

    db = connectToMySQL("users")
    query = "SELECT thoughts.id_thoughts, thoughts.author, thoughts.content, thoughts.created_at, users.first_name, users.last_name FROM thoughts JOIN users on thoughts.author = users.id_users"
    all_thoughts = db.query_db(query)

    db = connectToMySQL("users")
    query = "SELECT thoughts_id_thoughts FROM liked_thoughts WHERE users_id_users = %(uid)s"
    data = {
        'uid': session['user_id']
    }
    results = db.query_db(query, data)
    liked_thought_ids = [result['thoughts_id_thoughts']for result in results]

    db = connectToMySQL('users')
    query = "SELECT thoughts_id_thoughts, COUNT(thoughts_id_thoughts) AS count from liked_thoughts GROUP BY thoughts_id_thoughts"
    like_count = db.query_db(query)

    for thought in all_thoughts:
        for like in like_count:
            if thought['id_thoughts'] == like['thoughts_id_thoughts']:
                thought['like_count'] = like['count']
        if 'like_count' not in thought:   
            thought['like_count'] = 0

    if result:
        return render_template("landing.html", user_fn = result[0], all_thoughts = all_thoughts, liked_thought_ids = liked_thought_ids)
    else:
        return render_template("landing.html")

@app.route('/success')
def landing_page():
    if 'user_id' not in session:
        return redirect("/")
    
    db = connectToMySQL("users")
    query = "SELECT users.first_name FROM users WHERE id_users = %(uid)s"
    data = {'uid': session['user_id'] }
    result = db.query_db(query, data)

    db = connectToMySQL("users")
    query = "SELECT thoughts.id_thoughts, thoughts.author, thoughts.content, thoughts.created_at, users.first_name, users.last_name FROM thoughts JOIN users on thoughts.author = users.id_users"
    all_thoughts = db.query_db(query)

    db = connectToMySQL("users")
    query = "SELECT thoughts_id_thoughts FROM liked_thoughts WHERE users_id_users = %(uid)s"
    data = {
        'uid': session['user_id']
    }
    results = db.query_db(query, data)
    liked_thought_ids = [result['thoughts_id_thoughts']for result in results]

    db = connectToMySQL('users')
    query = "SELECT thoughts_id_thoughts, COUNT(thoughts_id_thoughts) AS count from liked_thoughts GROUP BY thoughts_id_thoughts"
    like_count = db.query_db(query)

    for thought in all_thoughts:
        for like in like_count:
            if thought['id_thoughts'] == like['thoughts_id_thoughts']:
                thought['like_count'] = like['count']
        if 'like_count' not in thought:   
            thought['like_count'] = 0

    if result:
        return render_template("landing.html", user_fn = result[0], all_thoughts = all_thoughts, liked_thought_ids = liked_thought_ids)
    else:
        return render_template("landing.html")

@app.route("/thought", methods=['POST'])
def on_tweet():
    is_valid = True
    if len(request.form['thought']) < 5:
        is_valid = False
        flash("Thoughts must be at least 5 characters")

    if is_valid:
        db = connectToMySQL("users")
        query = "INSERT into thoughts (content, author, created_at, updated_at) VALUE (%(tc)s, %(aid)s, NOW(), NOW())"
        data = {
            'tc': request.form.get('thought'),
            'aid': session['user_id']
        }
        db.query_db(query, data)

    return redirect("/success")

@app.route("/delete/<thought_id>")
def on_delete(thought_id):
    db = connectToMySQL("users")
    query = "DELETE FROM thoughts WHERE id_thoughts = %(tid)s"
    data = {
        'tid': thought_id
    }
    db.query_db(query, data)
    return redirect("/success")

@app.route("/thought_details/<thought_id>")
def thought_details(thought_id):
    db = connectToMySQL("users")
    query = "SELECT thoughts.id_thoughts, thoughts.content, users.first_name FROM thoughts JOIN users on thoughts.author = users.id_users WHERE thoughts.id_thoughts = %(tid)s"
    data = {
        'tid': thought_id
    }
    thought = db.query_db(query, data)

    db = connectToMySQL("users")
    query = "SELECT * FROM thoughts WHERE id_thoughts = %(tid)s"
    data = {
        'tid': thought_id
    }
    thought_data = db.query_db(query, data)
    if thought:
        thought = thought[0]

    db = connectToMySQL('users')
    query = "SELECT users.first_name, users.last_name FROM liked_thoughts JOIN users on liked_thoughts.users_id_users = users.id_users WHERE thoughts_id_thoughts = %(tid)s"
    data = {
        'tid': thought_id
    }
    users_who_liked_thought = db.query_db(query, data)

    return render_template("details.html", thought_data = thought_data[0], users_who_liked_thought = users_who_liked_thought, thought = thought)


@app.route("/liked_thought/<thought_id>")
def on_like(thought_id):
    db = connectToMySQL("users")
    query = "INSERT INTO liked_thoughts (users_id_users, thoughts_id_thoughts) VALUES (%(uid)s, %(tid)s)"
    data = {
        'uid': session['user_id'],
        'tid': thought_id
    }
    db.query_db(query, data)
    return redirect("/success")

@app.route("/unliked_thought/<thought_id>")
def on_unlike(thought_id):
    db = connectToMySQL("users")
    query = "DELETE FROM liked_thoughts WHERE users_id_users = %(uid)s AND thoughts_id_thoughts = %(tid)s"
    data = {
        'uid': session['user_id'],
        'tid': thought_id
    }
    db.query_db(query, data)
    return redirect("/success")

if __name__ == "__main__":
    app.run(debug=True)
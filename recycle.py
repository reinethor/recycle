######################################################################
#
#   APPLICATION INTIALIZATION
#
######################################################################
import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash


# create our application
app = Flask(__name__)

# configuration
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'users.db'),
    DEBUG=True,
    SECRET_KEY='developer key',
))

# define the user session
@app.before_request
def before_request():
    g.user = None
    if 'uid' in session:
        g.user = query_db('select * from user where uid = ?',
                          [session['uid']], one=True)

######################################################################
#
#   DATABASE
#
######################################################################
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

######################################################################
#
#   HELPERS
#
######################################################################

def get_uid(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select uid from user where username = ?',
                  [username], one=True)
    return rv[0] if rv else None

def get_username(uid):
    """Convenience method to look up the username for a uid."""
    rv = query_db('select username from user where uid = ?',
                  [uid], one=True)
    return rv[0] if rv else None

def get_day(uid):
    """Convenience method to look up day for a uid."""
    rv = query_db('select day from user where uid = ?',
                    [uid], one=True)
    return rv[0] if rv else None


######################################################################
#
#   APP RELATED
#
######################################################################

# def get_phase(username):
def increment_day(uid):
    """Increments the day value of a user in the database."""
    db = get_db()
    db.execute('''update user
                set day = day + 1
                where uid = ?;''', [session['uid']])
    db.commit()

def decrement_day(uid):
    """Decrements the day value of a user in the database."""
    db = get_db()
    db.execute('''update user
                set day = day - 1
                where uid = ?;''', [session['uid']])
    db.commit()

######################################################################
#
#   WEBPAGES
#
######################################################################
@app.route('/')
def user_home():
    return render_template('user_home.html', user = query_db('''select user.* from user where
        uid = ?''', [session['uid']]))

@app.route('/home')
def public_home():
    return render_template('public_home.html')

@app.route('/recycle')
def recycle():
    increment_day(session['uid'])
    return redirect(url_for('user_home'))

#   USER ACCOUNTS

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('user_home'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_uid(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            db = get_db()
            db.execute('''insert into user (
              username, email, pw_hash, day) values (?, ?, ?, 1)''',
              [request.form['username'], request.form['email'],
               generate_password_hash(request.form['password'])])
            db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('user_home'))
    error = None
    if request.method == 'POST':
        print("in the post method")
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            print('\nELSE\n')
            flash('You were logged in')
            session['uid'] = user['uid']
            return redirect(url_for('user_home'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('uid', None)
    return redirect(url_for('public_home'))

if __name__ == '__main__':
    app.run()

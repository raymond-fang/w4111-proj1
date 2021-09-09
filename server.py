
"""
Columbia's COMS W4111.001 Introduction to Databases
Authors: Andrew Tang, Raymond Fang
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config.from_mapping(SECRET_KEY='dev')

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
DATABASEURI = "postgresql://at3456:Tang0926@@34.73.36.248/project1" # Modify this with your own credentials you received from Joseph!

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

  account_id = session.get('account_id')

  if account_id is None:
      g.account = None
  else:
      g.account = g.conn.execute(text(
          'SELECT * FROM account WHERE account_id = :x'), x=account_id
      ).fetchone()
  
  admin_id = session.get('admin_id')

  if admin_id is None:
      g.admin = None
  else:
      g.admin = g.conn.execute(
        'SELECT * FROM administrator WHERE admin_id = %s', admin_id
      ).fetchone()

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
@app.route('/index')
def index():
  return render_template("index.html")

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        account = g.conn.execute(
          text(
            'SELECT * FROM account WHERE email = :x'
          ), x=email
        ).fetchone()

        if account is None:
            error = 'Incorrect email.'
        elif account['password'] != password:
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['account_id'] = account['account_id']
            return redirect('index')

        flash(error)

    return render_template('login.html')

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None

        if not email:
          error = 'Email is required.'
        elif not password:
          error = 'Password is required.'
        elif g.conn.execute(
          text(
            'SELECT email FROM account WHERE email = :x'
          ), x=email
        ).fetchone() is not None:
          error = 'Email {} is already registered.'.format(email)

        if error is None:
          max_id = g.conn.execute(
            'SELECT MAX(account_id) FROM account'
          ).fetchone()
          new_id = max_id['max'] + 1
          g.conn.execute(
            text(
              'INSERT INTO account VALUES (:x, :y, :z)'
            ), x=new_id, y=email, z=password
          )
          return redirect('login')

        flash(error)

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('index')
  
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
  if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        account = g.conn.execute(
          text(
            'SELECT * FROM administrator WHERE email = :x'
          ), x=email
        ).fetchone()

        if account is None:
            error = 'Incorrect email.'
        elif account['password'] != password:
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['admin_id'] = account['admin_id']
            return redirect('index')

        flash(error) 

  return render_template('admin_login.html')

@app.route('/edit_history')
def edit_history():
  deleted = g.conn.execute(
    'SELECT * FROM delete NATURAL JOIN administrator NATURAL JOIN review'
    ' ORDER BY CAST(review_id AS INTEGER) DESC'
  ).fetchall()
  modified = g.conn.execute(
    'SELECT * FROM modify NATURAL JOIN administrator NATURAL JOIN review'
    ' ORDER BY CAST(review_id AS INTEGER) DESC'
  ).fetchall()
  return render_template('edit_history.html', deleted=deleted, modified=modified)

@app.route('/anime') 
def generate_page():
  anime_id = request.args.get('anime_id')
  anime = g.conn.execute('SELECT * FROM anime WHERE anime_id = %s', anime_id).fetchone()

  reviews = g.conn.execute(
    'SELECT *'
    ' FROM anime NATURAL JOIN describes NATURAL JOIN review NATURAL JOIN writes'
    ' NATURAL JOIN account'
    ' WHERE anime_id = %s AND deleted = FALSE'
    ' ORDER BY CAST(review_id AS INTEGER) DESC', anime_id
  )

  comments = g.conn.execute(
    'SELECT *'
    ' FROM anime NATURAL JOIN belongs NATURAL JOIN comment NATURAL JOIN posts'
    ' NATURAL JOIN account'
    ' WHERE anime_id = %s'
    ' ORDER BY CAST(comment_id AS INTEGER) DESC', anime_id
  )

  write_url = "write?anime_id=" + str(anime_id)
  post_url = "post?anime_id=" + str(anime_id)
  return render_template('anime.html', anime=anime, reviews=reviews, 
    comments=comments, write_url=write_url, post_url=post_url)

@app.route('/rate', methods=['POST'])
def rate():
  rating = request.form['rating']
  anime_id = str(request.form['anime_id'])
  msg = 'Your rating of {} has been submitted!'.format(rating)

  # update ratings in rates
  if g.conn.execute(
      'SELECT account_id FROM rates WHERE anime_id = %s AND account_id = %s', anime_id, 
      g.account['account_id']
    ).fetchone() is not None:
    g.conn.execute(
      'UPDATE rates SET rating = %s WHERE anime_id = %s AND account_id = %s', rating,
      anime_id, g.account['account_id']
    )
  else:
    g.conn.execute(
      'INSERT INTO rates VALUES (%s, %s, %s)', g.account['account_id'], anime_id, rating
    )
  
  # calculate new avg
  avg = g.conn.execute(
    'SELECT AVG(rating) AS avg FROM rates WHERE anime_id = %s GROUP BY anime_id', anime_id
  ).fetchone()

  if not avg: # replace default value (no account rating records)
    avg = rating
  else: 
    avg = avg['avg']

  # update avg_rating in anime
  g.conn.execute(
    'UPDATE anime SET avg_rating = %s WHERE anime_id = %s', str(avg), anime_id
  )
  flash(msg)
  return redirect('anime?anime_id={}'.format(anime_id))

@app.route('/favorite', methods=['POST'])
def favorite():
  anime_id = str(request.form['anime_id'])
  name = str(request.form['name'])

  msg = 'Added to your favorites list!'

  # update ratings in rates
  if g.conn.execute(
      'SELECT account_id FROM favourite_anime WHERE anime_id = %s AND account_id = %s', anime_id, 
      g.account['account_id']
    ).fetchone() is None:
    g.conn.execute(
      'INSERT INTO favourite_anime VALUES (%s, %s)', g.account['account_id'], anime_id
    )

  flash(msg)
  return redirect('anime?anime_id={}'.format(anime_id))

@app.route('/write', methods=('GET', 'POST'))
def write():
    if request.method == 'POST':
        anime_id = request.form['anime_id']
        text = request.form['text'].strip()
        error = None

        if not text:
            error = 'Text is required.'

        if error is not None:
            flash(error)
        else:
            review_id = g.conn.execute(
              'SELECT MAX(CAST(review_id AS INTEGER)) FROM review'
            ).fetchone()
            new_id = str(review_id['max'] + 1)

            g.conn.execute(
              'INSERT INTO review VALUES(%s, %s, FALSE)', new_id, text
            )
            g.conn.execute(
              'INSERT INTO describes VALUES (%s, %s)', new_id, anime_id
            )
            g.conn.execute(
              'INSERT INTO writes VALUES (%s, %s)', g.account['account_id'], new_id
            )
            return redirect('anime?anime_id=' + str(anime_id))

    anime_id = request.args.get('anime_id')
    return render_template('write.html', anime_id=anime_id)

@app.route('/post', methods=('GET', 'POST'))
def post():
    if request.method == 'POST':
        anime_id = request.form['anime_id']
        text = request.form['text'].strip()
        episode = request.form['episode']
        error = None

        total_ep = g.conn.execute(
          'SELECT num_episodes FROM anime WHERE anime_id=%s', anime_id
        ).fetchone()['num_episodes']
        if total_ep == 'Unknown':
            error = 'Sorry, comments cannot be added to this anime.'
            flash(error)
            return render_template('post.html', anime_id=anime_id)

        if not episode:
            error = 'Episode number is required.'
        elif int(episode) > int(total_ep) or int(episode) <= 0:
            error = 'Episode does not exist.'

        if not text:
            error = 'Text is required.'

        if error is not None:
            flash(error)
        else:
            comment_id = g.conn.execute(
              'SELECT MAX(CAST(comment_id AS INTEGER)) FROM comment'
            ).fetchone()
            new_id = str(comment_id['max'] + 1)

            g.conn.execute(
              'INSERT INTO comment VALUES(%s, %s)', new_id, text
            )
            g.conn.execute(
              'INSERT INTO belongs VALUES (%s, %s, %s)', new_id, anime_id, int(episode)
            )
            g.conn.execute(
              'INSERT INTO posts VALUES (%s, %s)', g.account['account_id'], new_id
            )
            return redirect('anime?anime_id=' + str(anime_id))

    anime_id = request.args.get('anime_id')
    return render_template('post.html', anime_id=anime_id)

@app.route('/delete')
def del_review():
  review_id = request.args.get('review_id')
  comment_id = request.args.get('comment_id')
  anime_id = request.args.get('anime_id')
  msg = 'Review deleted!'
  if g.admin:
      admin_id = session.get('admin_id')
      if review_id:
          g.conn.execute('INSERT INTO delete VALUES(%s, %s)', review_id, admin_id)
          g.conn.execute('UPDATE review SET deleted = TRUE WHERE review_id = %s', review_id)
      else:
          g.conn.execute('DELETE FROM comment WHERE comment_id = %s', comment_id)
          msg = 'Comment deleted!'
  else:
      if review_id:
          g.conn.execute('UPDATE review SET deleted = TRUE WHERE review_id = %s', review_id)
      else:
          g.conn.execute('DELETE FROM comment WHERE comment_id = %s', comment_id)
          msg = 'Comment deleted!'
  flash(msg)
  return redirect('anime?anime_id={}'.format(anime_id))

@app.route('/modifyReview', methods=['GET', 'POST'])
def modifyReview():
  if request.method == 'POST':
    anime_id = request.form['anime_id']
    review_id = request.form['review_id']
    text = request.form['text'].strip()
    error = None

    if not text:
      error = "Text is required."

    if error is not None:
      flash(error)
    else:
      g.conn.execute(
        'UPDATE review SET text = %s WHERE review_id = %s', text, review_id
      )
      
      if g.admin:
        alreadyModified = g.conn.execute('SELECT * FROM modify WHERE admin_id = %s AND review_id = %s', g.admin['admin_id'], review_id).fetchone()
      
      if g.admin and not alreadyModified:
        g.conn.execute(
          'INSERT INTO modify VALUES(%s, %s)', review_id, g.admin['admin_id']
        )

      flash('Review successfully updated.')
      return redirect('anime?anime_id={}'.format(anime_id))

  review_id = request.args['review_id']
  anime_id = request.args['anime_id']
  text = g.conn.execute(
    'SELECT text FROM review WHERE review_id = %s', review_id
  ).fetchone()['text']
  return render_template('modifyReview.html', text=text, review_id=review_id, anime_id=anime_id)

@app.route('/modifyComment', methods=['GET', 'POST'])
def modifyComment():
  if request.method == 'POST':
    anime_id = request.form['anime_id']
    comment_id = request.form['comment_id']
    text = request.form['text'].strip()
    error = None

    if not text:
      error = "Text is required."

    if error is not None:
      flash(error)
    else:
      g.conn.execute(
        'UPDATE comment SET text = %s WHERE comment_id = %s', text, comment_id
      )
      flash('Comment successfully updated.')
      return redirect('anime?anime_id={}'.format(anime_id))

  comment_id = request.args['comment_id']
  anime_id = request.args['anime_id']
  text = g.conn.execute(
    'SELECT text FROM comment WHERE comment_id = %s', comment_id
  ).fetchone()['text']
  return render_template('modifyComment.html', text=text, comment_id=comment_id, anime_id=anime_id)  

@app.route('/search', methods=['POST'])
def recommend_animes():
  genres = request.form['genres'].strip()
  exclude = request.form['exclude'].strip()
  minRating = request.form['min_rating']
  listGenres = genres.split(", ")
  excludeGenres = exclude.split(", ")
  error = None

  minNum = 0.0
  if not minRating:
    minNum = float(0)
  else:
    minNum = float(minRating)

  if not genres:
    error = 'Please enter a genre(s).'  

  if error is not None:
    flash(error)
  else:
    g.conn.execute('CREATE TEMPORARY TABLE DesiredGenres (genre varchar(20) not null, primary key(genre))')
    g.conn.execute('CREATE TEMPORARY TABLE BadGenres (genre varchar(20) not null, primary key(genre))')

    s = 'INSERT INTO DesiredGenres VALUES '
    for genre in listGenres:
      s += '(\'{}\'), '.format(genre.strip())
    s = s[:-2] + ';'
    g.conn.execute(s)

    s = 'INSERT INTO BadGenres VALUES '
    for genre in excludeGenres:
      s += '(\'{}\'), '.format(genre.strip())
    s = s[:-2] + ';'
    g.conn.execute(s)
    
    # cleanup duplicates 
    g.conn.execute(
      'DELETE FROM DesiredGenres WHERE UPPER(genre) IN (SELECT UPPER(genre) FROM BadGenres)'
    )

    animes = g.conn.execute( # orders anime by number of relevant genres
          'SELECT DISTINCT(anime_id), anime_name, num_episodes, avg_rating,'
          '   SUM(CASE WHEN UPPER(genre) IN (SELECT UPPER(genre) FROM DesiredGenres) THEN 1'
          '            ELSE 0 END) AS n'
          ' FROM anime NATURAL JOIN anime_genre'
          ' WHERE anime_id IN (SELECT anime_id FROM anime_genre a JOIN DesiredGenres d'
          '                       ON UPPER(a.genre) = UPPER(d.genre))'
          '   AND anime_id NOT IN (SELECT anime_id FROM anime_genre a JOIN BadGenres b'
          '                       ON UPPER(a.genre) = UPPER(b.genre))'
          '   AND avg_rating >= %s'
          ' GROUP BY anime_id, anime_name, num_episodes, avg_rating'
          ' ORDER BY n DESC', minNum
    ).fetchall()

    if not animes:
      flash('No animes found. Pro tip: seperate your genres by \", \"')
      g.conn.execute('DROP TABLE DesiredGenres')
      g.conn.execute('DROP TABLE BadGenres')
      return redirect('index')

    genres = g.conn.execute(
      'SELECT anime_id, genre FROM anime NATURAL JOIN anime_genre' 
      ' WHERE avg_rating >= %s', minNum
    ).fetchall()

    # sort by rating for equal num of relevant genres
    cur_max_N = animes[0]['n']
    for i in range(0, len(animes)):
      if animes[i]['n'] != cur_max_N:
        cur_max_N = animes[i]['n']
      j = i+1
      while j < len(animes) and animes[j]['n'] == cur_max_N:
        if animes[j]['avg_rating'] > animes[i]['avg_rating']:
          tmp = animes[i]
          animes[i] = animes[j]
          animes[j] = tmp
        j += 1

    x = []  
    i = 0
    for row in animes:
      s = ''
      for genre in genres:
        if row['anime_id'] == genre['anime_id']:
          s += genre[1] + ', '
      li = list(row)
      li.append(s[:-2])
      t = tuple(li)
      x.append(t)
      i += 1
      if i == 100:
        break

    g.conn.execute('DROP TABLE DesiredGenres')
    g.conn.execute('DROP TABLE BadGenres')

    return render_template('recommendations.html', animes=x)
  
  return redirect('index')

@app.route('/lookup', methods=['POST'])
def lookup():
  anime_in = request.form['anime_name'].strip()
  error = None

  if not anime_in:
    error = 'Please enter an anime.'
  
  if error is not None:
    flash(error, 'anime_in')
  else:
    animes = g.conn.execute(
      'SELECT * FROM anime WHERE UPPER(anime_name) LIKE UPPER(%s)'
      ' ORDER BY CAST(anime_id AS INTEGER)', anime_in+'%'
    ).fetchall()
    
    genres = g.conn.execute(
      'SELECT anime_id, genre FROM anime NATURAL JOIN anime_genre'
      ' WHERE UPPER(anime_name) LIKE UPPER(%s)'
      ' ORDER BY CAST(anime_id AS INTEGER)', anime_in+'%'
    ).fetchall()
    
    x = []  
    i = 0
    for row in animes:
      s = ''
      while i < len(genres) and genres[i]['anime_id'] == row['anime_id']:
        s += genres[i]['genre'] + ', '
        i += 1
      li = list(row)
      li.append(s[:-2])
      t = tuple(li)
      x.append(t)

    if not animes:
      error = '\"{}\" is not an Anime!'.format(anime_in)
      flash(error, 'anime_in')
      return redirect('index')
    else:
      return render_template('/anime_list.html', animes=x, anime_in=anime_in)
  
  return redirect('index')

@app.route('/view_favorites') 
def view_favourites():
    account_id = session.get('account_id')
    favoriteAnimes = g.conn.execute(
            'SELECT anime_id, anime_name FROM anime NATURAL JOIN favourite_anime WHERE account_id = %s', account_id
    ).fetchall()

    return render_template('/favorite_list.html', favoriteAnimes=favoriteAnimes)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
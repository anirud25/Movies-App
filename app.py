from flask import Flask, request, render_template,session, redirect, url_for,jsonify
from forms import MovieForm
import uuid
import pandas as pd
import numpy as np
import functools
from flask import flash
from forms import RegisterForm, LoginForm 
from models import User
from passlib.hash import pbkdf2_sha256
from dataclasses import asdict
from ast import literal_eval
from datetime import datetime
from utils.funcs import *
from flask_sqlalchemy import SQLAlchemy
from src.model_training import ModelTrainer
from utils.database import select_query,create_movies_table, fix_cast,create_movies_table_sql, execute_query,select_query_bkp,backup_table
import random
#df = pd.read_csv('../Recommendation-System/artifacts/data.csv')
# df = pd.read_csv('test.csv')
# df = df.sort_values(by=['title'])
# df['release_date'] = df['release_date'].apply(lambda x: datetime.strptime(x,'%Y-%m-%d').strftime("%d %b %Y"))
# df.genres = df.genres.apply(literal_eval)
# df.genres = df.genres.apply(lambda x: [v for obj in x for k,v in obj.items() if k=='name'])
df = None
#df.budget = df.budget.apply(lambda x: "$ " +"{:,}".format(x))
cache = dict()
titlemap = None

#print(df.head())
try:
    users = pd.read_csv('userdata.csv',converters={"movies": literal_eval, 'ratings': literal_eval})
    que = ''' select id , id as Link , name as Value from actors_db order by popularity desc;'''
    movie_data = select_query(que)
    cache[que] = movie_data 
    que = ''' select year as Value, rowid as Link from  movies_db where year !=0 group by year order by year ;'''
    movie_data = select_query(que)
    cache[que] = movie_data 
    que = ''' select id, title from movies_db;'''
    movie_data = select_query(que)

    cache[que] = movie_data 

except:
    users = pd.DataFrame(columns=['_id','email','password','movies','ratings'])

application = Flask(__name__)

app = application
app.secret_key = "super secret key"


# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# Creating an SQLAlchemy instance
db = SQLAlchemy(app)
count = 0
# Returns if an actor (by idx) was in cast of a movie (by movie)
def searchbyid(idx,row):
    
    # Returns a dataframe of cast given a movie row
    def castdets(row):
        cast = literal_eval(row)
        dummy = pd.DataFrame()
        for m in cast:
            dummy = dummy.append(pd.DataFrame.from_dict(m,orient='index').transpose(),ignore_index=True)
        return dummy
    
    newdf= castdets(row)
    if not newdf.query("id=="+str(idx)).empty:
        return True
    return False

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for("login"))
        return route(*args, **kwargs)
    return route_wrapper

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/_get_titles')
def get_titles():
    global cache
    global titlemap
    if not titlemap:
        movies = cache.get(''' select id, title from movies_db;''')
        movies = movies.to_dict()
        movies = {movies['title'][k]:v for k,v in movies['id'].items()}
        movies = {str(k)+" (Movie) ":v for k,v in movies.items()}
        
        actors = cache.get(''' select id , id as Link , name as Value from actors_db order by popularity desc;''')
        actors = actors[['Link','Value']].to_dict() #list(json.loads(que).values())
        actors = {actors['Value'][k]:v for k,v in actors['Link'].items()}
        actors = {str(k)+" (Actor) ":v for k,v in actors.items()}
        titles = list(movies.keys()) + list(actors.keys())
        titlemap = {**movies, **actors}
    else:
        titles = list(titlemap.keys())
    
    return {"values":titles,"len":len(titles)}


@app.route('/')
@login_required
def index():
    #display_all(loading= True)
    return render_template('index.html',title = "Movies DB", movies=[])

@app.route('/recommend/')
@login_required
def recommend():
    #df.loc[df.index==0,'trailers']='https://trailers.mubicdn.net/959/optimised/720p-t-ariel_en_us_1280_720_1512009289.mp4'
    pg = request.args.get('page')
    usermovies = users[users['_id']==session["user_id"]]['ratings'].squeeze()
    usermovies = list(usermovies.keys())
    recommend = [] 
    m = ModelTrainer()
    global que
    if len(m.movie2idx) != cache[que].shape[0] :
        m.reload()
    
    # for i in usermovies:
    #     recommend= recommend + m.recommend_by_id(i,10)
    
    # recommend = ','.join([str(i) for i in recommend])
    # movies = select_query(get_query('movie_ids',recommend))
   
    # movies = movies.apply(clean_movie,axis=1)
    # inp = random.randint(0,len(usermovies)-1)
    # name = m.idx2movie[m.m_id2idx[usermovies[inp]]]
    # rec_dic = { 1: ('Based on your watched Movies', movies.sample(frac=1).head()),
    #              2: (f'Since you watched {name}', movies.iloc[inp*10:inp*10+5])
    # }
    search,movies = surprise_me(usermovies, m) #rec_dic[random.randint(1,2)]
    
    last = (movies.shape[0] // 5)
    last = last + 1 if movies.shape[0] % 5 else last
    if pg:
        if pg!='last':
            pg_s,pg_e = (int(pg)-1)*5, (5*(int(pg)-1)+5) 
        elif int(pg)> df.shape[0]/5:
            return render_template('recommend.html',movies=pd.DataFrame(),title = "Movies DB",page=1,last=last, search= search)
        else:
            pg_s,pg_e = (-5, None)
        return render_template('recommend.html',movies=movies[pg_s: pg_e],title = "Movies DB",page=pg,last=last, search= search)
    
    return render_template('recommend.html',movies=movies[0:5],title = "For you..",page=1,last=last, search= search)

@app.route('/movies/')
@login_required
def movies():
    #df.loc[df.index==0,'trailers']='https://trailers.mubicdn.net/959/optimised/720p-t-ariel_en_us_1280_720_1512009289.mp4'
    pg = request.args.get('page')
    val = request.args.get('val')
    filter = request.args.get('filter')
    
    ''' 
    if filter == 'search':
        movies = pd.DataFrame()
        for c in df.columns:
            combo = df[df[c].astype('str').str.contains(val, regex=True)]
            movies = movies.append(combo, ignore_index = True)
        movies = movies.drop_duplicates('id')
        
    elif filter == 'cast':
        # movies = df[df[filter].astype('str').str.contains(val, regex=True)]
        # movies = movies[movies[filter].apply(lambda x: searchbyid(val,x))]
        movies = select_query(f'select * from movies_db,json_each(movies_db.cast) where json_each.value->"$.id" = "{val}"; ')
        
        #print(movies.poster_path)
        #dumm = literal_eval(fil.squeevze())
       
        #dumm[1].update({'id':-1})189937
        
        #print(execute_query(f'update movies_db set cast = ? where id=70875;',clean_json(str([dumm[1]]))))
        # cols = get_roles()
        # fil = fil[cols]
        # movies_list = pd.DataFrame()
        # idx_list = []
        # for c in cols:
        #     if fil[c].squeeze() != 'nan':
        #         temp = literal_eval(fil[c].squeeze())
        #         idx_list = idx_list + [ x.get('m_id') for x in temp]
        
        # for idx in idx_list:
        #     movies_list = movies_list.append(select_query(f'select * from movies where id= {float(idx)}'))
        # movies_list = movies_list.sort_values(by='year')
        # cols = df.columns
       
    else:
        movies = df[df[filter].astype('str').str.contains(val, regex=True)] '''
    query = get_query(filter, val)
    #print(query)
    global cache
    if not cache.__contains__(query):
        movies = select_query(query)
        if movies.__contains__('poster_path'):
            movies.poster_path = movies.poster_path.apply(lambda x: 'https://image.tmdb.org/t/p/original'+x if x and 'https' not in x else x)
        if movies.__contains__('trailers'):
            movies.trailers = movies.trailers.apply(extract_trailer)
        cache[query] = movies
    else:
        print('Fetch from cache...')
        movies = cache.get(query)
    
    last = (movies.shape[0] // 5)
    last = last + 1 if movies.shape[0] % 5 else last
    try:
        title = val+" Movies" if filter.lower() not in ['cast', 'movie_ids'] else request.args.get('title')+ ' Movie(s)'
    except:
        title= "Movies DB"
    if pg:
        if pg!='last':
            pg_s,pg_e = (int(pg)-1)*5, (5*(int(pg)-1)+5) 
        elif int(pg)> df.shape[0]/5:
            return render_template('filterresults.html',movies=pd.DataFrame(),title = title,page=1,last=last,val=val,filter=filter)
        else:
            pg_s,pg_e = (-5, None)
        return render_template('filterresults.html',movies=movies[pg_s: pg_e],title = title,page=pg,last=last,val=val,filter=filter)
    
    return render_template('filterresults.html',movies=movies[0:5],title = title,page=1,last=last,val=val,filter=filter)

@app.route('/sm', methods=['POST','GET'])
def something():
    if request.method == 'POST':
        que = request.form.get('query')
        if 'select' in que.lower():
            movie_data = select_query(que)
            cols = movie_data.columns
            print(que)
            if 'trailers' in cols:
                movie_data.trailers = movie_data.trailers.apply(extract_trailer)
            #print(movie_data.trailers)
            return render_template("querysql.html", title="Movies DB", movies_data=movie_data.head(20),cols =cols)
        else:
            return render_template("querysql.html", title="Movies DB", movies_data=pd.DataFrame(),cols =[])
    else:
        return render_template("querysql.html", title="Query DB",movies_data=pd.DataFrame(),cols =[])
    #return render_template('tabledata.html',title = "Movies DB", movies_data= df[df['id']==2])

@app.route('/table_filter')
def table_filter():

    que = ''' select movies_db.id as id, json_each.value->'$.id' as Link , json_each.value->>'$.name' as Genre from movies_db,json_each(genres) where genres != "[]" group by json_each.value;'''
    movie_data = select_query(que)
    
    if not movie_data.empty:
        cols = movie_data.columns
        movie_data.to_json('data.json')
        return render_template("table_genres.html", title="Movies DB", movies_data=movie_data,cols =cols)
    else:
        return render_template("table_genres.html", title="Movies DB", movies_data=pd.DataFrame(),cols =[])
   
    
    #return render_template('tabledata.html',title = "Movies DB", movies_data= df[df['id']==2])

@app.route('/_get_table')
def get_table():
    global cache 
    
    fil = request.args.get('tbl_name')
    
    dic = {
        'Languages': ''' select movies_db.id as id, json_each.value->'$.id' as Link , json_each.value->>'$.english_name' as Value from movies_db,json_each(spoken_languages) where spoken_languages != "[]" group by json_each.value;''',
        'Genres': ''' select movies_db.id as id, json_each.value->'$.id' as Link , json_each.value->>'$.name' as Value from movies_db,json_each(genres) where genres != "[]" group by json_each.value;''',
        'Cast': ''' select id , id as Link , name as Value from actors_db order by popularity desc;''',
        'Year': ''' select year as Value, rowid as Link from  movies_db where year !=0 group by year order by year ;'''
    }
    que = dic.get(fil, dic.get('Genres'))
    if cache.__contains__(que):
        movie_data = cache.get(que)
        print('Fetch from cache..')
        
    else:
        movie_data = select_query(que)
        cache[que] = movie_data 
    if movie_data.__contains__('id'):
        data = [{'Link':l, 'Value':v, 'Id':i} for l,v,i in zip(list(range(1,len(movie_data)+1)), movie_data.Value.to_list(), movie_data.id.to_list())]
    else:
       data = [{'Link':l, 'Value':v} for l,v in zip(list(range(1,len(movie_data)+1)), movie_data.Value.to_list())]
 
    print('Loading complete...')
    #print(json.dumps(movie_data.iloc[:,1:].to_json()))
    return json.dumps(data) #.to_html(classes='table table-striped" id = "data" style="color: var(--accent-colour) !important; ',
                                      # index=False, border=0))
     

@app.route('/<path:path>')
def unknownpath(path):
    return render_template('index.html',title = "Movies DB")

@app.route('/toggle_theme')
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    return redirect(request.args.get("current_page"))


''' @app.route('/fav_movie', methods=['POST','GET'])
@login_required
def fav_movie():
    form = MovieForm()
    if form.validate_on_submit():
        movie = {
            "_id": uuid.uuid4().hex,
            "title": form.title.data,
            "year": form.year.data
        }
        session["movie"] = movie
        user_id= session["user_id"]
        users.loc[users['_id']==user_id,["movies"]].squeeze().append(movie['title'])
        users.loc[users['_id']==user_id,["ratings"]].squeeze().update({movie['title']: 0})
        users.to_csv('userdata.csv',index=False)
        return redirect(url_for("movie",mov_id=movie['id']))
    
    return render_template(
        "new_movie.html", title="Movies DB - My Favorite Movie", form=form
    ) '''

@app.route("/movie/<int:mov_id>")
def movie(mov_id: int, ratings= 0):
    
    #movie = df[df['id']==mov_id].squeeze()
    q = f'select * from movies_db where id = {mov_id};'
    global cache
    if cache.__contains__(q):
        movie = cache.get(q)
        print('Fetch from Cache.. ')
    else:
        movie = select_query(q)
        if movie.empty:
            movie = get_details(mov_id).squeeze()
            return render_template("movie_details.html", movie=movie, ratings = ratings, title=movie.title)
        if movie.shape[0]>1:
            raise Exception(f'More than one movie with Id {mov_id}')
        movie = movie.squeeze()
        
        movie = clean_movie(movie,images=True)
        cache[q] = movie
    if not movie.empty and session.get('user_id'):
        ratings = users.loc[users['_id']==session["user_id"],'ratings'].squeeze().get(mov_id)
        ratings = 0 if not ratings else ratings
        
    elif not movie.empty:
        ratings = 0 
    else:
        movie = df[df['title']==None].squeeze() # add spell check
    
        
    return render_template("movie_details.html", movie=movie, ratings = ratings, title=movie.title)


@app.route("/actor/<int:act_id>")
def actors(act_id: int):
    
    #actor = df[df['id']==mov_id].squeeze()
    q = f'select * from actors_db where id = {act_id};'
    global cache
    if cache.__contains__(q):
        actor = cache.get(q)
        print('Fetch from Cache.. ')
    else:
        actor = select_query(q)
        
        if actor.shape[0]>1:
            raise Exception(f'More than one Actor with Id {act_id}')
        elif actor.empty:
            actor = get_details(act_id, "actor")
       
        actor = actor.squeeze()
        actor = clean_actor_dets(actor)
        cache[q] = actor
    
    return render_template("actor_details.html", actor=actor, title=actor.get('name'))

@app.route('/display_all')
@login_required
def display_all(loading=False):
    movie_data = select_query(get_query(filter='all_movies'))
    user_ratings = users[users['_id']==session["user_id"]]['ratings'].squeeze()
    for k,v in user_ratings.items():
        movie_data.loc[movie_data['id']==k, 'rating'] = int(v)
    
    movie_data = movie_data.apply(clean_movie,axis=1)
    #movie_data['rating'] = movie_data['rating'].apply(lambda x: 0 if str(x)=='nan' else x)
    movie_data = movie_data[['id','title', 'genres', 'release_date','poster_path', 'overview',
        'vote_average','runtime','spoken_languages']]
    cols = ['id','title', 'genres', 'release date', 'poster','overview',
        'average votes', 'runtime','languages']
    
    
    if not loading:
        return render_template("tabledata.html", title="Movies DB", movies_data=movie_data,cols=cols)
    
@app.route('/display_usermovies')
@login_required
def display_usermovies():
    #user_moviedata = users[users['_id']==session["user_id"]]['movies'].squeeze()
    user_ratings = users[users['_id']==session["user_id"]]['ratings'].squeeze()
    user_moviedata = list(user_ratings.keys())
    que = get_query('movie_ids',user_moviedata)
    global cache
    if not cache.__contains__(que):
        movie_data = select_query(que) #df[df['id'].isin(user_moviedata)].copy()
    
        movie_data = movie_data.apply(clean_movie,axis=1)
        
        cache[que] = movie_data
    else:
        movie_data = cache.get(que)
        print('Fetching from Cache..')
    
    for k,v in user_ratings.items():
            movie_data.loc[movie_data['id']==k, 'rating'] = int(v)
    movie_data = movie_data[['id','title', 'genres', 'release_date','poster_path', 'overview',
             'rating','runtime','spoken_languages']]
    cols = ['id','title', 'genres', 'release date', 'poster','overview',
         'your rating','runtime','languages']
    
    return render_template("tabledata.html", title="Movies DB", movies_data=movie_data.head(100),cols =cols)
    

@app.route("/movie/<string:mov_id>/rate")
@login_required
def rate_movie(mov_id):
    rating = int(request.args.get("rating")) if request.args.get("rating") else 0
    mov_id = int(mov_id)
    users.loc[users['_id']==session["user_id"],'ratings'].squeeze().update({mov_id:rating})
    users.to_csv('userdata.csv',index=False)
    return redirect(url_for("movie", mov_id=mov_id, ratings=rating))

@app.route("/register", methods=["POST", "GET"])
def register():
    if session.get("email"):
        return redirect(url_for("index"))

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data),
        )
        global users
        users = users.append(asdict(user), ignore_index = True)
        users.to_csv('userdata.csv',index=False)

        flash("User registered successfully", "success")

        return redirect(url_for("login"))

    return render_template(
        "register.html", title="Movies DB - Register", form=form
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user_data = users[users['email']==form.email.data].squeeze()
        if user_data.empty:
            flash("Login credentials not correct", category="danger")
            return redirect(url_for("login"))
        user = User(**user_data)

        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email
            session["role"] = user.role
            return redirect(url_for("index"))

        flash("Login credentials not correct", category="danger")

    return render_template("login.html", title="Movies DB - Login", form=form)

@app.route("/logout")
@login_required
def logout():
    current_theme = session.get("theme")
    session.clear()
    session["theme"] = current_theme
    users.to_csv('userdata.csv',index=False)
    return redirect(url_for("login"))

@app.route('/search')  # 'GET' is the default method, you don't need to mention it explicitly
def search():
    # query = request.args['search']
    query = request.args.get('search')  # try this instead
    global titlemap
    val = titlemap.get(query)
    if '(Movie)' in query:
        return redirect(url_for('movies', filter='movie_ids',val = val, title=query.split(' (Movie)')[0]))
    else:
        return redirect(url_for('movies', filter='cast',val = val ,title=query.split(' (Actor)')[0]))
    #print(query)
    return redirect(url_for('movies', filter='search',val=query))

@app.route("/admin")
@login_required
def admin():
    if session.get('role') == 'admin':
        myusers = users[['_id','email','movies','ratings']].copy()
        global cache
        ratings = {}
        for i in myusers.index.to_list():  
            movies = list(myusers.loc[myusers.index==i,'ratings'].squeeze().keys())
            
            que = get_query('movie_ids',movies)
            
            if not cache.__contains__(que):
                movie_data = select_query(que)
                #movie_data = movie_data.apply(clean_movie,axis=1)
            else:
                movie_data = cache.get(que)
            myusers.loc[myusers.index==i,'movies'] = myusers.loc[myusers.index==i,'movies'].apply(lambda x:  movie_data.title.to_list()) #myusers.movies.apply(lambda x: [ df[df.id==int(m)].title.squeeze() for m in x])
           
            k = myusers.loc[myusers.index==i,'ratings'].squeeze()
            
            for z,v in k.items():
                movie_data.loc[movie_data['id']==z, 'rating'] = int(v)
               
            ratings[i]= {k:v for k,v in zip(movie_data.title.to_list(), movie_data.rating.to_list())}
        
        
        return render_template('admin_dashboard.html',users=myusers,ratings=ratings)
    return redirect(url_for('unknownpath',path='404Error'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True) # map to http://127.0.0.1:5000/


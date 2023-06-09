import sqlite3
import pandas as pd
from ast import literal_eval
from tqdm import tqdm
import json


class DatabaseConnection:

    def __init__ (self,host):
        self.connection = None
        self.host = host

    def __enter__ (self):
        self.connection = sqlite3.connect(self.host)
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or exc_val or exc_tb:
            self.connection.close()
        else:
            self.connection.commit()
            self.connection.close()

def create_movies_table():
    df = pd.read_csv('test.csv')
    with DatabaseConnection('movies_data.db') as conn:
        conn.cursor().execute('drop table movies')
        df.to_sql(name='movies', con=conn,index=False)

def create_any_table(df, name):
    newdf = df.applymap(str)
    with DatabaseConnection('movies_data.db') as conn:
        conn.cursor().execute('drop table if EXISTS '+name)
        newdf.to_sql(name=name, con=conn,index=False)
    
def create_actors_table_sql():
    
    with DatabaseConnection('movies_data.db') as conn:
        conn.cursor().execute('drop table if EXISTS actors_db')
        conn.cursor().execute("CREATE TABLE actors_db( id INT PRIMARY KEY, name varchar, also_known_as varchar, birthday DATE, biography TEXT, gender INT, imdb_id varchar, place_of_birth varchar, popularity REAL, profile_path TEXT,homepage TEXT,known_for_department varchar, cast JSON DEFAULT('[]'),crew JSON DEFAULT('[]')); ")
        conn.cursor().execute('CREATE INDEX actors_db_idx_index ON actors_db(id);')
    return 'Created table'

def create_movies_table_sql():

    with DatabaseConnection('movies_data.db') as conn:
        conn.cursor().execute('drop table if EXISTS movies_db')
        conn.cursor().execute(''' 
    CREATE TABLE movies_db (
    "id" INTEGER,
    "backdrop_path" TEXT,
    "genres" JSON DEFAULT('[]'),
    "homepage" TEXT,
    "imdb_id" varchar,
    "original_language" varchar,
    "original_title" TEXT,
    "overview" TEXT,
    "popularity" REAL,
    "poster_path" TEXT,
    "release_date" DATE,
    "runtime" REAL,
    "spoken_languages" JSON DEFAULT('[]'),
    "keywords" JSON DEFAULT('[]'),
    "status" varchar,
    "tagline" TEXT,
    "title" TEXT,
    "vote_average" REAL,
    "trailers" JSON DEFAULT('[]'),
    "year" INTEGER,
    "cast" JSON DEFAULT('[]'), crew JSON DEFAULT('[]'));''')
        conn.cursor().execute('CREATE INDEX movies_db_idx_index ON movies_db(id);')
        conn.cursor().execute('CREATE INDEX movies_db_title_index ON movies_db(title);')
        conn.cursor().execute('CREATE INDEX movies_db_idx_cast_index ON movies_db(id,movies_db.cast);')
    return 'Created table'

def select_query(que):
    with DatabaseConnection('movies_data.db') as conn:
        # cursor = conn.cursor()
        # cursor.execute(que)
        result = pd.read_sql(que, conn)
        #result = result.drop_duplicates('id')

    return result

def select_query_bkp(que):
    with DatabaseConnection('all_data.db') as conn:
        # cursor = conn.cursor()
        # cursor.execute(que)
        result = pd.read_sql(que, conn)
        result = result.drop_duplicates('id')

    return result


def execute_query(que,*args):
    with DatabaseConnection('movies_data.db') as conn:
        # cursor = conn.cursor()
        # cursor.execute(que)
        
        if args:
            conn.cursor().execute(que,(*args,))
        else:
            conn.cursor().execute(que)
        #result = pd.read_sql(que, conn)

    return 'Done'

def insert_query(dic):

    tup = (dic.get('id'),dic.get('name'), ', '.join(dic.get('also_known_as')), dic.get('birthday'), dic.get('biography'),
           dic.get('gender'),dic.get('imdb_id'),dic.get('place_of_birth'),dic.get('popularity'),
           dic.get('profile_path'),dic.get('homepage'),dic.get('known_for_department'),json.dumps(dic.get('credits').get('cast'))
           ,json.dumps(dic.get('credits').get('crew')))
    #print(dic.get('known_for_department'),type(tup[11]))
    
    with DatabaseConnection('movies_data.db') as conn:
        # cursor = conn.cursor()
        # cursor.execute(que)
        conn.cursor().execute('Insert into actors_db values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',tup)


def insert_query_movies(dic):
      
    trailers = json.dumps(None)
    if dic.get('videos'):
        trailers = json.dumps(dic.get('videos').get('results'))
    year = 0
    if dic.get('release_date'):
        year = int(dic.get('release_date').split('-')[0])
    tup = (dic.get('id'),dic.get('backdrop_path'), json.dumps(dic.get('genres')),dic.get('homepage'),dic.get('imdb_id'), 
           dic.get('original_language'), dic.get('original_title'),dic.get('overview'),
           dic.get('popularity'),dic.get('poster_path'),dic.get('release_date'),dic.get('runtime'),
           json.dumps(dic.get('spoken_languages')),json.dumps(dic.get('keywords')),
           dic.get('status'),dic.get('tagline'),dic.get('title'),dic.get('vote_average'),trailers, year, json.dumps(dic.get('credits').get('cast'))
           ,json.dumps(dic.get('credits').get('crew')))
    #print(dic.get('known_for_department'),type(tup[11]))
    
    with DatabaseConnection('movies_data.db') as conn:
        # cursor = conn.cursor()
        # cursor.execute(que)
        conn.cursor().execute('Insert into movies_db values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',tup)

    

def backup_table(tbl):
    with DatabaseConnection('movies_data.db') as conn:
        conn.cursor().execute(f"drop table if EXISTS {tbl+'_bkp'};")
        conn.cursor().execute(f"CREATE TABLE {tbl+'_bkp'} AS SELECT * FROM {tbl}")
        idx_query = select_query(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{tbl}'").sql.squeeze()
       
        if idx_query.shape[0]>1:
            for idx in idx_query:
                if idx:
                    print(idx)
                    idx2 = idx.replace(tbl, tbl+'_bkp').replace('index', 'index_bkp')
                    conn.cursor().execute(idx2)
        else:
            idx_query = idx_query.replace(tbl, tbl+'_bkp').replace('index', 'index_bkp')
    return tbl+'_bkp created!'

def test():
    with DatabaseConnection('movies_data.db') as conn:
        # cursor = conn.cursor()
        # cursor.execute(que)
        conn.cursor().execute("CREATE TABLE myTbl( domain varchar PRIMARY KEY,linkList JSON DEFAULT('[]'));")
        conn.cursor().execute("INSERT INTO myTbl(domain) VALUES ('blah');")
        conn.cursor().execute("UPDATE myTbl SET linkList = json_insert(linkList, '$[#]', 'www.test.com') WHERE domain='blah';")
        conn.cursor().execute("UPDATE myTbl SET linkList = json_insert(linkList, '$[#]', 'www.exmpl.com') WHERE domain='blah';")
        result = pd.read_sql('SELECT * FROM myTbl;', conn)
    print(result)


def fix_cast(df):
    cast = df[['id','cast']]
    for x in tqdm(cast.iterrows()):
        details = x[1]
        q = details.cast
        #cast.iloc[cast.id==details.id,'fixed_cast']= json.dumps(literal_eval(q))
        with DatabaseConnection('movies_data.db') as conn:
            conn.cursor().execute('''update movies set cast_details = json(?) where id = ?;''',[json.dumps(literal_eval(q)), details.id],)
    return 'Complete'
            
def fix_actors(cols):
    err = []
    # with DatabaseConnection('movies_data.db') as conn:
    #         conn.cursor().execute('''ALTER TABLE movies ADD filmography JSON DEFAULT('[]');''')
    cast =  select_query("select * from actors ;")
    cast = cast[cols+['id']]
    for x in tqdm(cast.iterrows()):
        details = x[1]
        movies_dict = {}
        idx = details.id
        #cast.iloc[cast.id==details.id,'fixed_cast']= json.dumps(literal_eval(q))
        try:
            for c in cols:  
                q = details[c]
                if c == 'Acting_movies':
                    if q=='nan':
                        movies_dict['Actor'] = []
                    else:
                        movies_dict['Actor'] = json.dumps(literal_eval(q))
                else:
                    if q=='nan':
                        movies_dict['Directing'] = []
                    else:
                        movies_dict['Directing'] = json.dumps(literal_eval(q))
            
            with DatabaseConnection('movies_data.db') as conn:
                conn.cursor().execute('''update actors set filmography = json(?) where id = ?;''',[json.dumps(literal_eval(movies_dict)), idx],)
        except:
            err.append(details)
    return ('Complete', err) if err else 'Complete'



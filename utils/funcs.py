import pandas as pd
from ast import literal_eval
import requests
from tqdm import tqdm
import json
from utils.database import insert_query_movies, select_query,insert_query,execute_query
#from youtube_search_scraper import *
from src.data_ingestion import Movie
import random

def clean_df(df):
    movie_data = df.copy()
    movie_data.genres = movie_data.genres.apply(lambda x : " ".join(x))
    movie_data.vote_average = movie_data.vote_average.apply(lambda x : round(x,2) if str(x)!='nan' else 0)
    movie_data.rating = movie_data.rating.apply(lambda x: int(x) if str(x)!='nan' else 'Not Available')
    movie_data.overview = movie_data.overview.apply(str)
    #movie_data['rating'] = movie_data['rating'].apply(lambda x:  if str(x)=='nan' else x)
    movie_data.spoken_languages = movie_data.spoken_languages.apply(
        lambda x: " ".join([ d.get('name')+'( '+d.get('english_name')+')' for d in literal_eval(x) ])  
    )

    return movie_data

def clean_movie(movie, images= False):
    try:
        if movie.__contains__('cast'):
            movie.cast = json.loads(movie.cast)
        if movie.__contains__('crew'):
            crew = json.loads(movie.crew)
            dir = [x for x in crew if x.get('job')=='Director']
            movie.cast = dir + movie.cast + [x for x in crew if x.get('job')!='Director']
            for x in movie.cast:
            
                if str(x.get('profile_path'))=='None':
                    x.update({'profile_path':'data:image/svg+xml, <svg width="68" height="100" class="ipc-icon ipc-icon--inline ipc-media__icon" viewBox="0.75 3 22 22" version="1.1" xmlns="http://www.w3.org/2000/svg"><g transform="translate(3.000000, 2.000000)" fill="gray" role="presentation"><path d="M9,0 C11.49,0 13.5,1.97473684 13.5,4.42105263 C13.5,6.86736841 11.49,8.84210526 9,8.84210526 C6.50999996,8.84210526 4.5,6.86736841 4.5,4.42105263 C4.5,1.97473684 6.50999996,0 9,0 Z M9,21 C5.25,21 1.935,19.2035087 0,16.4807017 C0.045,13.6877193 6,12.1578947 9,12.1578947 C11.985,12.1578947 17.955,13.6877193 18,16.4807017 C16.065,19.2035087 12.75,21 9,21 Z"></path></g></svg>'})
                else:
                    xp = x['profile_path']
                    x['profile_path'] = 'https://image.tmdb.org/t/p/original'+xp if xp and 'https' not in xp and 'svg+xml' not in xp else xp
        
        if movie.__contains__('spoken_languages') and type(movie.get('spoken_languages'))==str:
            movie.spoken_languages = json.loads(movie.spoken_languages)
        if movie.__contains__('genres') and type(movie.get('genres'))==str:
            movie.genres = json.loads(movie.get('genres'))
        if movie.__contains__('trailers'):
            movie.trailers = extract_trailer(movie.trailers)
        if movie.__contains__('poster_path'):
            movie.poster_path = 'https://image.tmdb.org/t/p/original'+movie.poster_path if movie.poster_path and 'https' not in movie.poster_path and 'svg+xml' not in movie.poster_path else movie.poster_path
        if images:
            movie['images'] = get_images(movie.get('imdb_id'),"movie")
    except Exception as e:
        print(e)
    return movie

def clean_actor_dets(actor):
    
    if actor.__contains__('also_known_as') and type(actor.get('also_known_as')) == str:
        actor['also_known_as'] = actor.also_known_as.split(',')
    actor['images'] = get_images(actor.id,"actor")
    actor['gender'] = "Female" if actor.gender==1 else "Male"
    if actor.__contains__('profile_path'):
        actor.profile_path = 'https://image.tmdb.org/t/p/original'+actor.profile_path if actor.profile_path and 'https' not in actor.profile_path and 'svg+xml' not in actor.profile_path else actor.profile_path
    
    if actor.__contains__('cast') and type(actor.get('cast')) == str:
        actor.cast = json.loads(actor.cast)
        for x in actor.cast:
        
            if str(x.get('poster_path'))=='None':
                x.update({'poster_path':'data:image/svg+xml, <svg width="68" height="100" class="ipc-icon ipc-icon--inline ipc-media__icon" viewBox="0.75 3 22 22" version="1.1" xmlns="http://www.w3.org/2000/svg"><g transform="translate(3.000000, 2.000000)" fill="gray" role="presentation"><path d="M9,0 C11.49,0 13.5,1.97473684 13.5,4.42105263 C13.5,6.86736841 11.49,8.84210526 9,8.84210526 C6.50999996,8.84210526 4.5,6.86736841 4.5,4.42105263 C4.5,1.97473684 6.50999996,0 9,0 Z M9,21 C5.25,21 1.935,19.2035087 0,16.4807017 C0.045,13.6877193 6,12.1578947 9,12.1578947 C11.985,12.1578947 17.955,13.6877193 18,16.4807017 C16.065,19.2035087 12.75,21 9,21 Z"></path></g></svg>'})
            else:
                xp = x['poster_path']
                x['poster_path'] = 'https://image.tmdb.org/t/p/original'+xp if xp and 'https' not in xp and 'svg+xml' not in xp else xp

        # imgs = [a.get('backdrop_path'," ") for a in actor.cast]
        # imgs = ['https://image.tmdb.org/t/p/original'+ a for a in imgs if a]
        # actor['images'] = actor['images'] + imgs
    if actor.__contains__('crew') and type(actor.get('crew')) == str:
        actor.crew = json.loads(actor.crew)
        for x in actor.crew:
        
            if str(x.get('poster_path'))=='None':
                x.update({'poster_path':'data:image/svg+xml, <svg width="68" height="100" class="ipc-icon ipc-icon--inline ipc-media__icon" viewBox="0.75 3 22 22" version="1.1" xmlns="http://www.w3.org/2000/svg"><g transform="translate(3.000000, 2.000000)" fill="gray" role="presentation"><path d="M9,0 C11.49,0 13.5,1.97473684 13.5,4.42105263 C13.5,6.86736841 11.49,8.84210526 9,8.84210526 C6.50999996,8.84210526 4.5,6.86736841 4.5,4.42105263 C4.5,1.97473684 6.50999996,0 9,0 Z M9,21 C5.25,21 1.935,19.2035087 0,16.4807017 C0.045,13.6877193 6,12.1578947 9,12.1578947 C11.985,12.1578947 17.955,13.6877193 18,16.4807017 C16.065,19.2035087 12.75,21 9,21 Z"></path></g></svg>'})
            else:
                xp = x['poster_path']
                x['poster_path'] = 'https://image.tmdb.org/t/p/original'+xp if xp and 'https' not in xp and 'svg+xml' not in xp else xp
  
    #     imgs = [a.get('backdrop_path'," ") for a in actor.crew]
    #     imgs = ['https://image.tmdb.org/t/p/original'+ a for a in imgs if a]
    #     actor['images'] = actor['images'] + imgs
    return actor

def get_images(imdb_id,type="movie"):
    df = pd.DataFrame()
    try:
        if type == "movie":
            page=requests.get(f"https://api.themoviedb.org/3/movie/{imdb_id}?api_key=5573865962d8153adc3efb31b4e7e5c4&append_to_response=images")
        else:
            page=requests.get(f"https://api.themoviedb.org/3/person/{imdb_id}?api_key=5573865962d8153adc3efb31b4e7e5c4&append_to_response=images")
        #print(page.json().get('results'))
        page = page.json().get("images")
        result = page.get("backdrops",[]) + page.get("logos",[])+ page.get("posters",[])+page.get("profiles",[])
        result = ["https://image.tmdb.org/t/p/original"+x.get("file_path") for x in result]
        return result
    except Exception as e:
        print(e)
        return []
    
def get_details(imdb_id,type="movie"):
    df = pd.DataFrame()
    try:
        if type == "movie":
            movies_db([imdb_id])
            df = select_query(f'select * from movies_db where id = {imdb_id};')
            df = df.apply(clean_movie,axis=1)     
            
        else:
            df = actors_db(imdb_id)
            df = select_query(f'select * from actors_db where id = {imdb_id};')
            df = df.apply(clean_actor_dets,axis=1)   
           
        return df
    except Exception as e:
        print(e)
        return pd.DataFrame()

def actors_db(idx):
    page = requests.get(f'https://api.themoviedb.org/3/person/{idx}?&api_key=5573865962d8153adc3efb31b4e7e5c4&append_to_response=credits')
    if page:
        obj = page.json()
        try:
            insert_query(obj)
        except Exception as e:
            print(e)
        return obj
     

def movies_db(idx):
    logger = []
    for i in tqdm(idx):
        page = requests.get(f'https://api.themoviedb.org/3/movie/{i}?api_key=5573865962d8153adc3efb31b4e7e5c4&append_to_response=keywords,videos,credits')
        if page:
            obj = page.json()
            insert_query_movies(obj)
        else:
            logger.append(i)
    return obj

def clean_json(que):
    return json.dumps(literal_eval(que))

def get_query(filter,val=None):

    cols = '''movies_db.id, backdrop_path, genres, homepage, imdb_id, original_language, original_title, overview, popularity, poster_path as poster_path, release_date, runtime, 
    spoken_languages, keywords, status, tagline, title, vote_average, trailers, year, movies_db.cast, movies_db.crew'''
    if type(val)==list:
        val = ','.join([str(x) for x in val])
    query_dict = {

        "cast": f'''select {cols} from movies_db where id in (select value->>"$.id" as id from actors_db,json_each(actors_db.cast) where actors_db.id = {val} union select value->>"$.id" as id from actors_db,json_each(actors_db.crew) where actors_db.id = {val});''',
        "actors": f'''select {cols} from movies_db where id in (select value->>"$.id" as id from actors_db,json_each(actors_db.cast) where name like "%{val}%" union select value->>"$.id" as id from actors_db,json_each(actors_db.crew) where name like "%{val}%");''',
        "genres": f"select {cols} from movies_db,json_each(movies_db.genres) where json_each.value->'$.name' like '%{val}%'; ",
        "overview": f"select {cols} from movies_db where overview like '%{val}%'; ",
        "title": f"select {cols} from movies_db where title like '%{val}%'; ",
        "character": f"select {cols} from movies_db,json_each(movies_db.cast) where json_each.value->'$.character' like '%{val}%'; ",
        "year": f"select {cols} from movies_db where year = '{val}'; ",
        "spoken_languages": f"select {cols} from movies_db,json_each(movies_db.spoken_languages) where json_each.value->'$.english_name' like '%{val}%'; ",
        "languages": f"select {cols} from movies_db,json_each(movies_db.spoken_languages) where json_each.value->'$.english_name' like '%{val}%'; ",
        "imdb_id": f"select {cols} from movies_db where imdb_id = '{val}';",
        "movie_ids": f"select {cols} from movies_db where id in ({val});",
        "movie_ids_index" : f"SELECT {cols} FROM movies_db ORDER BY RANDOM() LIMIT 5;",
        "all_movies": f"select {cols} from movies_db;",

    }
    filter = filter.lower()

    if filter in query_dict.keys():
        return query_dict.get(filter)
        
    return 'union '.join([x.replace(';',' ') for x in list(query_dict.values())[1:6]])+';'

def extract_trailer(videos):
    try:
        temp = json.loads(videos) if type(videos) == str else videos
        
        if len(temp) == 1:
            return 'https://youtube.com/embed/'+temp[0].get('key')
        elif temp.__contains__('youtube'):
            for t in temp.get('youtube'):
                if 'trailer' in t.get('name').lower():
                    return 'https://youtube.com/embed/'+t.get('source')
            #return 'https://youtube.com/embed/'+temp.get('youtube')[0].get('source')
        for t in temp:
            if 'trailer' in t.get('name').lower():
                return 'https://youtube.com/embed/'+t.get('key')
        return '[]'
    except Exception as e:
        return videos
   


'''
SELECT "CREATE TEMP VIEW my_view_1 AS 
SELECT " ||  (SELECT group_concat(name, ', ') FROM pragma_table_info('my_table') WHERE  name != 'id') || " FROM my_table";
'''


'''def get_yt_trailer(missing):
    missing_list = {}
    for x,y,z in missing:
        youtube.search(keyword=f'{x} {y} official trailer')
        response=youtube.search_results()
        data=response['body']
        missing_list[z]= data
    print(missing_list)
    return missing_list'''


def link_from_url(obj, name, year):
    def extract_link(link):
        return link.split('=')[1].split('&')[0] if link else None

    options = {}
    for a in obj:
        y = a.get('title').lower()
        if 'trailer' in y and (name.lower() in y) and (str(year) in y or 'official' in y or 'full' in y):
            return 'https://youtube.com/embed/'+extract_link(a.get('link'))
        elif 'teaser' in y and (name.lower() in y) and (str(year) in y or 'official' in y or 'full' in y):
            return 'https://youtube.com/embed/'+extract_link(a.get('link'))
        elif 'preview' in y and (name.lower() in y) and (str(year) in y or 'official' in y or 'full' in y):
            return 'https://youtube.com/embed/'+extract_link(a.get('link'))
        elif (name.lower() in y) and 'teaser' in y:
            options[y] = 'https://youtube.com/embed/'+extract_link(a.get('link'))
    return options


def surprise_me(usermovies, m):
    choice = random.randint(1,3) 
    name = ""
    if choice == 1:
        recommend = []
        for i in usermovies:
            recommend= recommend + m.recommend_by_id(i,5)
    
        recommend = ','.join([str(i) for i in random.choices(recommend, k=10)])
        movies = select_query(get_query('movie_ids',recommend)).head()
    elif choice == 2:
        inp = random.randint(0,len(usermovies)-1)
        m_id = usermovies[inp]
        name = m.idx2movie[m.m_id2idx[m_id]]
        recommend = ','.join([str(i) for i in random.choices(m.recommend_by_id(m_id,5), k=10)])
        movies = select_query(get_query('movie_ids',recommend)).head()
    else:
        movies = select_query(get_query('movie_ids_index'))
    movies = movies.apply(clean_movie,axis=1)
    
    
    rec_dic = { 1: ('Based on your watched Movies', movies),#movies.sample(frac=1).head()),
                 2: (f'Since you watched {name}', movies),
                 3: (f'Try something new today', movies)
    }
    return rec_dic[choice]

     
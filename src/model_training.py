import pandas as pd
from ast import literal_eval
import json
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .io_funcs import save_object,load_object

from tqdm.notebook import tqdm
tqdm.pandas()
from utils.database import select_query
from src.exception import CustomException
# import importlib,sys
# importlib.reload(sys.modules['src.utils'])


class ModelTrainer:
    
    # convert the relevant data for each movie into a single string to be 
    # used by TfIdf
    def __init__(self):
        try:
            self.X = load_object('artifacts/model.pickle')
            self.movie2idx = load_object('artifacts/movie2idx.pickle')
            self.m_id2idx = load_object('artifacts/m_id2idx.pickle')
            self.actors_model = load_object('artifacts/actors_model.pickle')
            self.idx2movie = load_object('artifacts/idx2movie.pickle')
        except:
            self.reload()
    
    def reload(self):
            self.df = select_query('select * from movies_db;');
            self.fit_tfidf()
    
    def genres_and_keywords_to_string(self, row):
        try:
            genres = json.loads(row['genres'])
            genres = ' '.join(''.join(jj['name'].split()).lower() for jj in genres)
        except:
            genres = literal_eval(row['genres'])
            genres = ' '.join(''.join(jj['name'].split()).lower() for jj in genres)

        try:
            keywords = json.loads(row['keywords']).get('keywords')
            keywords = ' '.join(''.join(jj['name'].split()).lower() for jj in keywords)
            
        except:
            keywords = literal_eval(row['keywords'])
            keywords = ' '.join(''.join(jj['name'].split()).lower() for jj in keywords)
        
        try:
            languages = json.loads(row['spoken_languages'])
            languages = ' '.join(''.join(jj['english_name'].split()).lower()+'LANG' for jj in languages)
            
        except:
            languages = literal_eval(row['spoken_languages'])
            languages = ' '.join(''.join(jj['english_name'].split()).lower()+'LANG' for jj in languages)
        
        return f"{genres} {keywords} {languages}"
    
    def fit_tfidf(self):
        self.df['string'] = self.df.apply(self.genres_and_keywords_to_string,axis=1)
        tfidf = TfidfVectorizer(max_features=4500)
        self.X = tfidf.fit_transform(self.df['string'])

        self.movie2idx = pd.Series(self.df.index, index = self.df['title'])
        self.m_id2idx = pd.Series(self.df.index, index = self.df['id'])

        save_object('artifacts/vectorizer.pickle',tfidf)
        save_object('artifacts/movie2idx.pickle',self.movie2idx)
        save_object('artifacts/model.pickle',self.X)
        save_object('artifacts/m_id2idx.pickle', self.m_id2idx)

        self.df['cast_string'] = self.df.apply(self.cast_crew_to_string,axis=1)
        
        tfidf = TfidfVectorizer(max_features=65000)
        self.actors_model = tfidf.fit_transform(self.df['cast_string'])
        save_object('artifacts/actors_model.pickle',self.actors_model)

        self.idx2movie = pd.Series([k for k,v in self.movie2idx.items()], index = [v for k,v in self.movie2idx.items()])
        save_object('artifacts/idx2movie.pickle',self.idx2movie)

       

    # create a function that generates recommendation
    def recommend_by_title(self,title,K=5):
        # get the row in the dataframe for this movie
        try:
            idx = self.movie2idx[title]
            
        #In case of multiple same titles, the return type of above could be a pd series
            if type(idx) == pd.Series:
                idx = idx.iloc[0]
            idx = self.get_m_id(idx)
            return self.recommend_by_id(idx)
        except Exception as e:
            raise CustomException(e,sys)
            return 'The movie not found. :( \nTry another movie.'
        
        
    def recommend_by_id(self,idx,K=5):
    
        try:
            if type(idx)==str:
                idx = int(idx)
            idx = self.m_id2idx[idx]
            query = self.X[idx] # get the vector TF-IDF vectorized for the title
            scores = cosine_similarity(query, self.X)
            
            # flatten the 1xN array to 1-D
            scores = scores.flatten()
            
            # get the indexes of highest scoring movies except itself
            # for K recommendations
            recommended_idx = (-scores).argsort()[1:K+1]
            recommended_idx = [x for x in recommended_idx if scores[x]>0]

            query = self.actors_model[idx]
            scores = cosine_similarity(query, self.actors_model)
            scores = scores.flatten()
            recommended_idx_cast = (-scores).argsort()[0:K+1]
            recommended_idx_cast = [x for x in recommended_idx_cast if scores[x]>0]
            # return the titles of the recommendations
            mov_idx  = []
            for t in set(list(recommended_idx)+ list(recommended_idx_cast)):
                if t != idx :
                    mov_idx.append(self.get_m_id(t))
                   
            return mov_idx
        except Exception as e:
            raise CustomException(e,sys)
            return 'The movie not found. :( \nTry another movie.'
        
    def get_m_id(self, idx):

        return {v:k for k,v in self.m_id2idx.items()}.get(idx)
    
    def cast_crew_to_string(self, row):
        try:
            cast = json.loads(row['cast'])
            cast = ' '.join(''.join(jj['name'].split()+[str(jj['id'])]).lower() for jj in cast if jj['popularity']>2.5
                            and 'uncredited' not in  jj['character'].lower() and 'self' not in  jj['character'].lower()
                            and 'special appearance' not in  jj['character'].lower() and 'cameo' not in  jj['character'].lower()
                            )
        except:
            cast = literal_eval(row['cast'])
            cast = ' '.join(''.join(jj['name'].split()+[str(jj['id'])]).lower() for jj in cast if jj['popularity']>2.5
                            and 'uncredited' not in  jj['character'].lower() and 'self' not in  jj['character'].lower()
                            and 'special appearance' not in  jj['character'].lower() and 'cameo' not in  jj['character'].lower())

        try:
            crew = json.loads(row['crew'])
            crew = ' '.join(''.join(jj['name'].split()+[str(jj['id'])]).lower() for jj in crew if jj['job']=='Director')
        except:
            crew = literal_eval(row['crew'])
            crew = ' '.join(''.join(jj['name'].split()+[str(jj['id'])]).lower() for jj in crew if jj['job']=='Director')
        return f'{cast} {crew}'
    
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from dataclasses import dataclass, field
from tqdm import tqdm

@dataclass
class Movie:
    _id: str  = field(default_factory=int)
    title: str = field(default_factory=str)
    original_language: str = field(default_factory=str)
    url: str = field(default_factory=str)
    overview: str = field(default_factory=str)

    def get_movies(self):

        self.dataFrame=pd.DataFrame()
        total_pages = 550
        for i in tqdm(range(1,total_pages+1)):
            page=requests.get("https://api.themoviedb.org/3/movie/top_rated?api_key=5573865962d8153adc3efb31b4e7e5c4&language=en-US&page={}".format(i))
            #print(page.json().get('results'))
            result=page.json().get('results')
            temp=pd.DataFrame(result)
            self.dataFrame= self.dataFrame.append(temp,ignore_index=True)

    def get_moviebyid(self,idx):
        
        self.dataFrame=pd.DataFrame()
        for i in tqdm(idx):
            page=requests.get(f"https://api.themoviedb.org/3/movie/{i}?api_key=5573865962d8153adc3efb31b4e7e5c4&append_to_response=trailers")
            #print(page.json().get('results'))
            
            result = pd.DataFrame.from_dict(page.json(),orient='index')
            result = result.transpose()
           
            self.dataFrame= self.dataFrame.append(result,ignore_index=True)
            if not page:
                self.log(i)
        
    def store_df(self, name):
        self.dataFrame.to_csv(name, index=False)

    def log(self, content, name='logger.txt'):
        with open(name, 'a') as f:
            f.write(str(content)+"\n")

# my_movie = Movie()
# idx = pd.read_csv('idxmovies.csv')
# idx = idx.ids.to_list()
# my_movie.get_moviebyid(idx)
# my_movie.store_df('data_with_trailers.csv')

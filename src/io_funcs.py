import os
import sys

import numpy as np
import pandas as pd
import dill
import re
from collections import Counter

from src.exception import CustomException


def save_object(file_path,obj):

    try:
        dir_path = os.path.dirname(file_path)

        os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "wb") as file_obj:
            dill.dump(obj, file_obj)
    
    except Exception as e:
        raise CustomException(e,sys)


def load_object(file_path):
    try:
        with open(file_path,'rb') as file_obj:
            return dill.load(file_obj)
    except Exception as e:
        raise CustomException(e,sys)
    
    
class CorrectTitle:
    
    def __init__(self,doc):
        # create a frequency table of all the words of the document
        self.titles = [row for row in doc]
        self.all_words = Counter(self.words(doc))

    def get_title_with_correction(self,word):
        return [m for m in self.titles if word.lower() in m.lower()]

    # function to tokenise words
    def words(self,document):
        "Convert text to lower case and tokenise the document"
        all_titles = []
        for row in document:
            all_titles+= re.findall(r'[\w-]+', row.lower())
        return all_titles

    def edits_one(self,word):
        "Create all edits that are one edit away from `word`."
        alphabets    = 'abcdefghijklmnopqrstuvwxyz'
        splits     = [(word[:i], word[i:])                   for i in range(len(word) + 1)]
        deletes    = [left + right[1:]                       for left, right in splits if right]
        inserts    = [left + c + right                       for left, right in splits for c in alphabets]
        replaces   = [left + c + right[1:]                   for left, right in splits if right for c in alphabets]
        transposes = [left + right[1] + right[0] + right[2:] for left, right in splits if len(right)>1]
        return set(deletes + inserts + replaces + transposes)

    def edits_two(self,word):
        "Create all edits that are two edits away from `word`."
        return (e2 for e1 in self.edits_one(word) for e2 in self.edits_one(e1))

    def known(self,words):
        "The subset of `words` that appear in the `all_words`."
        return set(word for word in words if word in self.all_words)

    def possible_corrections(self,word):
        "Generate possible spelling corrections for word."
        return (self.known([word]) or self.known(self.edits_one(word)) or self.known(self.edits_two(word)) or [word])
    
    def prob(self,word, N=0): 
        "Probability of `word`: Number of appearances of 'word' / total number of tokens"
        N = sum(self.all_words.values())
        return self.all_words[word] / N
    
    def spell_check(self,word):
        "Print the most probable spelling correction for `word` out of all the `possible_corrections`"
        correct_word = max(self.possible_corrections(word), key=self.prob)
        if correct_word != word:
            print( "Did you mean " + correct_word + "?")
            return self.get_title_with_correction(correct_word)
        else:
            return self.get_title_with_correction(correct_word)
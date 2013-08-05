from nltk.stem.porter import PorterStemmer
from tagger import tagger
import pickle

weights = pickle.load(open('tagger/data/dict.pkl', 'rb'))
reader = tagger.Reader()
stemmer = tagger.Stemmer(stemmer=PorterStemmer())
rater = tagger.Rater(weights, 2)
get_features = tagger.Tagger(reader, stemmer, rater)

======
tagger
======

Module for extracting tags from text documents.
                   
Copyright (C) 2011 by Alessandro Presta

Configuration
=============

Dependencies:
python2.7, stemming, nltk (optional), lxml (optional)

You can install the stemming package with::

    $ easy_install stemming

Usage
=====

Tagging a text document from Python::

    import tagger
    weights = pickle.load(open('data/dict.pkl', 'rb')) # or your own dictionary
    myreader = tagger.Reader() # or your own reader class
    mystemmer = tagger.Stemmer() # or your own stemmer class
    myrater = tagger.Rater(weights) # or your own... (you got the idea)
    mytagger = Tagger(myreader, mystemmer, myrater)
    best_3_tags = mytagger(text_string, 3)

Running the module as a script::

    $ ./tagger.py <text document(s) to tag>

Example::

    $ ./tagger.py tests/*
    Loading dictionary... 
    Tags for  tests/bbc1.txt :
    ['bin laden', 'obama', 'pakistan', 'killed', 'raid']
    Tags for  tests/bbc2.txt :
    ['jo yeates', 'bristol', 'vincent tabak', 'murder', 'strangled']
    Tags for  tests/bbc3.txt :
    ['snp', 'party', 'election', 'scottish', 'labour']
    Tags for  tests/guardian1.txt :
    ['bin laden', 'al-qaida', 'killed', 'pakistan', 'al-fawwaz']
    Tags for  tests/guardian2.txt :
    ['clegg', 'tory', 'lib dem', 'party', 'coalition']
    Tags for  tests/post1.txt :
    ['sony', 'stolen', 'playstation network', 'hacker attack', 'lawsuit']
    Tags for  tests/wikipedia1.txt :
    ['universe', 'anthropic principle', 'observed', 'cosmological', 'theory']
    Tags for  tests/wikipedia2.txt :
    ['beetroot', 'beet', 'betaine', 'blood pressure', 'dietary nitrate']
    Tags for  tests/wikipedia3.txt :
    ['the lounge lizards', 'jazz', 'john lurie', 'musical', 'albums']

A brief explanation
===================

Extracting tags from a text document involves at least three steps: splitting the document into words, grouping together variants of the same word, and ranking them according to their relevance.
These three tasks are carried out respectively by the **Reader**, **Stemmer** and **Rater** classes, and their work is put together by the **Tagger** class.

A **Reader** object may accept as input a document in some format, perform some normalisation of the text (such as turning everything into lower case), analyse the structure of the phrases and punctuation, and return a list of words respecting the order in the text, perhaps with some additional information such as which ones look like proper nouns, or are at the end of a phrase.
A very straightforward way of doing this would be to just match all the words with a regular expression, and this is indeed what the **SimpleReader** class does.

The **Stemmer** tries to recognise the root of a word, in order to identify slightly different forms. This is already a quite complicated task, and it's clearly language-specific.
The *stem* module in the NLTK package provides algorithms for many languages
and integrates nicely with the tagger::
    
    import nltk
    # an English stemmer using Lancaster's algorithm
    mystemmer = Stemmer(nltk.stem.LancasterStemmer)
    # an Italian stemmer
    class MyItalianStemmer(Stemmer):
        def __init__(self):
            Stemmer.__init__(self, nltk.stem.ItalianStemmer)
        def preprocess(self, string):
            # do something with the string before passing it to nltk's stemmer

The **Rater** takes the list of words contained in the document, together with any additional information gathered at the previous stages, and returns a list of tags (i.e. words or small units of text) ordered by some idea of "relevance".

It turns out that just working on the information contained in the document itself is not enough, because it says nothing about the frequency of a term in the language. For this reason, an early "off-line" phase of the algorithm consists in analysing a *corpus* (i.e. a sample of documents written in the same language) to build a dictionary of known words. This is taken care by the **build_dict()** function.
It is advised to build your own dictionaries, and the **build_dict_from_nltk()** function in the *extras* module enables you to use the corpora included in NLTK::
    
    build_dict_from_nltk(output_file, nltk.corpus.brown, 
                         nltk.corpus.stopwords.words('english'), measure='ICF')

So far, we may define the relevance of a word as the product of two distinct functions: one that depends on the document itself, and one that depends on the corpus.
A standard measure in information retrieval is TF-IDF (*term frequency-inverse
document frequency*): the frequency of the word in the document multiplied by
the (logarithm of) the inverse of its frequency in the corpus (i.e. the cardinality of the corpus divided by the number of documents where the word is found).
If we treat the whole corpus as a single document, and count the total occurrences of the term instead, we obtain ICF (*inverse collection frequency*).
Both of these are implemented in the *build_dict* module, and any other reasonable measure should be fine, provided that it is normalised in the interval [0,1]. The dictionary is passed to the **Rater** object as the *weights* argument in its constructor.
We might also want to define the first term of the product in a different way, and this is done by overriding the **rate_tags()** method (which by default calculates TF for each word and multiplies it by its weight)::

    class MyRater(Rater):
        def rate_tags(self, tags):
            # set each tag's rating as you wish

If we were not too picky about the results, these few bits would already make an acceptable tagger.
However, it's a matter of fact that tags formed only by single words are quite limited: while "obama" and "barack obama" are both reasonable tags (and it is quite easy to treat cases like this in order to regard them as equal), having "laden" and "bin" as two separate tags is definitely not acceptable and misleading.
Compare the results on the same document using the **NaiveRater** class (defined in the module *extras*) instead of the standard one.

The *multitag_size* parameter in the **Rater**'s constructor defines the maximum number of words that can constitute a tag. Multitags are generated in the **create_multitags()** method; if additional information about the position of a word in the phrase is available (i.e. the **terminal** member of the class **Tag**), this can be done in a more accurate way.
The rating of a **MultiTag** is computed from the ratings of its unit tags.
By default, the **combined_rating()** method uses the geometric mean, with a special treatment of proper nouns if that information is available too (in the **proper** member).
This method can be overridden too, so there is room for experimentation.

With a few "common sense" heuristics the results are greatly improved.
The final stage of the default rating algorithm involves discarding redundant tags (i.e. tags that contain or are contained in other, less relevant tags).

It should be stressed that the default implementation doesn't make any assumption on the type of document that is being tagged (except for it being written in English) and on the kinds of tags that should be given priority (which sometimes can be a matter of taste or depend on the particular task we are using the tags for).
With some additional assumptions and an accurate treatment of corner cases, the tagger can be tailored to suit the user's needs.

This is proof-of-concept software and extensive experimentation is encouraged. The design of the base classes should allow for this, and the few examples in the *extras* module are a good starting point for customising the algorithm.

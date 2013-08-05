#! /usr/bin/env python
"""
import solver
from scipy.spatial.distance import cosine

terms = solver.sample_terms
msg = "Common Sense in Compensation Act - Prohibits any discretionary monetary payment to an employee of a federal executive agency during the period beginning on the enactment of this Act and the close of FY2013, or during FY2014 or FY2015, to the extent that such payment would cause the employee's total covered compensation (i.e., basic pay and discretionary monetary payment) to exceed 105% of the total amount of such employees basic pay (before the application of any step-increase). Defines \"discretionary monetary payment\" as any award or other monetary payment and any step-increase."
ref = solver.build_reference_featureset(terms)
src = solver.make_ngrams(msg, n=2, stem=True)
sv, tv = solver.align_vectors(src, ref)

distances = []
for term in tv.keys():
    distances.append([cosine([t[1] for t in sv],
                             [t[1] for t in tv[term]]),
                      term])

distances.sort()
for pair in distances:
    print '%s: %s' % (pair[1], pair[0])

"""
import os
import nltk
import re
import json
import requests
import redis
import pickle
import dj_database_url

from nltk.tokenize import word_tokenize as tokenize
from nltk.util import ngrams as ngramify
from nltk.stem.porter import PorterStemmer
from math import exp
from urllib import quote
from pyquery import PyQuery as pq
from scipy.spatial.distance import cosine

from extract import get_features

stemmer = PorterStemmer()
redis_params = dj_database_url.parse(os.environ.get('REDISTOGO_URL'))
cache = redis.Redis(
    host=redis_params['HOST'],
    password=redis_params['PASSWORD'],
    port=redis_params['PORT'],
    )


def choose(text, **kwargs):
    original_terms = kwargs['from_list']
    ref = build_reference_featureset(original_terms)
    src = make_ngrams(text, n=2, stem=True)
    sv, tv = align_vectors(src, ref)
    distances = []
    for term in tv.keys():
        distances.append([cosine([t[1] for t in sv],
                                 [t[1] for t in tv[term]]),
                          term])
    distances.sort()
    match = distances[0][1]
    return [t for t in original_terms if match in t][0]


def rank(text, **kwargs):
    original_terms = kwargs['from_list']
    ref = build_reference_featureset(original_terms)
    src = make_ngrams(text, n=2, stem=True)
    sv, tv = align_vectors(src, ref)
    distances = []
    for term in tv.keys():
        distances.append([cosine([t[1] for t in sv],
                                 [t[1] for t in tv[term]]),
                          term])
    distances.sort()
    distances = [(d[1], d[0]) for d in distances]
    return dict(distances)


def get_text_from_wikipedia_with_redirects(term):
    url = "http://en.wikipedia.org/w/api.php?action=parse&format=json&page=%s&prop=text" % quote(term)
    try:
        result = requests.get(url).text
        data = json.loads(result)['parse']
        page_text = data['text']['*']
        page_title = data['title']
        if pq(page_text).text().startswith('REDIRECT') or 'disambiguation' in page_title:
            page = pq(page_text)
            term = page.find('a').eq(0).attr('href').lstrip('/wiki/')
            print 'Redirecting to %s...' % term
            return get_text_from_wikipedia_with_redirects(term)
        try:
            end = page_text.index('<span class="mw-headline" id="Notes">')
        except ValueError:
            try:
                end = page_text.index('<span class="mw-headline" id="References">')
            except ValueError:
                print "page text was suspect: %s" % page_text
                end = len(page_text) - 1
        trimmed_page_text = page_text[0:end]
        page = pq(trimmed_page_text)
        article = re.sub(r'\[ ?[\d\w]+ ?\]', '', page.text())
    except KeyError, e:
        raise KeyError('KeyError: \'%s\': result was: %s' % (e, result))
    return article


def build_reference_featureset(terms):
    normalized_terms = []
    featureset = {}
    for term in terms:
        normalized_terms.append(re.split(r'\/| and ', term))
    normalized_terms = [term for sublist in normalized_terms for term in sublist]
    for term in normalized_terms:
        cached = cache.get(term)
        if cached:

            featureset[term] = pickle.loads(cached)
            continue
        try:
            text = get_text_from_wikipedia_with_redirects(term)
        except ValueError, e:
            print "Ohnoes! Bad result for %s: %s, skipping" % (term, e)
            continue
        except KeyError, e:
            if "The page you specified doesn't exist" in e:
                print "Skipping %s, no page." % term
                continue
        features = get_features(text, 1000)
        cache.set(term, pickle.dumps(features))
        featureset[term] = features
    return featureset


def make_ngrams(corpus, **kwargs):
    n = kwargs.get('n', 1)
    ncursor = 1
    stem = kwargs.get('stem', True)
    ngrams = tokenize(corpus)
    if stem:
        ngrams = [stemmer.stem(ngram) for ngram in ngrams]
    ncursor += 1
    while ncursor <= n:
        ngrams += ngramify(ngrams, n)
        ncursor += 1
    return ngrams


def align_vectors(source, reference):
    source_aligned = {}
    terms_aligned_base = {}
    # create a source dict
    for ngram in source:
        gram = ngram
        if isinstance(ngram, tuple):
            gram = u' '.join(ngram)
        terms_aligned_base[gram] = 0
        try:
            source_aligned[gram] += 1
        except KeyError:
            source_aligned[gram] = 1
    terms_aligned = {}
    # create individual term dicts that are padded from (and pad out) the source
    for term in reference.keys():
        terms_aligned[term] = terms_aligned_base.copy()
        for tag in reference[term]:
            score = (tag.rating * 1000)
            terms_aligned[term][tag.stem] = score
            source_aligned[tag.stem] = source_aligned.get(tag.stem, 0)
    # revisit the (now complete) source dict to pad out each term again
    for ngram in source_aligned.keys():
        for term in reference.keys():
            if terms_aligned[term].get(ngram) is None:
                terms_aligned[term][ngram] = 0
    # create vectors from source and term dicts
    source_vector = source_aligned.items()
    source_vector.sort()
    term_vectors = {}
    for term in terms_aligned.keys():
        vector = terms_aligned[term].items()
        vector.sort()
        term_vectors[term] = tuple(vector)

    return (tuple(source_vector), term_vectors)

sample_terms = ["Abortion", "Agriculture", "Animal Rights", "Budget/Spending", "Business", "Civil Rights", "Commerce", "Congratulations/Birthdays", "Crime/Drugs", "Debt Ceiling", "Defense", "Education", "Elections", "Energy", "Environment", "Family Values", "Foreign Relations", "Health", "Homeland Security", "Housing", "Immigration", "Intelligence", "Jobs", "Judiciary", "Labor", "Medicare", "Parks and Public Lands", "Pension/Retirement", "Postal", "Regulatory Reform", "Religion", "Science/Technology", "Second Amendment", "Senate Procedure", "Small Business", "Social Security", "Taxes", "Telecommunications", "Tobacco", "Trade", "Transportation", "Unemployment", "Veterans", "Water/Rivers", "Welfare", "Other"]
sample_msg = "Common Sense in Compensation Act - Prohibits any discretionary monetary payment to an employee of a federal executive agency during the period beginning on the enactment of this Act and the close of FY2013, or during FY2014 or FY2015, to the extent that such payment would cause the employee's total covered compensation (i.e., basic pay and discretionary monetary payment) to exceed 105% of the total amount of such employees basic pay (before the application of any step-increase). Defines \"discretionary monetary payment\" as any award or other monetary payment and any step-increase."
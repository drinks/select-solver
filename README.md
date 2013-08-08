# What is this?

This project, working title 'select-solver' for lack of ambition to come up with a name, is a simple flask server for doing wikipedia-based text classification.

**'select-solver'** is a reference to the need this code arose from, which is:

    Given a list of topic-based select list options
        I should be able to determine which one a given passage of text is most likely about.

## How's it work?

To meet these ends, you submit a `get` or `post` request to `/choose.json` with two parameters:

- `text`, the passage to classify. A brief example could be the phrase, **"I like to hunt and shoot things"**.
- `choices`, the list of possible words, comma-separated, that could be used to describe the text. An example might be **"taxes,health care,firearms"**.

From there, this project will attempt to download, tokenize and tag the [wikipedia page](http://wikipedia.com) for each choice you provided. It will also tokenize your input text, and construct [aligned term vectors](http://en.wikipedia.org/wiki/Vector_space_model) for each collection of words.

The term with the vector that is the shortest [cosine distance](http://en.wikipedia.org/wiki/Cosine_similarity) away from your input text gets declared the winner, and returned as a json string.

To see all choices and their associated distances, You can use the endpoint `/rank.json` instead.

## Requirements

This is a flask app designed for Heroku, but can run in any virtualenv environment with access to an internet connection and a Redis server.

If you use heroku, you'll want to compile your stack using a buildpack that includes numpy and scipy, like this one: https://github.com/dbrgn/heroku-buildpack-python-sklearn. You'll also need to install NLTK.

If you're using Foreman, copy .env.example to .env and fill it out with appropriate values.

## Notes

We're doing a lot of calculations on the fly here, and while the feature sets for individual terms are cached in redis, obviously a lot of work could be done to optimize. Depending on how many 'new' words are in your choice set, expect it to take many seconds to get results.

With that said, this is really just a proof of concept and shouldn't **at all** be expected to deliver accurate results. If your use case can deal with slightly better than random accuracy, this is for you.

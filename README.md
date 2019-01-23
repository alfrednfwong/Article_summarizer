# Article summarizer and web scraping

A project on natural language processing at Xccelerate HK. The task is to summarize a news article in four sentences.

For the NLP corpus a script is written to scrape all articles from theonion.com. The target article from CNN is stemmed and have the stop words removed. And then it is vectorized by tfidf rules with the corpus scraped from the onion. The tfidf score is computed for each tokenized sentence, and the four with the highest scores are returned as the summary for the article.

Finally the articles in the corpus are separated into 10 clusters by Kmeans. The cluster number will then be used as output labels to train various classifier models whose accuracy scores are compared.

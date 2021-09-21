#!/usr/bin/env python

from os import environ
from typing import Any, Tuple, List, Dict
from newsapi import NewsApiClient
from newsplease import NewsPlease
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import date
import spacy
import string
from articles_orm import Base, Article, ArticleFeatures
from utils import read_file_content
from pytictoc import TicToc

newsapi = NewsApiClient(api_key=environ['GNEWS_API_KEY'])
database_uri = f"sqlite:///NewsAPI_articles.db"
try:
    if environ['DATABASE_URI'] is not None:
        database_uri = environ['DATABASE_URI'] # switch to postgres db if ran in container
except: 
    pass
engine = create_engine(database_uri)
topic_list = read_file_content('/data/topics.txt')
en_stopwords = read_file_content('/data/stopwords_en.txt')
nlp = spacy.load('en_core_web_md')
nlp.add_pipe("merge_entities")
nlp.add_pipe('money_merger', before='ner')
additional_remove_chars = "'\"`—“’”\n"
punctuation = string.punctuation.replace('-','')+additional_remove_chars
t = TicToc()

def save_to_db(session: Session, mdls: List[Base]):
    session.add_all(mdls)
    session.commit()


def pull_todays_articles() -> Dict[str, Any]:
    return {
        topic: newsapi.get_everything(
            q=topic,
            page_size=100,
            page=1,
            language='en',
            from_param=date.today(),
            to=date.today())
        for topic in topic_list}


def truncate_duplicated_articles(session: Session, todays_articles: Dict[str, Any]) -> List[Tuple[Any, Any]]:
    truncated_articles = []
    _articles_titles = []
    for topic, contents_dict in todays_articles.items():
        for article in contents_dict['articles']:
            is_article_unique = article['title'] not in _articles_titles
            already_in_db = any(session.query(Article).filter(Article.title == article['title']))
            is_article_unique = is_article_unique and not already_in_db
            if (is_article_unique):
                truncated_articles += [(topic, article)] 
                _articles_titles += [article['title']]
    return truncated_articles, _articles_titles


def store_articles_urls(session: Session, todays_articles: Dict[str, Any]) -> List[Any]:
    truncated_articles, _ = truncate_duplicated_articles(session, todays_articles)
    return [(topic, truncated_article['url']) for topic, truncated_article in truncated_articles]


def extract_maintexts(topic_urls: List[Any]) -> None:
    objects = []
    for topic, url in topic_urls:
        try:
            article = NewsPlease.from_url(url)
        except:  # some download error happened, we can afford to skip this article
            continue
        if (article.maintext is not None):
            mdl_article = Article(
                parent_topic=topic,
                source=article.source_domain,
                title=article.title,
                description=article.description,
                maintext=article.maintext,
                publication_date=article.date_publish,
                url=url
            )
            objects += [mdl_article]
    return objects


def preprocess_articles_features(articles: List[Any]) -> List[Any]:
    mdl_articles_features = []
    for article in articles:
        article_doc = nlp(article.maintext)
        lemmas = [token.lemma_ for token in article_doc 
                if 
                token.lemma_ not in en_stopwords 
                and token.lemma_ not in punctuation]
        # clean original lemmas from numericals
        num_numericals = len([lemma for lemma in lemmas if any(char.isdigit() for char in lemma)])
        lemmas = [lemma for lemma in lemmas if not any(char.isdigit() for char in lemma)]
        # pull out named entities as a feature of its own
        named_entities = list(set([f"_{ent.label_}_{ent.text}" for ent in article_doc.ents if ent.label_ in ['GEO', 'ORG', 'PER', 'GPE']]))
        article_lemmatized = ' '.join(lemmas)
        mdl_article_features = ArticleFeatures(
            title_vector=nlp(article.title).vector.tolist(),
            num_numericals=num_numericals,
            named_entities=named_entities,
            lemmatized_text=article_lemmatized
        )
        mdl_article_features.article = article # set up relationship
        mdl_articles_features += [mdl_article_features]
    return mdl_articles_features


if __name__ == "__main__":

    print("#1 Pulling today's articles...")
    t.tic()
    todays_articles = pull_todays_articles()
    t.toc("#1 took")
    # Attempt to create schema. If already exists, will not do anything
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        print('#2 Preparing urls and truncating duplicates...')
        t.tic()
        topic_urls = store_articles_urls(session, todays_articles)
        t.toc("#2 took")
        print("#3 Extracting main content and saving to database...")
        t.tic()
        mdl_articles = extract_maintexts(topic_urls)
        save_to_db(session, mdl_articles)
        t.toc("#3 took")
        print('#4 Preprocessing articles and saving features to database...')
        t.tic()
        mdl_articles_features = preprocess_articles_features(mdl_articles)
        save_to_db(session, mdl_articles_features)
        t.toc("#4 took")
        print("Done, happy analyzing!")
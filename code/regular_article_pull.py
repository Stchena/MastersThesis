#!/usr/bin/env python

from os import environ
from typing import Any, List, Dict
from newsapi import NewsApiClient
from newsplease import NewsPlease
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import DatabaseError
from datetime import date
import spacy
from articles_orm import Base, Article, ArticleFeatures
from utils import read_file_content


newsapi = NewsApiClient(api_key='fbfb692eb3844ce59e10eea6069d1161')
database_uri = f"sqlite:///NewsAPI_articles.db"
try:
    if environ['DATABASE_URI'] is not None:
        database_uri = environ['DATABASE_URI'] # switch to postgres db if ran in container
except: 
    pass
engine = create_engine(database_uri)
topic_list = read_file_content('/data/topics.txt')
nlp = spacy.load('en_core_web_md')


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


def truncate_duplicated_articles(session: Session, todays_articles: Dict[str, Any]) -> Dict[str, List[Any]]:
    truncated_articles = {}
    _articles_titles = []
    for topic in topic_list:
            cta = todays_articles[topic]['articles']
            current_topic_articles = []
            try:
                session.query(Article) # probe the db
                is_table_existent = 1
            except DatabaseError:
                is_table_existent = 0
            for article in cta:
                # check duplicacy against itself and against data already stored in DB (to save only unique articles)
                # checking against DB also prunes cross-topic duplicates
                is_article_unique = article['title'] not in _articles_titles
                if (is_table_existent):
                    is_article_unique = is_article_unique and (not any(session.query(Article).filter(Article.title == article['title'])))
                if (is_article_unique):
                    current_topic_articles += [article]
                    _articles_titles += [article['title']]
            truncated_articles[topic] = current_topic_articles
    return truncated_articles


def store_articles_urls(session: Session, todays_articles: Dict[str, Any]) -> Dict[str, Any]:
    truncated_articles = truncate_duplicated_articles(session, todays_articles)
    topic_urls = {}
    for topic, articles in truncated_articles.items():
        topic_urls[topic] = [article['url'] for article in articles]
    return topic_urls


def extract_and_save_maintexts_to_db(session: Session, topic_urls: List[Any]) -> None:
    objects = []
    for topic in topic_list:
        for url in topic_urls[topic]:
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
        # bulk save all in topic then flush and go again for next topic
        session.bulk_save_objects(objects)
        session.commit()
        objects = []


def preprocess_articles(articles: List[Any]) -> List[Any]:
    return ["done"]


if __name__ == "__main__":

    print("#1 Pulling today's articles...")
    todays_articles = pull_todays_articles()
    # Attempt to create schema. If already exists, will not do anything
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        print('#2 Preparing urls and truncating duplicates...')
        topic_urls = store_articles_urls(session, todays_articles)
        print("#3 Extracting main content and saving to database...")
        extract_and_save_maintexts_to_db(session, topic_urls)
        print('#4 Pulling updated articles from database...')
        articles = session.query(Article).distinct(Article.title).all() # work on cutting duplicates...
    print('#5 Preprocessing texts...')
    something = preprocess_articles(articles)
    print(something[0])
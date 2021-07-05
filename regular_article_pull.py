#!/usr/bin/env python

from typing import Any, List, Dict
from newsapi import NewsApiClient
from newsplease import NewsPlease
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from articles_orm import Base, Article, ArticleFeatures
from datetime import date
from utils import read_topics
import spacy


newsapi = NewsApiClient(api_key='fbfb692eb3844ce59e10eea6069d1161')
engine = create_engine(f"sqlite:///NewsAPI_articles.db")
topic_list = read_topics()
nlp = spacy.load()


def pull_todays_articles() -> Dict[Any, Any]:
    return {
        topic: newsapi.get_everything(
            q=topic,
            page_size=100,
            page=1,
            language='en',
            from_param=date.today(),
            to=date.today())
        for topic in topic_list}


def truncate_duplicated_articles(todays_articles: Dict[Any, Any]) -> Dict[Any, Any]:
    truncated_articles = {}
    for topic in topic_list:
            cta = todays_articles[topic]['articles']
            current_topic_articles = []
            current_topic_articles_titles = []
            for article in cta:
                # check duplicacy against itself and against data already stored in DB (to save only unique articles TEST)
                if ((article['title'] not in current_topic_articles_titles) and
                    (not any(Session(engine).query(Article).filter(Article.title == article['title'])))):
                    current_topic_articles += [article]
                    current_topic_articles_titles += [article['title']]
            truncated_articles[topic] = current_topic_articles
    return truncated_articles


def store_articles_urls(todays_articles: Dict[Any, Any]) -> Dict[Any, Any]:
    truncated_articles = truncate_duplicated_articles(todays_articles)
    topic_urls = {topic: article['url']
                        for topic, article in truncated_articles.items()}
    return topic_urls


def extract_and_save_maintexts_to_db(session, topic_urls: List[Any]) -> None:
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
        # bulk save all topics then flush
        session.bulk_save_objects(objects)
        session.commit()
        objects = []


def preprocess_articles(articles: List[Any]) -> List[Any]:
    pass


if __name__ == "__main__":

    print("#1 Pulling today's articles...")
    todays_articles = pull_todays_articles()
    print('#2 Preparing urls and truncating duplicates...')
    topic_urls = store_articles_urls(todays_articles)
    with Session(engine) as session:
        print("#3 Extracting main content and saving to database...")
        extract_and_save_maintexts_to_db(session, topic_urls)
        print('#4 Pulling updated articles from database...')
        articles = session.query(Article).all()
    print('#5 Preprocessing texts...')
    something = preprocess_articles(articles)
from os import environ
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.append('/app')
from regular_article_pull import save_to_db, truncate_duplicated_articles, store_articles_urls, extract_maintexts, preprocess_articles_features
from articles_orm import Base, Article, ArticleFeatures


database_uri = environ["TEST_DB_URI"]
engine = create_engine(database_uri)
Base.metadata.create_all(engine)


def clear_db():
    for tbl in reversed(Base.metadata.sorted_tables):
        engine.execute(tbl.delete())


def test_truncate_duplicated_articles_when_same_title_same_topic():
    todays_articles = {'bitcoin': {
    "articles": [
        {"title": "Pytest test is the best test among all tests!"
        },
        {"title": "Pytest test is the best test among all tests!"}
    ]
    }
    }
    with Session(engine) as session:
        truncated_articles, titles = truncate_duplicated_articles(session, todays_articles)
    assert len(truncated_articles) == 1


def test_truncate_duplicated_articles_when_same_title_different_topic():
    todays_articles = {'bitcoin': {
    "articles": [
        {"title": "Pytest test is the best test among all tests!"
        }]},
        "crypto": {
            "articles": [
            {"title": "Pytest test is the best test among all tests!"
        }]}
    }
    with Session(engine) as session:
        truncated_articles, _ = truncate_duplicated_articles(session, todays_articles)
    assert len(truncated_articles) == 1


def test_truncate_duplicated_articles_when_article_already_in_db():
    clear_db()
    todays_articles = {'reuters': {"articles": [{"title": "Taliban overrun northern Afghan cities of Kunduz, Sar-e Pul, Taloqan"}]}}
    art1_given = Article(
            parent_topic="reuters",
            source="www.reuters.com",
            title="Taliban overrun northern Afghan cities of Kunduz, Sar-e Pul, Taloqan",
            description="Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday, local officials said, as the insurgents intensified pressure on the north and threatened further cities.",
            maintext="",
            publication_date="",
            url="https://www.reuters.com/world/asia-pacific/taliban-capture-government-buildings-afghan-city-kunduz-2021-08-08/"
            )
    with Session(engine) as session:
        session.add(art1_given)
        session.commit()
        truncated_articles, _ = truncate_duplicated_articles(session, todays_articles)
    assert len(truncated_articles) == 0
    clear_db()


def test_truncate_duplicated_articles_when_similar_title():
    todays_articles = {'bitcoin': {
    "articles": [
        {"title": "Pytest test is the best test among all tests!"},
        {"title": "Pytest test might actually be the best test among all tests!"}]
        }
    }
    with Session(engine) as session:
        truncated_articles, titles = truncate_duplicated_articles(session, todays_articles)
    assert len(truncated_articles) == 0


def test_store_urls():
    todays_articles = {'bitcoin': {
    "articles": [
        {"title": "Bitcoin 1",
        "url": "http://bitcoin1"
        },
        {"title": "Bitcoin 2",
        "url": "http://bitcoin2"}
        ]},
        "crypto": {
            "articles": [
            {"title": "Another one",
            "url": "http://crypto"
        }]}
    }
    with Session(engine) as session:
        urls = store_articles_urls(session, todays_articles)
    assert urls[0][1] == "http://bitcoin1"


def test_extract_maintexts():
    topic_urls = [('reuters', 'https://www.reuters.com/world/asia-pacific/taliban-capture-government-buildings-afghan-city-kunduz-2021-08-08/')]
    art1_given = Article(
            parent_topic="reuters",
            source="www.reuters.com",
            title="Taliban overrun northern Afghan cities of Kunduz, Sar-e Pul, Taloqan",
            description="Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday, local officials said, as the insurgents intensified pressure on the north and threatened further cities.",
            maintext="Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday",
            publication_date="",
            url="https://www.reuters.com/world/asia-pacific/taliban-capture-government-buildings-afghan-city-kunduz-2021-08-08/"
            )
    mdl_articles = extract_maintexts(topic_urls)
    assert mdl_articles[0].maintext[194:306] == art1_given.maintext


def test_preprocess_articles_features():
    articles = [Article(
            parent_topic="reuters",
            source="www.reuters.com",
            title="Taliban overrun northern Afghan cities of Kunduz, Sar-e Pul, Taloqan",
            description="Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday, local officials said, as the insurgents intensified pressure on the north and threatened further cities.",
            maintext="KABUL, Aug 8 (Reuters) - Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday",
            publication_date="",
            url="https://www.reuters.com/world/asia-pacific/taliban-capture-government-buildings-afghan-city-kunduz-2021-08-08/"
            )]
    preprocessed_articles = preprocess_articles_features(articles)
    assert preprocessed_articles[0].num_numericals  == 1
    assert "_GPE_KABUL" in preprocessed_articles[0].named_entities


def test_save_to_db():
    clear_db()
    articles = [Article(
            parent_topic="reuters",
            source="www.reuters.com",
            title="Taliban overrun northern Afghan cities of Kunduz, Sar-e Pul, Taloqan",
            description="Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday, local officials said, as the insurgents intensified pressure on the north and threatened further cities.",
            maintext="KABUL, Aug 8 (Reuters) - Taliban fighters overran three provincial capitals including the strategic northeastern city of Kunduz on Sunday",
            publication_date="",
            url="https://www.reuters.com/world/asia-pacific/taliban-capture-government-buildings-afghan-city-kunduz-2021-08-08/"
            )]
    with Session(engine) as session:
        save_to_db(session, articles)
        art1_test = session.query(Article).first()
        art1_features = preprocess_articles_features([art1_test])
        save_to_db(session, art1_features)
        art1_features_test = session.query(ArticleFeatures).first()
        assert art1_test.url == articles[0].url
        assert art1_test.maintext == articles[0].maintext
        assert type(art1_features_test.title_vector[0]) == type(art1_features[0].title_vector[0]) is float
        assert art1_features_test.num_numericals == art1_features[0].num_numericals == 1
        clear_db()

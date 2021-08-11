from sqlalchemy import ForeignKey, Column, Integer, String, Text, ARRAY, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.sql.sqltypes import Float

Base = declarative_base()
nlp = spacy.load('en_core_web_md')


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    parent_topic = Column(String)
    source = Column(String)
    title = Column(String)
    description = Column(String)
    maintext = Column(Text)
    publication_date = Column(String)
    url = Column(String)
    features = relationship("ArticleFeatures", uselist=False, back_populates="article")
    
    def __init__(self, parent_topic, source, title, description, maintext, publication_date, url):
        self.parent_topic = parent_topic
        self.source = source
        self.title = title
        self.description = description
        self.maintext = maintext
        self.publication_date = publication_date
        self.url = url

    def __str__(self):
        return f'Article(topic={self.parent_topic}, title={self.title}, description={self.description} url={self.url})'

    
class ArticleFeatures(Base):
    __tablename__ = "articles_features"
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, 
                        ForeignKey("articles.id", ondelete='CASCADE'),
                        nullable=False
                        )
    article = relationship(Article, back_populates='features')
    title_vector = Column(ARRAY(Float))
    num_numericals = Column(Integer)
    named_entities = Column(ARRAY(String))
    lemmatized_text = Column(String)
    
    def __init__(self, title_vector, num_numericals, named_entities, lemmatized_text):
        self.title_vector = title_vector
        self.num_numericals = num_numericals
        self.named_entities = named_entities
        self.lemmatized_text = lemmatized_text

    @hybrid_method
    def title_similarity(self, title_vector):
        return (cosine_similarity(self.title_vector, title_vector) > 0.9)

    @title_similarity.expression
    def title_similarity(cls, title_vector):
        return (cosine_similarity(cls.title_vector, title_vector) > 0.9)
        
    def __str__(self):
        return f'ArticleFeatures(title_vector={self.title_vector}, num_numericals={self.num_numericals}, named_entities={self.named_entities} lemmatized_text={self.lemmatized_text})'

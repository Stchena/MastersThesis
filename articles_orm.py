from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


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
    features = relationship("ArticleFeatures", uselist=False, backref="articles")
    
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
    keywords_pca = Column(String)
    keywords_nmf = Column(String)
    
    def __init__(self, keywords_pca, keywords_nmf):
        self.keywords_pca = keywords_pca
        self.keywords_nmf = keywords_nmf
        
    def __str__(self):
        return f'pca: {self.keywords_pca}\n nmf: {self.keywords_nmf}'

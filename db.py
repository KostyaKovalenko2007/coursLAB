from sqlalchemy import Column, Integer, String, create_engine, ForeignKey,Boolean,JSON
from sqlalchemy.orm import sessionmaker,declarative_base
# from os import getenv
import json
Base = declarative_base()


DIALECT = 'postgresql'
USERNAME = 'postgres'
PASSWORD = 'dimkanet'
HOST = 'localhost'
PORT = 5432
DATABASE = 'VKBOT'

# dialect+driver://username:password@host:port/database
DSN = f"{DIALECT}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    vkID = Column(String,unique=True)
    creteria = Column(JSON) #{"city:"","age":"","gender":"", "other":""}


    def __init__(self, client_id:str,creteria:json):
        self.vkID = client_id
        self.creteria=creteria

    def __repr__(self):
        return f'<{self.__class__.__name__} #{self.id}>'



class SearchResult(Base):
    __tablename__ = 'SearchResults'
    id = Column(Integer, primary_key=True)
    clientID = Column(Integer, ForeignKey("clients.id"))
    vkID = Column(String)
    fio = Column(String)
    img1 = Column(String)
    img2 = Column(String)
    img3 = Column(String)

    def __str__(self):
        return f"{self.name} - {self.vkID}"

    def __init__(self, name):
        self.name = name


class Favorite(Base):
    __tablename__ = 'Favorites'
    id = Column(Integer, primary_key=True)
    ClientID = Column(Integer, ForeignKey("clients.id"))
    SearchID = Column(Integer, ForeignKey("SearchResults.id"))
    like = Column(Boolean,default=True)


    def __init__(self, serch_item:SearchResult,like=True):
        self.ClientID = serch_item.id
        self.SearchID = serch_item.vkID
        self.like = like

    def __repr__(self):
        return f'<Favorite#{self.SearchID} tag#{self.like}>'

class BotDB():
    def __init__(self):
        #engine = create_engine("postgresql://vk_bot_lab:Qw123456@192.168.88.4/vkbot")
        #Session = sessionmaker(bind=engine)
        # DSN = getenv('dsn')
        self.engine = create_engine(DSN)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    def create_tables(self):
        Base.metadata.drop_all(self.engine)
        print('Tables cleaned')
        Base.metadata.create_all(self.engine)
        print('Tables created')
        pass
    def create_client(self,vkID,creteria):
        return Client(client_id=vkID,creteria=creteria)
    def get_client_by_vkID(self,vkID:str):
        return self.session.query(Client(vkID=vkID))
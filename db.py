import os

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Boolean, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Query
# from os import getenv
import json

Base = declarative_base()


class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    vkID = Column(String, unique=True)
    creteria = Column(JSON)  # {"city:"","age":"","gender":"", "other":""}
    currentSearchID = Column(Integer, ForeignKey("SearchResults.id"), nullable=True)

    def __init__(self, client_id: str, creteria: json):
        self.vkID = client_id
        self.creteria = creteria
        self.currentSearchID

    def __repr__(self):
        return f'<{self.__class__.__name__} #{self.id}>'
    def get_current(self):
        return self.currentSearchID

    def set_serchID(self,id):
        self.currentSearchID=id


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
    def view(self):
        # формирует  cловарик с ответа ботом
        pass
    def __init__(self, ClientID, vkID, fio, imgs=[]):
        self.vkID = vkID
        self.clientID = ClientID
        self.fio = fio
        self.img1 = imgs[0] if len(imgs) > 0 else ''
        self.img2 = imgs[1] if len(imgs) > 1 else ''
        self.img3 = imgs[2] if len(imgs) > 2 else ''

    def refresh_search(self, client: Client, data: list):
        # Метод удаляет старые результаты поиска (кроме тех которые отмечены как Like/Dislike
        # Наполняет новой выборкой передаваемой в виде списка из словарей
        # устанавливает в профиле клиент значение первого из поисковой выборки
        # не добавляет которые уже помечены как Like/Dislike (если такие попадутся)
        pass

    def get_next_searchID(self):
        # метод возвращает следующий идентификатор профиля из поискового запроса двигаясь последовательно перебирая профили по поисковому запросу
        # возвращает следующий профиль и меняет сслыку currentSearchID
        pass


class Favorite(Base):
    __tablename__ = 'Favorites'
    id = Column(Integer, primary_key=True)
    ClientID = Column(Integer, ForeignKey("clients.id"))
    SearchID = Column(Integer, ForeignKey("SearchResults.id"))
    like = Column(Boolean, default=True)

    def __init__(self, serch_item: SearchResult, like=True):
        self.ClientID = serch_item.id
        self.SearchID = serch_item.vkID
        self.like = like

    def __repr__(self):
        return f'<Favorite#{self.SearchID} tag#{self.like}>'

    def like_correction(self, like=True):
        # Корректирует мнение если оно изменилось
        pass


class BotDB():
    session = None

    def __init__(self):
        # engine = create_engine("postgresql://vk_bot_lab:Qw123456@192.168.88.4/vkbot")
        # Session = sessionmaker(bind=engine)
        # DSN = getenv('dsn')
        self.engine = create_engine(os.getenv('dsn'))
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        Base.metadata.drop_all(self.engine)
        print('Tables cleaned')
        Base.metadata.create_all(self.engine)
        print('Tables created')
        pass

    def create_client(self, vkID, creteria: json):
        client = Client(client_id=vkID, creteria=creteria)
        try:
            self.session.add(client)
            self.session.commit()
            return 1, "Client registered"
        except:
            return 0, f"Can't create record for\n VKID={vkID}\n Criteria={creteria} "

    def get_client_criterias(self, vkID):
        res: Query = self.session.query(Client).filter(Client.vkID == str(vkID))
        if res.count() == 1:
            return json.loads(res.first().creteria)
        else:
            return None

    def update_client_creteria(self, vkID: str, creteria: json):
        self.session.query(Client).filter(Client.vkID == vkID).update({Client.creteria: creteria})
        self.session.commit()

    def get_client_by_vkID(self, vkID: str):
        return self.session.query(Client(vkID=str(vkID))).first()

    def put_search(self, ClientID: Client, SearchResults: list):
        # Удаляет предыдущий поиск из таблицы SearchResults для клиента
        # обнуляет
        client = self.session.query(Client).filter(Client.vkID == str(ClientID)).first()
        self.session.query(SearchResult).filter(
            SearchResult.clientID==client.id).delete()  # TODO нужно исключить имеющиеся завписи в Favorites
        for profile in SearchResults:
            item = SearchResult(ClientID=client.id,
                                    vkID=str(profile['id']),
                                    fio=f'{profile["first_name"]} {profile["last_name"]}',
                                    imgs=list(profile['photos'])
                                )
            self.session.add(item)
        self.session.commit()
        pass

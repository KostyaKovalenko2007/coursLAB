from db import Client,SearchResult,Favorite,BotDB

if __name__ == '__main__':
    bd = BotDB()
    bd.create_tables()

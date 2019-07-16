import stock
from pymongo import MongoClient

# to instantiate a mongodb docker
# docker run --name docker_mongodb -d -p 27017:27017 -v /Users/<username>/data:/data/db mongo

client = MongoClient(port=27017)
db = client.stock
names = stock.get_stock_name()

for name, sector in names.items():
    s = stock.Stock('THA', name, sector=sector, source='web')
    query = {'symbol':s.symbol, 'country':s.country}
    db.set.update_one(query, {'$set':s.__dict__}, upsert=True)
    print('stock {} sector {}: DONE'.format(name, sector))

client.close()

# print(stock.get_stock_detail('ADVANC'))
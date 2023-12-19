from motor import motor_asyncio
import pymongo
def add_admin(MONGO_URL):
    try:
        client=pymongo.MongoClient(MONGO_URL)
        wallet_collection=client.etherscan_database.wallet_collection
        user_collection=client.etherscan_database.user_collection
        admin=user_collection.find_one({"role":"admin"})
        if admin is None:
            user_collection.insert_one({"role":"admin","username":"scaraxo"})
            print("Channel admin was inserted to the database")
        client.close()
    except Exception as e:
        print(e)
        
async def is_paid_user(MONGO_URL,USERNAME):
    try:
        client=motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        user_collection=client.etherscan_database.user_collection
        user_document=await user_collection.find_one({"username":USERNAME})
        if user_document:
            return True
        else:
            return False
    except Exception as e:
        print(e)

def connect_db(MONGO_URL):
    try:
        client=motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        wallet_collection=client.etherscan_database.wallet_collection
        return wallet_collection
    except Exception as e:
        print(e)
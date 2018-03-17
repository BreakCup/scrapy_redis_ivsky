#coding=utf-8
import pymongo
import redis
import json

def process_item():
    redisCli=redis.StrictRedis(host='216.189.56.204',port=6379,db=0,password='breakcup')
    mongoCli=pymongo.MongoClient(host='localhost',port=27017)
    db_name=mongoCli["test"]
    table_list=db_name["list"]
    table_pic=db_name["pics"]
    i = 0
    while True:
        source, data = redisCli.blpop(["ivsky:items"])
        data = json.loads(data.decode("utf-8"))
        print(data)
        if data['UID'] < 5:
            if data['UID'] == 1:
                table_list.insert_one({
                    'PID': 0,
                    'UID':data['UID'],
                    'name':data['name'],
                    'url':data['url']
                })
            else:
                re = table_list.find({"name":data['preType']})
                for _data in re:
                    table_list.insert_one({
                        'PID':_data['_id'],
                        'UID':data['UID'],
                        'name':data['name'],
                        'url':data['url']
                    })
                if not re:
                    print("erro：找不到pid。")

        else:
            re = table_list.find({"name":data['preType']})
            for _data in re:
                table_list.insert_one({
                    'PID':_data['_id'],
                    'UID':data['UID'],
                    'name':data['name'],
                    'url':data['url'],
                    'referer':data['referer']
                })
            if not re:
                print("erro：找不到pid。")
        #table_name.insert(data)

if __name__=="__main__":
    process_item()
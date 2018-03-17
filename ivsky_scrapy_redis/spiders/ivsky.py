# -*- encoding: utf-8 -*-

###########################################
#           @breakcup
#           writed in 2018/3/13
#           version:0.0.4
##########################################



import scrapy
import scrapy_redis
from ivsky_scrapy_redis.items import IvskyScrapyRedisItem
from scrapy_redis.spiders import RedisSpider

UID_1 = 1
UID_2 = 2
UID_3 = 3
UID_4 = 4
UID_5 = 5
DEBUG = True
#parse爬取一&二级类型->保存item，for遍历url 并返回Request对象，回调三级菜单函数，爬取三级类型->保存item，
# for遍历url，并返回Request对象，回调图片组函数，爬取图片组->保存item，for遍历url并返回Request对象，回调图片函数，爬取图片信息，保存item

#一级类型：图片/壁纸
#二级类型：图片/壁纸下分类
#三级类型：小分类

class ivsky(RedisSpider):
    name = 'ivsky'

    baseUrl = 'http://www.ivsky.com'    
    #start_urls = [baseUrl]
    redis_key = 'ivsky:start_urls'

    #爬虫入口
    def parse(self,response):
        fatherTypes = self.getItem(response = response,level=UID_2)
        mainTypes = self.getItem(response = response,level=UID_1)

        if fatherTypes:
            if mainTypes:
                for mainType in mainTypes:
                    ivskyItem = IvskyScrapyRedisItem()
                    ivskyItem['name'] = mainType['name']
                    ivskyItem['url'] = mainType['url']
                    ivskyItem['UID'] = mainType['UID']
                    ivskyItem['preType'] = 'none'
                    ivskyItem['referer'] = mainType['referer']
                    yield ivskyItem
                #self.saveItem(mainTypes[0],'none')
                #self.saveItem(mainTypes[1],'none')
            #debug
            if DEBUG:
                print("### mainType1 / mainType2 ",mainTypes[0],mainTypes[1])
            
            ivskyItem2 = IvskyScrapyRedisItem()
            for i in range(len(fatherTypes)):
                name = fatherTypes[i]['name']
                url = fatherTypes[i]['url']
                UID = fatherTypes[i]['UID']

                #debug
                if DEBUG:
                    print("二级目录",UID,name,url)

                if i<18:
                    #self.saveItem(fatherTypes[i],mainTypes[0])
                    ivskyItem['preType'] = mainTypes[0]['name']
                else:
                    #self.saveItem(fatherTypes[i],mainTypes[1])
                    ivskyItem['preType'] = mainTypes[1]['name']
                ivskyItem['name'] = fatherTypes[i]['name']
                ivskyItem['url'] = fatherTypes[i]['url']
                ivskyItem['UID'] = fatherTypes[i]['UID']
                ivskyItem['referer'] = fatherTypes[i]['referer']
                yield ivskyItem
                yield scrapy.Request(url = url , callback=self.childType)
        else:
            pass

    #爬取小分类
    def childType(self,response):
        preType = self.getPreType(curUID = 3,response = response)
        types = self.getItem(response = response, level = UID_3)
        for sline in types:
            name = sline['name']
            url = sline['url']
            UID = sline['UID']

            #self.saveItem(sline,preType)
            ivskyItem = IvskyScrapyRedisItem()
            ivskyItem['name'] = sline['name']
            ivskyItem['url'] = sline['url']
            ivskyItem['UID'] = sline['UID']
            ivskyItem['preType'] = preType
            ivskyItem['referer'] = sline['referer']
            yield ivskyItem
            #debug
            if DEBUG:
                print("小分类:",UID,name,url,preType)

            yield scrapy.Request(url = url, callback=self.picsGroup)

    #爬取图片组
    def picsGroup(self,response):
        preType = self.getPreType(curUID = 4,response = response)
        picsGroups = self.getItem(response = response,level=UID_4)
        if picsGroups:
            for group in picsGroups:
                if DEBUG:
                    print('图片组',group)
                ivskyItem = IvskyScrapyRedisItem()
                ivskyItem['name'] = group['name']
                ivskyItem['url'] = group['url']
                ivskyItem['UID'] = group['UID']
                ivskyItem['preType'] = preType
                ivskyItem['referer'] = group['referer']
                yield ivskyItem
                #self.saveItem(group,preType)
                yield scrapy.Request(url = group['url'] , callback=self.handlePics)
        #获取下一页
        nextPage = self.getNextPage(response)
        if nextPage:
            #debug
            if DEBUG:
                print("下一页：",nextPage)
            yield scrapy.Request(url = nextPage , callback=self.parse)
        else:
            #debug
            if DEBUG:
                print("SPIDER STOPED")

    #处理组内图片
    def handlePics(self,response):
        urls = response.xpath('//ul[@class="pli"]/li/div/a/@href').extract()
        if DEBUG:
            print('图片组内图片',urls)
        if urls:      
            for url in urls:
                _url = self.baseUrl + url
                yield scrapy.Request(url = _url, callback=self.savePics)

    #获取图片下载地址
    def savePics(self,response):
        if DEBUG:
                print('处理图片函数')
        items = self.getItem(response,UID_5)
        preType = self.getPreType(response,UID_5)
        if items:
            if DEBUG:
                print('图片地址',items)
            for item in items:
                #self.saveItem(item,preType)
                ivskyItem = IvskyScrapyRedisItem()
                ivskyItem['name'] = item['name']
                ivskyItem['url'] = item['url']
                ivskyItem['UID'] = item['UID']
                ivskyItem['preType'] = preType
                ivskyItem['referer'] = item['referer']
                yield ivskyItem



    #获取上一级类型
    #根据当前深度的不同特征获取上一级类型
    #UID =  2 / 3 /4
    #当前深度必须在2
    def getPreType(self,response,curUID):
        #if curUID == 1:
        #    return 'none'
        if curUID == UID_2:
            re = response.xpath('//div[@class="pos"]/a[2]/text()').extract()
            if re:
                return re[0]
            else:
                return False
        if curUID == UID_3:
            re = response.xpath('//div[@class="sort"]/ul/li[contains(@class,"on")]/a/text()').extract()
            if re:
                return re[0]
            else:
                return False
        if curUID == UID_4:
            re = response.xpath('//div[@class="sline"]/div/a[contains(@class,"tag_on")]/text()').extract()
            if re:
                return re[0]
            else:
                return False
        if curUID == UID_5:
            re = response.xpath('//div[@id="al_tit"]/h1/text()').re('(.*?) ')
            if re:
                return re[0]
            else:
                return False

        return False

    #获取层级类型(目录)
    def getItem(self,response,level):
        items = []
        #一级
        if level==UID_1:
            names =  response.xpath('//ul[@class="kw_tit"]/li/text()').extract()
            urls = response.xpath('//div[@class="kw"]/a/@href').extract()
            if names and urls:
                items.append({
                    'name':names[0],
                    'url':self.baseUrl + urls[0],
                    'UID':UID_1,
                    'referer':'none'
                })
                items.append({
                    'name':names[1],
                    'url':self.baseUrl + urls[19],
                    'UID':UID_1,
                    'referer':'none'
                })
        #二级
        if level==UID_2:
            kws = response.xpath('//div[@class="kw"]/a')
            for i in range(1,len(kws)):
                name = kws[i].xpath('text()').extract()[0]
                href = kws[i].xpath('@href').extract()[0]
                if i!=19:
                    items.append({
                        'name':name,
                        'url':self.baseUrl + href,
                        'UID':UID_2,
                        'referer':'none'
                    })
        #三级
        if level==UID_3:
            slines = response.xpath('//div[@class="sline"]/div/a')
            if slines:
                for sline in slines:
                    items.append({
                        'name':sline.xpath('text()').extract()[0],
                        'url':self.baseUrl + sline.xpath('@href').extract()[0],
                        'UID':UID_3,
                        'referer':'none'
                    })
            pass
        #四级
        if level==UID_4:
            picsGroups = response.xpath('//ul[@class="pli"]/li/div/a')
            if picsGroups:
                for picsGroup in picsGroups:
                    name = picsGroup.xpath('@title').re('(.*?) ')[0]
                    url = self.baseUrl + picsGroup.xpath('@href').re('(.*)/')[0]
                    if items:
                        if items[-1]['name'] != name:
                            items.append({
                                'name':name,
                                'url':url,
                                'UID':UID_4,
                                'referer':'none'
                            })
                    else:
                        items.append({
                            'name':name,
                            'url':url,
                            'UID':UID_4,
                            'referer':'none'
                        })
        #五级（图片）
        if level==UID_5:
            #图片地址
            url =  response.xpath('/*').re('<script.*?imgURL=\'(.*?)\'.*?</script>')
            #图片名字
            name = response.xpath('//div[@id="al_tit"]/h1/text()').extract()
            #referer
            referer = response.url
            if url and name:
                url = self.baseUrl + url[0]
                name = name[0]
                items.append({
                    'name':name,
                    'url':url,
                    'UID':UID_5,
                    'referer':referer
                })
        return items

    #获取下一页
    def getNextPage(self,response):
        page = response.xpath('//div[@class="pagelist"]/a[@class="page-next"]/@href').extract()
        if page:
            return self.baseUrl + page[0]
        else:
            return False
    
    #保存项目
    def saveItem(self,item,preType):
        ivskyItem = IvskyScrapyRedisItem()
        #debug
        if DEBUG:
            print('###item',item,preType)
        ivskyItem['name'] = item['name']
        ivskyItem['url'] = item['url']
        ivskyItem['UID'] = item['UID']
        ivskyItem['preType'] = preType
        ivskyItem['referer'] = item['referer']
        yield ivskyItem

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from pymongo import MongoClient


class InstaPipeline:
    def __init__(self):
        client = MongoClient()
        self.db = client["Instagram"]

    def process_item(self, item, spider):
        self.db[spider.tag].insert_one(item)
        return item

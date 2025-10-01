from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
import time 
import json


es = Elasticsearch('http://localhost:9200')
index_name = "news"



# 문서 삽입 실행
# - 지정된 ID로 문서 저장
es.indices.create(index=index_name, body={
    "mappings": {
        "properties": {
            "title":     { "type": "text" },     #// 검색 대상
            "content":   { "type": "text" },     #// 검색 대상
            "writer":    { "type": "text" },     #// 검색 대상
            "category":  { "type": "keyword" },  #// 필터링용
            "url":       {"type": "text"},       # 중복 확인이나 보여주기 용도
            "keywords":  { "type": "keyword" },  #// 필터/정렬용
            "write_date":{ "type": "date" },      #// 정렬 및 기간 필터
            "updated_at":{ "type": "date" }     # 생성시기
        }
    },

    "settings":{
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "korean_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer"
                }
            }
        }
    }

})
print("생성완료")
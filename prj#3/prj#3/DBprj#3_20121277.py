# -*- coding: utf-8 -*-
from __future__ import division
import datetime
import time
import sys
import MeCab
import operator
from pymongo import MongoClient
from bson import ObjectId
from itertools import combinations
import re
from collections import Counter
import math


def printMenu():
    print "< M E N U >"
    print "1. WordCount"
    print "2. TF-IDF"
    print "3. Similarity"
    print "4. MorpAnalysis"
    print "5. CopyData"


# In this project, we assume a word seperated by a space is a morpheme.
stop_word = dict()
def MorphAnalysis(docs, col_tfidf, init_flag):
    # Step(1) Read Stopword list from file anamed stopword_list.txt
    if init_flag == 1:
        with open("stopword_list.txt", "r") as f:
            while True:
                line = f.readline()
                if not line: break
                stop_word[line.strip('\n')] = line.strip('\n')

    # Step(2) Analysis Morpheme in given text and delete stopword
    for doc in docs:
        content = doc['text']

        # Delete non-alphabetical characters
        content = re.sub('[^a-zA-Z]', ' ', content)

        # Change all capital letter to small letter
        content = content.lower().split()

        # delete stopword in a given text dataset
        MorpList = []
        for arg in content:
            if arg not in stop_word:
                MorpList.append(arg)
        MorpList = list(set(MorpList))  # 중복 제거

        # Step(3) Store processed morpheme data into MongoDB
        col_tfidf.update({'_id': doc['_id']}, {'$set': {'morph': MorpList}}, True)


def WordCount(docs, col_tfidf):
    for doc in docs:
        content = doc['text']
        pats = doc['morph']

        word_count = dict()
        for pat in pats:
            # re.I option : 대소문자 구별이 없도록 찾는다.
            word_count[pat] = len(re.findall(pat, content, re.I))

        # Store processed data into MongoDB
        col_tfidf.update({'_id': doc['_id']}, {'$set': {'word_count': word_count}}, True)


IDFs = dict()
def TfIdf(docs, col_tfidf, init_flag):
    NUM_OF_DOCS = make_doc_nums(col_tfidf)
    D = docs.count()

    if init_flag == 1:
        for word in NUM_OF_DOCS.keys():
            IDFs[word] = math.log(D / NUM_OF_DOCS[word])

    for doc in docs:
        tf_idf = dict()

        # get sum of word count in a doc
        tot = 0
        for word in doc['word_count'].keys():
            tot += doc['word_count'][word]

        # get tf_idf in a doc
        for word in doc['word_count'].keys():
            tf_idf[word] = (doc['word_count'][word] / tot) * IDFs[word]

        # Store processed data into MongoDB
        col_tfidf.update({'_id': doc['_id']}, {'$set': {'tf_idf': tf_idf}}, True)


# TO-DO in project
def Similarity(docs, col_tfidf):
    id_input1 = str(raw_input("Insert 1st Object ID: "))
    id_input2 = str(raw_input("Insert 2nd Object ID: "))

    # 사용자가 입력한 id 2개가 모두 유효할 때, 함수가 정상작동 할 수 있다.
    # cnt는 유효한 id 입력이 들어올 때마다 하나씩 증가한다.
    cnt = 0
    for doc in docs:
        if str(doc["_id"]) == id_input1:
            morph1 = doc['morph']
            tfidf1 = doc['tf_idf']
            cnt += 1
        elif str(doc["_id"]) == id_input2:
            morph2 = doc['morph']
            tfidf2 = doc['tf_idf']
            cnt += 1
        if cnt == 2:
            break
    else:
        print("Please check obj id!")
        return

    # 두개의 morph set을 합집합하여, 벡터의 차원을 생성
    set1 = set(morph1)
    set2 = set(morph2)
    union_words = list(set1 | set2)

    # make 2 word vectors
    vec1 = list()
    vec2 = list()
    for word in union_words:
        if word in morph1:
            vec1.append(tfidf1[word])
        else:
            vec1.append(0)

        if word in morph2:
            vec2.append(tfidf2[word])
        else:
            vec2.append(0)

    # calculate cosine similarity
    cosine_similarity = get_product(vec1, vec2) / (get_norm(vec1) * get_norm(vec2))
    print("Cosine Similarity of two docs is")
    print(cosine_similarity)
    print("")


def copyData(docs, col_tfidf):
    col_tfidf.drop()
    for doc in docs:
        contentDic = dict()
        for key in doc.keys():
            if key != "_id":
                contentDic[key] = doc[key]
        col_tfidf.insert(contentDic)


# make doc num list by Counter class
def make_doc_nums(col_tfidf):
    docs = col_tfidf.find()
    dfs = Counter()
    for doc in docs:
        cnt = Counter()
        for pat in doc['morph']:
            cnt[pat] = 1  # 1개의 doc에 pat이 여러개 있더라도 doc당 1개만 count한다.
        dfs.update(cnt)
    return dict(dfs)


# 벡터의 내적을 계산
def get_product(vec1, vec2):
    if len(vec1) != len(vec2):
        print("Vector dimensions do not match!")
        return
    return sum(x * y for x, y in zip(vec1, vec2))


# 벡터의 norm을 계산
def get_norm(vec):
    def square(x):
        return x ** 2

    return math.sqrt(sum(map(square, vec)))


# Access MongoDB
conn = MongoClient('localhost')

# fill it with your DB name - db+studentID ex) db20120121
db = conn['db20121277']

# fill it with your MongoDB( db + Student ID) ID and Password(default : 1234)
db.authenticate('db20121277', 'db20121277')

col = db['tweet']
col_tfidf = db['tweet_tfidf']

if __name__ == "__main__":
    # initialize
    print("Initializing... please wait...")
    docs = col_tfidf.find()
    MorphAnalysis(docs, col_tfidf, 1)
    WordCount(docs, col_tfidf)
    TfIdf(docs, col_tfidf, 1)

    printMenu()
    try:
        selector = input()
    except:
        selector = 0

    if selector == 1:
        docs = col_tfidf.find()
        print("WordCount")
        WordCount(docs, col_tfidf)

        # print word_count for input id
        docs = col_tfidf.find()
        id_input = str(raw_input("Insert Object ID: "))
        for doc in docs:
            if str(doc["_id"]) == id_input:
                print(doc['word_count'])
                break
        else:
            print("There's no such an id!")

    elif selector == 2:
        docs = col_tfidf.find()
        print("TF-IDF")
        TfIdf(docs, col_tfidf, 0)

        # print tf_idf for input id
        docs = col_tfidf.find()
        id_input = str(raw_input("Insert Object ID: "))
        for doc in docs:
            if str(doc["_id"]) == id_input:
                print(doc['tf_idf'])
                break
        else:
            print("There's no such an id!")

    elif selector == 3:
        docs = col_tfidf.find()
        print("Similiarity")
        Similarity(docs, col_tfidf)

    elif selector == 4:
        docs = col_tfidf.find()
        print("MorpAnalysis")
        MorphAnalysis(docs, col_tfidf, 0)

        # print morphemes for input id
        docs = col_tfidf.find()
        id_input = str(raw_input("Insert Object ID: "))
        for doc in docs:
            if str(doc["_id"]) == id_input:
                print(doc['morph'])
                break
        else:
            print("There's no such an id!")

    elif selector == 5:
        print("CopyData")
        docs = col.find()
        copyData(docs, col_tfidf)

    else:
        print("You must enter one of the numbers from 1 to 5.")

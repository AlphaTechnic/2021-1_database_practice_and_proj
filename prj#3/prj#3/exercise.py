# -*- coding: utf-8 -*-
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
    print "1. WordCount"
    print "2. TF-IDF"
    print "3. Similarity"
    print "4. MorpAnalysis"
    print "5. CopyData"


# In this project, we assume a word seperated by a space is a morpheme.
def MorphAnalysis(docs, col_tfidf):
    # TO-DO in open lab

    print("MorpAnalysis")

    # Step(1) Read Stopword list from file anamed stopword_list.txt
    stop_word = dict()

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

        # Step(3) Store processed morpheme data into MongoDB
        col_tfidf.update({'_id': doc['_id']}, {'$set': {'morph': MorpList}}, True)


def WordCount(docs, col_tfidf):
    print("WordCount")

    for doc in docs:
        content = doc['text']
        pats = doc['morph']

        word_count = dict()
        for pat in pats:
            word_count[pat] = len(re.findall(pat, content, re.I))

        # Step(3) Store processed morpheme data into MongoDB
        col_tfidf.update({'_id': doc['_id']}, {'$set': {'word_count': word_count}}, True)


# TO-DO in project

def TfIdf(docs, col_tfidf):
    print("TF-IDF")
    dfs = get_df(col_tfidf)
    NUM = docs.count()

    IDFs = dict()
    for ind, word in enumerate(dfs.keys()):
        IDFs[word] = math.log(NUM / dfs[word])

    for doc in docs:
        tf_idf = dict()

        for word in doc['word_count'].keys():
            idf = IDFs[word]
            tf_idf[word] = doc['word_count'][word] * idf

        # Step(3) Store processed morpheme data into MongoDB
        col_tfidf.update({'_id': doc['_id']}, {'$set': {'tf_idf': tf_idf}}, True)


# TO-DO in project

def Similarity(docs, col_tfidf):
    print("Similiarity")
    id_input1 = str(raw_input("Insert 1st Object ID: "))
    id_input2 = str(raw_input("Insert 2nd Object ID: "))

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

    set1 = set(morph1)
    set2 = set(morph2)
    union_words = list(set1 | set2)

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

    cosine_similarity = get_product(vec1, vec2) / (get_length(vec1) * get_length(vec2))
    print("Cosine Similarity of two docs is")
    print(cosine_similarity)
    print("")


# TO-DO in project

def copyData(docs, col_tfidf):
    col_tfidf.drop()
    for doc in docs:
        contentDic = dict()
        for key in doc.keys():
            if key != "_id":
                contentDic[key] = doc[key]
        col_tfidf.insert(contentDic)


# TO-Do in open lab
def get_df(col_tfidf):
    docs = col_tfidf.find()
    dfs = Counter()
    for doc in docs:
        cnt = Counter()
        for pat in doc['morph']:
            cnt[pat] = 1
            dfs.update(cnt)
    return dict(dfs)


def get_product(vec1, vec2):
    if len(vec1) != len(vec2):
        print("Vector dimensions do not match!")
        return
    return sum(x * y for x, y in zip(vec1, vec2))


def get_length(vec):
    def square(x):
        return x ** 2

    return math.sqrt(sum(map(square, vec)))


# Access MongoDB
conn = MongoClient('localhost')

# fill it with your DB name - db+studentID ex) db20120121
db = conn['db20121277']

# fill it with your MongoDB( db + Student ID) ID and Password(default : 1234)
db.authenticate('db20121277', 'nea05200@')

col = db['tweet']
col_tfidf = db['tweet_tfidf']

if __name__ == "__main__":
    printMenu()
    selector = input()

    if selector == 1:
        docs = col_tfidf.find()
        WordCount(docs, col_tfidf)

        # print word_count
        docs = col_tfidf.find()
        id_input = str(raw_input("Insert Object ID: "))
        for doc in docs:
            if str(doc["_id"]) == id_input:
                print(doc['word_count'])
                break
        else:
            print("There's no such id!")

    elif selector == 2:
        docs = col_tfidf.find()
        TfIdf(docs, col_tfidf)

        # print tf_idf
        docs = col_tfidf.find()
        id_input = str(raw_input("Insert Object ID: "))
        for doc in docs:
            if str(doc["_id"]) == id_input:
                print(doc['tf_idf'])
                break
        else:
            print("There's no such id!")

    elif selector == 3:
        docs = col_tfidf.find()
        Similarity(docs, col_tfidf)

    elif selector == 4:
        docs = col_tfidf.find()
        MorphAnalysis(docs, col_tfidf)

        # print morphemes
        docs = col_tfidf.find()
        id_input = str(raw_input("Insert Object ID: "))
        for doc in docs:
            if str(doc["_id"]) == id_input:
                print(doc['morph'])
                break
        else:
            print("There's no such id!")

    elif selector == 5:
        docs = col.find()
        copyData(docs, col_tfidf)

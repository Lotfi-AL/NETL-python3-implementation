"""
Author:         Shraey Bhatia
Date:           October 2016
File:           candidate_gen.py

This file generates label candidates and save the output in a file. It uses both
doc2vec and word2vec models and normalise them to unit vector. There are a couple of
pickle files namely doc2vec_indices and word2vec_indices  which restrict the search of
word2vec and doc2vec labels. These pickle files are in support_files.
"""

import os
import gensim
import pandas as pd
from gensim.models import Doc2Vec
from gensim.models import Word2Vec
import math
from collections import defaultdict
from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL,\
    double, uint32, seterr, array, uint8, vstack, fromstring, sqrt, newaxis,\
ndarray, empty, sum as np_sum, prod, ones, ascontiguousarray
from gensim import utils,matutils
import re
import pickle
import multiprocessing as mp
from multiprocessing import Pool
import argparse
import numpy as np
# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("num_cand_labels")
parser.add_argument("doc2vecmodel")
parser.add_argument("word2vecmodel")
parser.add_argument("data")
parser.add_argument("outputfile_candidates")
parser.add_argument("doc2vec_indices")
parser.add_argument("word2vec_indices")
args = parser.parse_args()

"""
Pickle file needed to run the code. These file have the indices of doc2vec which 
have length of label(wiki title less than 5). The word2vec file has indices of the
file which were used in to create phrases in word2vec model. The indices are taken from 
trained doc2vec and word2vec models. Additionally there is some bit of preprocessing involved 
of removing brackets from some candidate labels. To get more insight into it refer to the paper.
"""

with open(args.doc2vec_indices,'rb') as m:   
    d_indices=pickle.load(m)
with open(args.word2vec_indices,'rb') as n:
    w_indices =pickle.load(n)

# Models loaded
model1 =Doc2Vec.load(args.doc2vecmodel)
model2 = Word2Vec.load(args.word2vecmodel)
print("models loaded")

# Loading the data file
topics = pd.read_csv(args.data)
try:
    new_frame= topics.drop('domain',1)
    topic_list = new_frame.set_index('topic_id').T.to_dict('list')
except:
    topic_list = topics.set_index('topic_id').T.to_dict('list')
print("Data Gathered")


print(len(d_indices))
w_indices = list(set(w_indices))
d_indices = list(set(d_indices))


# Models normalised in unit vectord from the indices given above in pickle files.
#model1.vectors_norm = model1.dv.get_normed_vectors()
#model1.dv.vectors_norm = model1.dv.get_normed_vectors()[d_indices]
print(model1.dv.index_to_key[0])
print(dir(model1.dv))
#print(model1.dv.similar_by_key("busser"))
#print(model1.dv.vectors)

print("doc2vec normalized")


#model2_vectors_norm = model2.get_normed_vectors()
#model3 = model2_vectors_norm[w_indices]
print("word2vec normalized")

# This method is mainly used to remove brackets from the candidate labels.

def get_word(word):
    if type(word)!=str:
        return word
    inst = re.search(r"_\(([A-Za-z0-9_]+)\)", word)
    if inst == None:
        return word
    else:
        word = re.sub(r'_\(.+\)','',word)
        return word

def get_labels(topic_num):
    valdoc2vec =0.0
    valword2vec =0.0
    cnt = 0
    store_indices =[]
    
    print("Processing Topic number " +str(topic_num))
    for item in topic_list[topic_num]:
        print(topic_num,item)
        try:
            tempdoc2vec = model1.dv.get_vector(item) # The word2vec value of topic word from doc2vec trained model
        except:
            print("passed")
            pass
        else:
            print("nani")
            meandoc2vec = matutils.unitvec(tempdoc2vec).astype(REAL)    # Getting the unit vector
            distsdoc2vec = dot(model1.dv.get_normed_vectors(), meandoc2vec) # The dot product of all labels in doc2vec with the unit vector of topic word
            valdoc2vec = valdoc2vec + distsdoc2vec
        try:
            tempword2vec = model2.wv.get_vector(item)#model2.getmodel2.syn0norm[model2.vocab[item].index]  # The word2vec value of topic word from word2vec trained model
        except:
            pass
        else:
            meanword2vec = matutils.unitvec(tempword2vec).astype(REAL) # Unit vector
            distsword2vec = dot(model2.wv.get_normed_vectors(), meanword2vec) # The dot prodiuct of all possible labels in word2vec vocab with the unit vector of topic word
            """
            This next section of code checks if the topic word is also a potential label in trained word2vec model. If that is the case, it is 
            important the dot product of label with that topic word is not taken into account.Hence we make that zero and further down the code
            also exclude it in taking average of that label over all topic words. 

            """
              
            if (model2.wv.key_to_index[item]) in w_indices:
                
                i_val = w_indices.index(model2.wv.key_to_index[item])
                store_indices.append(i_val)
                distsword2vec[i_val] =0.0
            valword2vec = valword2vec + distsword2vec
    
    avgdoc2vec = valdoc2vec/float(len(topic_list[topic_num])) # Give the average vector over all topic words
    avgword2vec = valword2vec/float(len(topic_list[topic_num])) # Average of word2vec vector over all topic words
    
    bestdoc2vec = matutils.argsort(avgdoc2vec, topn = 100, reverse=True) # argsort and get top 100 doc2vec label indices
    resultdoc2vec =[]
    # Get the doc2vec labels from indices
    for elem in bestdoc2vec:

        ind = d_indices[elem]
        print(elem,ind)
        print(ind,"index")
        temp = model1.dv.index_to_key[elem]
        #temp = model1.docvecs.index_to_doctag(ind)
        print(temp,ind,elem)
        resultdoc2vec.append((temp,float(avgdoc2vec[elem])))
   
    # This modifies the average word2vec vector for cases in which the word2vec label was same as topic word.
    for element in store_indices:
        avgword2vec[element] = (avgword2vec[element]*len(topic_list[topic_num]))/(float(len(topic_list[topic_num])-1))
    bestword2vec = matutils.argsort(avgword2vec,topn=100, reverse=True) #argsort and get top 100 word2vec label indices
    # Get the word2vec labels from indices
    resultword2vec = []
    for element in bestword2vec:
        if element > len(w_indices):
            continue
        ind = w_indices[element]
        print(ind,element)
        temp = model2.wv.index_to_key[element]
        print(temp,ind,element)
        resultword2vec.append((temp,float(avgword2vec[element])))
    
    # Get the combined set of both doc2vec labels and word2vec labels
    comb_labels = list(set([i[0] for i in resultdoc2vec]+[i[0] for i in resultword2vec]))
    newlist_doc2vec = []
    newlist_word2vec = []
    print("lets go")
    # Get indices from combined labels
    print(comb_labels,"comb_labels")
    for elem in comb_labels:
        try:
            print(elem)
            #newlist_doc2vec.append(d_indices.index(model1.docvecs.doctags[elem].offset))
            newlist_doc2vec.append(model1.dv.key_to_index[elem])
            print("noo")
            temp = get_word(elem)
            #newlist_word2vec.append(w_indices.index(model2.vocab[temp].index))
            newlist_word2vec.append(model2.wv.key_to_index[temp])
        except:
            print("failure pass")
            pass

    newlist_doc2vec = list(set(newlist_doc2vec))
    newlist_word2vec = list(set(newlist_word2vec))
    print(newlist_doc2vec,"newlistdoc2vec")
    print(newlist_word2vec,"newlistword2vec")
    # Finally again get the labels from indices. We searched for the score from both doctvec and word2vec models
    resultlist_doc2vecnew =[(model1.dv.index_to_key[elem],float(avgdoc2vec[elem])) for elem in newlist_doc2vec]
    resultlist_word2vecnew =[(model2.wv.index_to_key[elem],float(avgword2vec[elem])) for elem in newlist_word2vec]
    print(resultlist_word2vecnew,resultlist_doc2vecnew)
    # Finally get the combined score with the label. The label used will be of doc2vec not of word2vec. 
    new_score = []
    for item in resultlist_word2vecnew:
        print(item)
        k, v = item
        for elem in resultlist_doc2vecnew:
            k2,v2 = elem
            k3 = get_word(k2)
            if k==k3:
                v3 = v+v2
                new_score.append((k2,v3))
    new_score = sorted(new_score,key =lambda x:x[1], reverse =True)
    print("yolo")
    print(new_score)
    print(new_score[:(int(args.num_cand_labels))])
    return new_score[:(int(args.num_cand_labels))]

cores = mp.cpu_count()
#pool = mp.Pool(processes=cores)
#result = pool.map(get_labels, range(0,len(topic_list)))
result = []

for i in range(len(topic_list)):
    result.append(get_labels(i))

# The output file for candidates.
g = open(args.outputfile_candidates,'w')
for i, elem in enumerate(result):
    val = ""
    for item in elem:
        val = val + " "+item[0]
    g.write(val+"\n")
g.close()

print("Candidate labels written to "+args.outputfile_candidates)
print("\n")

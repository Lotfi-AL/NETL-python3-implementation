"""
Author:         Shraey Bhatia
Date:           October 2016
File:           doc2vectrain.py

Gives a trained document vectors model (also known as Doc2VecModel). 
The input format are documents extrated using wiki extractor and tokenized using stanford tokenizer stored in a directory
Output would be a trained doc2vec model.
Parameters taken for main_train.py
"""

import os
import re
import sys
import gensim
import argparse
import codecs
import unicodedata
import multiprocessing
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec
import logging

#These are the arguments that are passed in main_train.py
parser = argparse.ArgumentParser()
parser.add_argument("epochs")  # Number of training epochs
parser.add_argument("input_dir")
parser.add_argument("output_dir")
args = parser.parse_args()

# Checks if the output directory specified already exists. If it does remove it.

if os.path.isdir(args.output_dir):
    del_query = "rm -r " + args.output_dir
    os.system(del_query)

# Create an output directory for the model
query = "mkdir " + args.output_dir
os.system(query)

output = args.output_dir + "/doc2vecmodel.d2v"


# Doc2vec Input documents Class. It uses yield to optimize memory usage and "tag" is Document title with an undescore.
class LabeledLineSentence(object):
    def __init__(self, sources):
        self.sources = sources
    
    def __iter__(self):
        
        for source in self.sources:
            with codecs.open(source, "r", "utf-8") as fin:
                for cnt, line in enumerate(fin):
                    if "<doc" in line:  # Every new document starts with this format
                        found = ""
                        
                        m = re.search('title="(.*)">', line)  # This gives the document title of Wikipedia
                        if m:
                            found = m.group(1)
                            found = found.lower()
                            found = unicodedata.normalize("NFKD", found)
                            found = found.replace(" ", "_")
                            #found = found.encode('utf-8')
                        
                        else:
                            found = ""
                        values = []
                    else:
                        if "</doc" not in line:  # </doc tells us end of document, till not reached it is same document
                            for word in line.split(" "):
                                values.append(word.strip())
                        if "</doc" in line:
                            if found != "":
                                yield TaggedDocument(words=values, tags=[found])


cores = multiprocessing.cpu_count()
filenames = []

# Get all tokenised files in directory and subdirectories ( tokenised by stanford parser)
for path, subdirs, files in os.walk(args.input_dir):
    for name in files:
        temp = os.path.join(path, name)
        filenames.append(temp)
sentences = LabeledLineSentence(filenames[0:1])
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Doc2Vec model initialization and parameters
model = Doc2Vec(window=15, min_count=20, sample=1e-5, workers=cores, hs=0, dm=0, negative=5, dbow_words=1,
                dm_concat=0)
print(sentences)
model.build_vocab(sentences)

model.train(corpus_iterable=sentences,total_examples=model.corpus_count,epochs=int(args.epochs))
# Model Training
#for epoch in range(int(args.epochs)):
#    model.train(total_examples=model.corpus_count,corpus_iterable=sentences)
#    print("Epoch completed: " + str(epoch + 1))

print(model.dv.index_to_key[0])
model.save(output)

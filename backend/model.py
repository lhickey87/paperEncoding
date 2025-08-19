
import tensorflow_hub as hub
import tensorflow as tf


module_url = "https://tfhub.dev/google/universal-sentence-encoder/4" #@param ["https://tfhub.dev/google/universal-sentence-encoder/4", "https://tfhub.dev/google/universal-sentence-encoder-large/5"]
model = hub.load(module_url)
print ("module %s loaded" % module_url)


def embed(input):
  return model(input)

def toVector(vec):
   return vec.numpy().tolist()

def compute_similarity_score(vec1: list, vec2: list):
    total = 0
    for i in range(0,512):
       total += vec1[i]*vec2[i] 
    return total 
    

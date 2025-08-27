
import tensorflow_hub as hub
import tensorflow as tf
import numpy as np

module_url = "https://tfhub.dev/google/universal-sentence-encoder/4" #@param ["https://tfhub.dev/google/universal-sentence-encoder/4", "https://tfhub.dev/google/universal-sentence-encoder-large/5"]
model = hub.load(module_url)
print ("module %s loaded" % module_url)


def embed(input):
  return model(input)

def toVector(vec):
   return vec.numpy().tolist()

def compute_similarity_score(vec1: list, vec2: list):
    dot = np.dot(vec1,vec2)
    mag1 = np.dot(vec1,vec1)
    mag2 = np.dot(vec2,vec2)
    return dot/(mag1*mag2)
    

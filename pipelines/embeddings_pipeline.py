import apache_beam as beam
import json
import logging
from model import embed, toVector



class embeddingsPipeline(beam.dofn):




    def process(self, json_string):

        #NEED MODEL LOGIC

        try:
            data = json.loads(json_string)
            
        
        except Exception as e:
            logging.error(f"Json string was not properly processed: {e}")
            return
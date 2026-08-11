import json
import joblib 
import pandas as pd
from functioning import create_embedding



def processing_file(file_name):
    chunks_id = 0
    my_dict = []
    with open(file_name, 'r') as f:
        contents = json.load(f)


    for item in contents:
        embedding = create_embedding(item['normalized_embedding_text'])
        chunk_record = item.copy()
        chunk_record['chunks_id'] = chunks_id
        chunk_record['embedding'] = embedding
        chunks_id += 1

        my_dict.append(chunk_record)    
    # print(chunk_record)

    df = pd.DataFrame.from_records(my_dict)

    joblib.dump(df, 'embedding.joblib')
        






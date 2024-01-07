import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.freebase_func import *
from utils import *
from tqdm import tqdm

def run(input_file):
    data = readjson_50(input_file)
    all_golden_triple_len = 0
    all_predict_triple_len = 0
    for lines in tqdm(data):
        golden_sparql, relation_path_candidates, topic_entity = lines['sparql'], lines['relation_path_candidates'], lines['topic_entity']

        # get number of golden relations
        triples = [splt for splt in golden_sparql.split("\n") if "PREFIX" not in splt and "SELECT" not in splt and "WHERE" not in splt and "{" not in splt and "}" not in splt and "FILTER" not in splt and "ORDER" not in splt and "LIMIT" not in splt and len(splt)!=0]
        num_of_golden_triples = len(triples)

        # get number of predict relations
        num_of_predict_triples = 0
        for key, value in relation_path_candidates.items():
            num_of_predict_triples += (len(value[0].split("->")) - 1)

        lines['num_of_golden_triples'] = num_of_golden_triples
        lines['num_of_predict_triples'] = num_of_predict_triples

        all_golden_triple_len += num_of_golden_triples
        all_predict_triple_len += num_of_predict_triples


    print("avg golden triple len:", all_golden_triple_len/len(data))
    print("avg predict triple len:", all_predict_triple_len/len(data))
    savejson(input_file.split('.')[0]+"_data_ana.json", data)

input_file="/home/v-sitaocheng/demos/dangle_over_ground/data/initial_plan/cwq_gpt35_0105.json"
run(input_file)
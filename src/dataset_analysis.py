import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.freebase_func import *
from utils import readjson, savejson, jsonl_to_json, read_jsonl
from tqdm import tqdm


def efficiency_analysis(input_file):
    if input_file.endswith("json"):
        data = readjson(input_file)
    elif input_file.endswith("jsonl"):
        data = read_jsonl(input_file)

    all_refine_time = 0.0
    max_refine_time = 0
    all_path = 0
    call_time = dict()

    for index, line in enumerate(tqdm(data)):
        len_of_predict_knowledge_dict = line['len_of_predict_knowledge']
        all_path += len(len_of_predict_knowledge_dict.keys())
        for k, v in len_of_predict_knowledge_dict.items():
            call = len(v)-1
            max_refine_time = max(max_refine_time, call)
            all_refine_time += len(v)-1
            if len(v)-1 not in call_time.keys():
                call_time[call] = 1
            else:
                call_time[call] += 1
            

    print("average refine time : ", all_refine_time/all_path)
    print("max refine time : ", max_refine_time)
    print("distribution: ", call_time)

def reasoning_path_analysis(intput_file):
    if input_file.endswith("json"):
        data = readjson(input_file)
    elif input_file.endswith("jsonl"):
        data = read_jsonl(input_file)
    all_grounded = 0.0
    number_of_path = 0
    grounding_progress = 0.0
    len_of_predict_path = 0
    len_of_grounded_path = 0
    cvt_end = 0
    data=data[:1000]
    for lines in data:
        len_of_predict_knowledge, len_of_grounded_knowledge = lines['len_of_predict_knowledge'], lines['len_of_grounded_knowledge']
        number_of_path += len(len_of_predict_knowledge.keys())
        kg_paths = lines['kg_paths'].split("\n")
        for path in kg_paths:
            if path.split(" -> ")[-1].startswith("m."):
                cvt_end += 1
                break

        for k,v in len_of_predict_knowledge.items():
            grounding_progress += len_of_grounded_knowledge[k][-1] / v[-1]
            if len_of_grounded_knowledge[k][-1] == v[-1]:
                all_grounded += 1.0
                
            len_of_predict_path += v[-1]
            len_of_grounded_path += len_of_grounded_knowledge[k][-1]


    print("all grounded rate: ", all_grounded/number_of_path)
    print("avg grounded progress: ", grounding_progress/number_of_path)
    print("avg len of predict progress: ", len_of_predict_path/len(data))
    print("avg len of grounded progress: ", len_of_grounded_path/len(data))
    print("cvt ending rate: ", cvt_end/len(data))


def len_of_path(input_file):
    data = readjson(input_file)
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


    print("avg golden path len:", all_golden_triple_len/len(data))
    print("avg predict path len:", all_predict_triple_len/len(data))
    # savejson(input_file.split('.')[0]+"_data_ana.json", data)

def webqsp_statistics(input_file):
    data = readjson(input_file)
    number_multi_constrain = 0
    for line in data:
        if len(line['topic_entity'].keys())>1:
            number_multi_constrain+=1
    print("multi number: ", number_multi_constrain)
    print("total number: ", len(data))
    


# input_file="/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_campre_method___compare_rog_beam1_0114.jsonl"
# reasoning_path_analysis(input_file)

# input_file = "/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_llm_refine_sequence_err_msg_onePath_CVT_HardStop_oldengine_thought_0112.jsonl"
# efficiency_analysis(input_file)

input_path="/home/v-sitaocheng/demos/dangle_over_ground/data/datasets/WebQSP.json"
webqsp_statistics(input_path)
import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
# import utils
from utils.freebase_func import *
import json
# from rank_bm25 import BM25Okapi
from utils import *
import openai
import re
import time
from tqdm import tqdm
import argparse
import pickle
import string
from utils.cloudgpt_aoai_new import *
from utils.prompt_list import *


def read_jsonl_file_50(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line)
            data.append(json_obj)
    return data  

def readjson_50(file_name):
    with open(file_name, encoding='utf-8') as f:
        data=json.load(f)
    return data


def savejson(file_name, new_data):
    with open(file_name, mode='w',encoding='utf-8') as fp:
        json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)


def extract_variables_from_sparql_query(query):
    # 匹配以"?x"、"?y"等格式开头的字符串作为变量
    variable_pattern = r'\?[\w]+'
    variables = re.findall(variable_pattern, query)
    
    # 使用set()去除重复的变量，并将其连接为一个字符串
    distinct_variables = ' '.join(set(variables))

    query=query.replace(")?", ")\n?").replace("}?", "}\n?").replace(".?", ".\n?")
    query = re.sub(r'#.*?\n', '\n', query)

    # 在查询中添加 SELECT DISTINCT 子句来获取所有变量的结果
    splits = query.split("\n")
    for index, lines in enumerate(splits) :
        if "SELECT" in lines:
            splits[index] = f'SELECT DISTINCT {distinct_variables}'
        
        # if ";" in lines:
        #     if len(lines.split(" "))==4:
        #         lines = lines.replace(";", '.')
        #     elif len(lines.split(" ")) == 3 and index>=1:
        #         first_var = splits[index-1].split(" ")[0]
        #         splits[index] = (first_var + lines).replace(';', '.')

    # modified_query = query.replace("SELECT DISTINCT", "SELECT").replace('SELECT', f'SELECT DISTINCT {distinct_variables}')
    modified_query="\n".join(splits)
    return modified_query



def extract_query_knowledge(sparql_query, sparql_results):
    # triples = sparql_query.split("\n")
    triplets_matches = []
    for lines in sparql_query.split("\n"):
        if "PREFIX" in lines or "SELECT" in lines or "FILTER" in lines or "ORDER" in lines or "EXISTS" in lines or "?" not in lines:
            continue
        triplets_matches.append(lines.strip())
    # print(triplets_matches)

    # 解析查询结果，构建三元组知识
    knowledge = []
    for result in sparql_results:
        for triplet in triplets_matches:
            vars_in_triplet = re.findall(r'\?[\w]+', triplet)  # 提取三元组中的变量
            formatted_triplet = triplet
            # print(formatted_triplet)
            # print(vars_in_triplet)
            # print(result)
            # 替换三元组模式中的变量为结果值
            for var in vars_in_triplet:
                if var[1:] not in result.keys():
                    continue

                var_value = result[var[1:]]['value']
                # 如果变量值以'http'开头，则去掉前缀只保留'm.'开头的部分
                if var_value.startswith('http'):
                    var_value = var_value.split('/')[-1]
                    
                formatted_triplet = formatted_triplet.replace(var, var_value).strip()
                print(formatted_triplet)

            if formatted_triplet[-1]=='.':
                formatted_triplet=formatted_triplet[:-1].strip()

            # 添加知识
            knowledge.append(formatted_triplet.strip().replace('?', '').replace("ns:", "").split(" "))

    return knowledge

def get_golden_knowledge():
    cwq = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")
    for lines in tqdm(cwq):
        sparql = lines['sparql']
        modified_sparql = extract_variables_from_sparql_query(sparql)
        query_result = execurte_sparql(modified_sparql)
        lines['instantiated_knowledge'] = extract_query_knowledge(modified_sparql, query_result)

        savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json", cwq)


def instantiate_knowledge():
    cwq = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")
    for lines in tqdm(cwq):
        entity_label_map={}
        entity_set = set()
        knowledge = lines['instantiated_knowledge']
        for know in knowledge:
            entity_set.add(know[0])
            entity_set.add(know[2])

        num_UnName_Entity = 0
        for e in entity_set:
            # print(e)
            if e.startswith("m.") or e.startswith("g."):
                label = id2entity_name_or_type_en(e)
                if label == "UnName_Entity":
                    num_UnName_Entity += 1
                    # label = "intermediate_entity_" + str(num_UnName_Entity)
                    label = e
            else:
                label = e
            
            entity_label_map[e]=label

        triples=""
        for know in knowledge:
            seq_knowledge = "(" + entity_label_map[know[0].replace("ns:","")] + ", " + know[1].replace("ns:", "") + ", " + entity_label_map[know[2].replace("ns:", "")] + " )\n"
            if seq_knowledge in triples:
                continue
            triples += seq_knowledge
        
        triples.strip('\n')

        lines['golden_knowledge_enumerate'] = triples
        lines['entity_ids']=list(entity_set)    
        lines['entity_label_map']=entity_label_map
    
        savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1127.json", cwq)


def deal_egpsr_entity():
    egpsr=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_test_cwq_1113.json")
    for lines in tqdm(egpsr):
        subgraph = lines['subgraph']
        num_UnName_Entity = 0

        ent_id_label_map={}
        for e in subgraph['entities_ids']:
            # print(e)
            if e.startswith("m.") or e.startswith("g."):
                label = id2entity_name_or_type_en(e)
                if label == "UnName_Entity":
                    num_UnName_Entity += 1
                    # label = "intermediate_entity_" + str(num_UnName_Entity)
                    label = e
            else:
                label = e            
            ent_id_label_map[e]=label

        lines['subgraph']['ent_id_label_map'] = ent_id_label_map
    savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_test_cwq_1128.json", egpsr)


def calculate_contract_recall_natural_language():
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")
    all_recall=0
    non_zero_num=0
    all_knowledge_len=0

    for lines in tqdm(data):
        golden_knowledge_seq = lines['golden_knowledge_enumerate']
        contract_knowledge_seq = lines['knowledge_triples_egpsr_contract_top1']
        golden_knowledge_set = set()
        contract_knowledge_set = set()
        if len(golden_knowledge_seq)==0:
            continue

        for know in golden_knowledge_seq.strip().split('\n'):
            know = know.strip().replace(", ", ",")
            if know[0]=='(':
                know=know[1:]
            if know[-1]==')':
                know=know[:-1]
            know=know.strip()
            golden_knowledge_set.add(know)

        for know in contract_knowledge_seq.strip().split('\n'):
            know=know.strip().replace(", ", ",")
            if know[0]=='(':
                know=know[1:]
            if know[-1]==')':
                know=know[:-1]
            know=know.strip()
            contract_knowledge_set.add(know)
        recall=0

        for golden_know in golden_knowledge_set:
            if golden_know in contract_knowledge_set:
                recall+=1
        
        if len(golden_knowledge_set)==0:
            # all_recall+=1
            continue
        else:
            print(recall/len(golden_knowledge_set))
            all_recall += recall/len(golden_knowledge_set)
            non_zero_num += 1
            all_knowledge_len += len(golden_knowledge_set)
    
    print("golden knowledge avg recall",all_recall/non_zero_num)
    print("golden knowledge avg len: ", all_knowledge_len/non_zero_num)

def normalize(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""
    s = s.lower()
    exclude = set(string.punctuation)
    s = "".join(char for char in s if char not in exclude)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    # remove <pad> token:
    s = re.sub(r"\b(<pad>)\b", " ", s)
    s = " ".join(s.split())
    return s


def match(s1: str, s2: str) -> bool:
    s1 = normalize(s1)
    s2 = normalize(s2)
    return s2 in s1


def calculate_answer_coverage_rate():
    # sr_graph = read_jsonl_file_50("/home/v-sitaocheng/demos/llm_hallu/reasoning-on-graphs/results/gen_rule_path/RoG-cwq/RoG/test/predictions_kg.jsonl")
    # sr_graph = read_jsonl_file_50("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/RoG/test/_home_v-sitaocheng_demos_llm_hallu_reasoning-on-graphs_results_gen_rule_path_RoG-cwq_RoG_test_predictions_3_False_jsonl/predictions_kg_with_input_llm_cwq100_path_onePath_gpt35_1225_llm_stop.jsonl")
    sr_graph = read_jsonl_file_50("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/RoG/test/_home_v-sitaocheng_demos_llm_hallu_reasoning-on-graphs_results_gen_rule_path_RoG-cwq_RoG_test_predictions_3_False_jsonl/predictions_kg_with_input_llm_cwq100_path_onePath_gpt35_1226_llm_stop_longest_only_multi_merge.jsonl")
    # cwq = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1127.json")
    cwq = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/data/cwq.json")
    all_recall=0
    all_recall=0
    non_zero_num=0
    all_knowledge_len=0
    predict_knowledge_len=0
    all_knowledge_num = 0
    all_knowledge_one_path_num = 0

    for index, lines in enumerate(tqdm(sr_graph)):
        topic_entity = cwq[index]['topic_entity']
        num_of_path = len(topic_entity.keys())
        if num_of_path == 1:
            continue
        # print(topic_entity.values())
        all_knowledge_one_path_num += 1

        knowledge_seq = lines['kg_triples_str'].replace(", ",",").replace(" ,",",").strip()
        all_knowledge_num += len(knowledge_seq.split("\n"))
        answer_list = lines['ground_truth']

        recall=0
        for ans in answer_list:
            # if ","+ans.strip() in knowledge_seq or ans+"," in knowledge_seq:
            if match(knowledge_seq, ans):
                recall+=1
                print(lines['kg_triples_str'])
        if recall == 0:
            print(lines['question'])
            print(topic_entity)
            print(lines['kg_paths'])
            print(answer_list)
            print("********************************************************************************************************************")
       
        all_recall+=recall/len(answer_list)

    # print("coverage rate:" , all_recall/len(sr_graph))    
    print(all_knowledge_one_path_num)
    print("coverage rate one path:" , all_recall/all_knowledge_one_path_num)    
    # print("number of knowledge:" , all_knowledge_num/len(sr_graph))    
    print("number of knowledge:" , all_knowledge_num/all_knowledge_one_path_num)    


def calculate_graph_recall():
    sr_graph = readjson_50("/home/v-sitaocheng/demos/llm_hallu/reasoning-on-graphs/results/gen_rule_path/RoG-cwq/RoG/test/predictions_kg.json")
    cwq = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1127.json")

    all_recall=0
    non_zero_num=0
    all_knowledge_len=0
    predict_knowledge_len=0

    for index, lines in enumerate(tqdm(sr_graph)):
        contract_knowledge_seq = lines['kg_triples']
        golden_knowledge_seq = cwq[index]['golden_knowledge_enumerate']
        
        golden_knowledge_set = set()
        contract_knowledge_set = set()

        if len(golden_knowledge_seq)==0:
            continue

        for know in golden_knowledge_seq.strip().split('\n'):
            know = know.strip().replace(", ", ",").replace(" ,", ",").strip()
            if know[0]=='(':
                know=know[1:]
            if know[-1]==')':
                know=know[:-1]
            know = know.strip()
            golden_knowledge_set.add(know)

        if len(contract_knowledge_seq) != 0 :
            for know in contract_knowledge_seq.strip().split('\n'):
                know = know.strip().replace(", ", ",").replace(" ,", ",").strip()
                if know[0]=='(':
                    know=know[1:]
                if know[-1]==')':
                    know=know[:-1]
                know=know.strip()
                contract_knowledge_set.add(know)

        recall=0

        for golden_know in golden_knowledge_set:
            if golden_know in contract_knowledge_set:
                recall+=1
        
        if len(golden_knowledge_set)==0:
            # all_recall+=1
            continue
        else:
            print(recall/len(golden_knowledge_set))
            all_recall += recall/len(golden_knowledge_set)
            non_zero_num += 1
            all_knowledge_len += len(golden_knowledge_set)
    
    print("golden knowledge avg recall",all_recall/non_zero_num)
    print("golden knowledge avg len: ", all_knowledge_len/non_zero_num)
    # print("predict knowledge avg len:", predict_knowledge_len/100)


def calculate_recall_triple():
    sr_graph = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_test_cwq_top1_NSM_1115.json")
    cwq = readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")

    all_recall=0
    non_zero_num=0
    all_knowledge_len=0
    predict_knowledge_len=0
    for index, lines in enumerate(tqdm(sr_graph)):
        sub_graph_knowledge = lines['subgraph']['knowledges']
        golden_knowledge = cwq[index]['instantiated_knowledge']
        golden_knowledge_set = []
        predict_knowledge_set = []
        
        for lines in golden_knowledge:
            if lines in golden_knowledge_set:
                continue
            golden_knowledge_set.append(lines)

        for lines in sub_graph_knowledge:
            if lines in predict_knowledge_set:
                continue
            predict_knowledge_set.append(lines)

        predict_knowledge_len+=len(predict_knowledge_set)
        recall=0
        for golden_know in golden_knowledge_set:
            if golden_know in sub_graph_knowledge:
                recall+=1
        
        if len(golden_knowledge_set)==0:
            # all_recall+=1
            continue
        else:
            all_recall += recall/len(golden_knowledge_set)
            non_zero_num += 1
            all_knowledge_len += len(golden_knowledge_set)
        
    # print(all_recall/len(sr_graph))
    print("golden knowledge avg recall",all_recall/non_zero_num)
    print("golden knowledge avg len: ",all_knowledge_len/non_zero_num)
    print("predict knowledge avg len:", predict_knowledge_len/100)


if __name__ == '__main__':
    # run()
    # deal_egpsr_entity()
    # get_golden_knowledge()
    # instantiate_knowledge()
    # calculate_contract_recall()
    # calculate_graph_recall()

    calculate_answer_coverage_rate()
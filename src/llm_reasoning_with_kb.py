import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.freebase_func import *
from utils.prompt_list import *
import json
from rank_bm25 import BM25Okapi
from sentence_transformers import util
from sentence_transformers import SentenceTransformer
from utils.cloudgpt_aoai import get_openai_token
import openai
import re
import time
from tqdm import tqdm
import argparse
import pickle
import os

def run_llm(prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-35-turbo-20230613"):
    if "llama" not in engine.lower():
        # openai.api_key = "EMPTY"
        # openai.api_base = "http://localhost:8000/v1"  # your local llama server port
        # engine = openai.Model.list()["data"][0]["id"]
        
        openai.api_type = "azure"
        openai.api_base = "https://cloudgpt-openai.azure-api.net/"
        openai.api_version = "2023-07-01-preview"
        openai.api_key = get_openai_token()
    else:
        openai.api_key = opeani_api_keys
        openai.api_key = get_openai_token()

    messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}]
    # rules放在这里  Q: K: A:

    message_prompt = {"role":"user","content":prompt}
    messages.append(message_prompt)
    # print("start openai")
    f = 0
    result = ""
    while(f <= 5):
        try:
            response = openai.ChatCompletion.create(
                    engine=engine,
                    messages = messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    frequency_penalty=0,
                    presence_penalty=0)
            result = response["choices"][0]['message']['content']
            f = 10
        except:
            print("openai error, retry")
            f += 1
            messages[-1] = {"role":"user","content": prompt[:16384]}
            print(len(messages[1]["content"]))
            time.sleep(2)
    # print("end openai")
    return result

def generate_answer(question, cluster_chain_of_entities, args): 
    prompt = answer_prompt + question + '\n'
    chain_prompt = '\n'.join([', '.join([str(x) for x in chain]) for sublist in cluster_chain_of_entities for chain in sublist])
    prompt += "\nKnowledge Triplets: " + chain_prompt + 'A: '
    result = run_llm(prompt, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
    return result


def read_jsonl_file_50(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # print(line)
            json_obj = json.loads(line)
            data.append(json_obj)
    return data[:100]  

def readjson_50(file_name):
    with open(file_name, encoding='utf-8') as f:
        data=json.load(f)[:100]
    return data


def savejson(file_name, new_data):
    with open(file_name, mode='w',encoding='utf-8') as fp:
        json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)


def trim_sparql():
    with open("/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/data/cwq/data/cwq/cwq_dev.json", encoding='utf-8') as f:
        data=json.load(f)
    
    new_data=[]
    for data_items in tqdm(data):
        sparql = data_items['sparql']
        answer = data_items['answers'][0]['answer']
        new_sparql_lines = []

        data_items['topic_entity'] = {}
        for l in data_items['topics']:
            data_items['topic_entity'][l['uri'].replace("http://rdf.freebase.com/ns/","")] = l['label'][0]

        entity_label_map = data_items['topic_entity']
        lines = sparql.split('\n')

        for l in lines:
            if "FILTER (?x != ns:" in l or "FILTER (!isLiteral(?" in l or "PREFIX" in l:
                continue
            new_sparql_lines.append(l)
        print(entity_label_map)
        new_sparql="\n".join(new_sparql_lines)
        for key in entity_label_map.keys():
            new_sparql=new_sparql.replace("ns:"+key, entity_label_map[key])

        data_items['trimed_sparql']=new_sparql
    
        new_data.append({"question":data_items['question'], "results": answer, "sparql": sparql, 'trimed_sparql': new_sparql})

    savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/trimed_dev_{}.json".format('cwq'), new_data)
    # with open("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/trimed_test_{}.jsonl".format('cwq'), mode='w',encoding='utf-8') as fp:
    #     json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)



def get_knowledge_triple_golden():
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/trimed_test_cwq.json")
    # with open("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/trimed_test_cwq.jsonl", encoding='utf-8') as f:
    #     data=json.load(f)
    new_data=[]
    for lines in tqdm(data):
        prompt=kb_extract_prompt+"Sparql: "+lines['trimed_sparql'] + "\nAnswer: " + lines['results'] + "\nKnowledge Triplets:"
        response =  run_llm(prompt, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
        lines['knowledge_triple']=response
        new_data.append(lines)
        savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/kb_golden_test_{}_1112.json".format('cwq'), new_data)
        # with open("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/kb_golden_test_{}.jsonl".format('cwq'), mode='w',encoding='utf-8') as fp:
        #     json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)


def save_2_jsonl(question, answer, cluster_chain_of_entities, file_name, file_index):
    dict = {"question":question, "results": answer, "reasoning_chains": cluster_chain_of_entities}
    if not os.path.exists("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/reasoning_predict/"+file_index):
        os.makedirs("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/reasoning_predict/"+file_index)
    with open("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/reasoning_predict/"+file_index+"/kb_egpsr_predict_test_{}.jsonl".format(file_name), "a") as outfile:
        json_str = json.dumps(dict)
        outfile.write(json_str + "\n")


def reasoning_with_golden(file_index):
    print("reasoning_with_egpsr  file: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json", " field  knowledge_triple")

    # data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")
    for lines in tqdm(data):
        prompts = answer_prompt_kb_interwined + "Q: " + lines['question'] + "\nKnowledge Triplets: " + lines['golden_knowledge_enumerate'] + "\nA: "
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
        if len(response)==0 or len(lines['golden_knowledge_enumerate'])==0:
            prompts = cot_prompt + "\n\nQ: " + lines['question'] + "\nA: "
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            lines['golden_knowledge_enumerate'] = "COT"

        save_2_jsonl(lines['question'], response, lines['golden_knowledge_enumerate'], 'cwq_golden_1123_'+file_index)


def reasoning_with_egpsr(file_index):
    print("reasoning_with_egpsr  file: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json", " field knowledge_triples_ppr_top1")
    # data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    for lines in tqdm(data):
        prompts = answer_prompt_kb_interwined + "Q: " + lines['question'] + "\nKnowledge Triplets: " + lines['knowledge_triples_egpsr_top1_nointer'] + "\nA: "
        # prompts = answer_prompt_kb_interwined_q_first + "Knowledge Triplets: " + lines['knowledge_triples_egpsr_top1'] + "\nQ: " + lines['question']  + "\nA: "
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)

        if len(response)==0 or len(lines['knowledge_triples_egpsr_top1_nointer'])==0:
            prompts = cot_prompt + "\n\nQ: " + lines['question'] + "\nA: "
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            lines['knowledge_triples_egpsr_top1_nointer'] = "COT"

        save_2_jsonl(lines['question'], response, lines['knowledge_triples_egpsr_top1_nointer'], 'egpsr_cwq_top1_nointer'+file_index)
    

def reasoning_with_egpsr_contract(file_index):
    print("reasoning_with_egpsr_contract  file: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json", " field  knowledge_triples_ppr_contract_top1")
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    # data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")
    for lines in tqdm(data):
        prompts = answer_prompt_kb_interwined_nointer + "Q: " + lines['question'] + "\nKnowledge Triplets: " + lines['knowledge_triples_egpsr_contract_top1_nointer_reasoning'] + "\nA: "
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)

        if len(response)==0 or len(lines['knowledge_triples_egpsr_contract_top1_nointer_reasoning'])==0:
            prompts = cot_prompt + "\n\nQ: " + lines['question'] + "\nA: "
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            lines['knowledge_triples_egpsr_contract_top1_nointer_reasoning'] = "COT"

        save_2_jsonl(lines['question'], response, lines['knowledge_triples_egpsr_contract_top1_nointer_reasoning'], 'egpsr_contract_cwq_100sample_top1_nointer_reasoning'+file_index, file_index)
  


def reasoning_with_ROG(file_name, file_index):
    print("reasoning with ROG  file: ", file_name)
    # data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    reasoning_result=[]
    data=readjson_50(file_name)
    for lines in tqdm(data):
        prompts = answer_prompt_kb_interwined + "Q: " + lines['question'] + "\nKnowledge Triplets: " + lines['kg_triples_str'] + "\nA: "
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)

        if len(response)==0 or len(lines['kg_triples_str'])==0:
            prompts = cot_prompt + "\n\nQ: " + lines['question'] + "\nA: "
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            lines['kg_triples_str'] = "COT"
        reasoning_result.append({"question":lines['question'], "results": response, "reasoning_chains": lines['kg_triples_str']})

        savejson('/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/QA_result/ROG_cwq_top1_100examples'+file_index, reasoning_result)
        # save_2_jsonl(lines['question'], response, lines['kg_triples_str'], 'ROG_cwq_top1_'+file_index)
    


def extract_egprs_graph(file_index):
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1112.json")
    # entities=readlines("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/cwq_subgraph/entities.txt")
    # relations=readlines("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/cwq_subgraph/relations.txt")
    # test_simple=read_jsonl_file_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/cwq_subgraph/test_simple.jsonl")
    
    subgraph_file_name = "/home/v-sitaocheng/demos/llm_hallu/subgraph_retrieval/sr_cwq/SubgraphRetrievalKBQA/tmp/CWQ_NSM/"
    subgraph_file_name = "/home/v-sitaocheng/demos/llm_hallu/subgraph_retrieval/sr_cwq/SubgraphRetrievalKBQA/debug/cwq_retrieved_graph_cache/data/cwq/SubgraphRetrievalKBQA/src/tmp/reader_data/CWQ/"

    entities=readlines(subgraph_file_name+"entities.txt")
    relations=readlines(subgraph_file_name+"relations.txt")
    test_simple=read_jsonl_file_50(subgraph_file_name+"test_simple.json")
    # test_simple=readjson_50("/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/data/cwq/data/cwq/CWQ_test_top100_lp_top1_ep_instantiated_subg.json")

    with open('/home/v-sitaocheng/demos/llm_hallu/subgraph_retrieval/sr_cwq/SubgraphRetrievalKBQA/debug/ent2id.pickle', 'rb') as file:
        entity_id2index = pickle.load(file)
    entity_index2id={}
    for key in entity_id2index.keys():
        entity_index2id[entity_id2index[key]] = key

    print("extract_egprs_graph filename", subgraph_file_name+"test_simple.jsonl", "\n\ngolden: ","/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1112.json\n")
    for index, lines in tqdm(enumerate(data)):
        # subgraph=test_simple[index]['subg']
        subgraph=test_simple[index]['subgraph']
        ent=subgraph['entities']
        tup=subgraph['tuples']
        # new_entity_set_id = [entities[i] for i in ent]
        new_entity_set_id = [entity_index2id[i] for i in ent]
        # new_entity_set_id = [i.replace("ns:", "") for i in test_simple[index]["node_cgs"].keys()]
        new_entity_label_map = {}
        
        num_UnName_Entity = 0
        for e in new_entity_set_id:
            # print(e)
            if e.startswith("m.") or e.startswith("g."):
                label = id2entity_name_or_type_en(e)
                if label == "UnName_Entity":
                    num_UnName_Entity += 1
                    label = "intermediate_entity_" + str(num_UnName_Entity)
            else:
                label = e

            new_entity_label_map[e]=label

        knowledges=[]

        for t in tup:
            # knowledges.append([entities[t[0]], relations[t[1]], entities[t[2]]])
            knowledges.append([entity_index2id[t[0]], t[1], entity_index2id[t[2]]])

        # for t in subgraph:
            # knowledges.append(t.split(" "))

        lines['subgraph'] = {"entities_ids": new_entity_set_id, "ent_id_label_map": new_entity_label_map, "knowledges": knowledges}

    print("save extract_egprs_graph to ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/SR/kb_SR_test_cwq_top1_SR_"+file_index+".json")
    savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/SR/kb_SR_test_cwq_top1_SR_"+file_index+".json", data)


def build_knowledge_triple_egpsr(file_index):
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1127.json")
    # data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_dev_cwq_1112.json")
    # epgsr=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_test_cwq_top1_NSM_"+file_index+".json")
    epgsr=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_test_cwq_1128.json")
    print("build_knowledge_triple_egpsr filename: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/SR/kb_SR_test_cwq_top1_SR_"+file_index+".json", "\ngolden: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1112.json\n")
    for index, lines in enumerate(tqdm(data)):
        subgraph=epgsr[index]['subgraph']
        triples=""
        ent_label_map=subgraph['ent_id_label_map']
        for know in subgraph['knowledges']:
            triples += "(" + ent_label_map[know[0].replace("ns:","")] + ", " + know[1].replace("ns:", "") + ", " + ent_label_map[know[2].replace("ns:", "")] + ")\n"
        
        triples.strip('\n')
        lines['knowledge_triples_egpsr_top1_nointer'] = triples
    print("save to ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json", data)
    # savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_dev_cwq_1112.json", data)


def egpsr_contract(file_index):
    print("egpsr_contract filename: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    epgsr=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1129.json")
    # epgsr=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_dev_cwq_1112.json")
    for lines in tqdm(epgsr):
        # prompts = kb_contract_prompt_dev + "Question: " + lines['question'] + "\nKnowledge Triplets: " + lines['knowledge_triples_egpsr_top1'] + "\nRelevant Triples: "
        # prompts = kb_contract_prompt_dev_internal + "Question: " + lines['question'] + "\nKnowledge Triplets: " + lines['knowledge_triples_egpsr_top1_nointer'] + "\nRelevant Triples: "
        prompts = kb_contract_prompt_dev_internal_reasoning_1129 + "Question: " + lines['question'] + "\nKnowledge Triplets: " + lines['knowledge_triples_egpsr_top1_nointer'] + "\nReasoning:"
        del lines['knowledge_triples_ppr_top1']
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)

        if len(response) == 0 or len(lines['knowledge_triples_egpsr_top1_nointer'])==0:
            lines['knowledge_egpsr_contract_reasoning'] = ""
            lines['knowledge_triples_egpsr_contract_top1_nointer_reasoning'] = lines['knowledge_triples_egpsr_top1_nointer']
        else:
            lines['knowledge_egpsr_contract_reasoning'] = response
            # lines['knowledge_triples_egpsr_contract_top1_nointer'] = response
            lines['knowledge_triples_egpsr_contract_top1_nointer_reasoning'] = response.split("Refined Knowledge:")[-1].strip()
    
    print("save egpsr_contract to: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")
    savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json", epgsr)
    # savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_dev_cwq_1112.json", epgsr)




def rog_contract(input_file):
    print("Reasoning filename: ", input_file)
    epgsr=read_jsonl_file_50(input_file)
    # epgsr=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_dev_cwq_1112.json")
    for lines in tqdm(epgsr):
        # prompts = kb_contract_prompt_dev + "Question: " + lines['question'] + "\nKnowledge Triplets: " + lines['knowledge_triples_egpsr_top1'] + "\nRelevant Triples: "
        prompts = kb_contract_prompt_dev_internal + "Question: " + lines['question'] + "\nKnowledge Triplets: " + lines['kg_triples_str'] + "\nRelevant Triples: "
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
        if len(response) == 0:
            lines['kg_triples_contract'] = lines['kg_triples_str']
        else:
            lines['kg_triples_contract'] = response
    
    print("save ROG contract to: ", input_file.split(".")[0]+"_contracted.json")
    savejson(input_file.split(".")[0]+"_contracted.json", epgsr)
    # savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/egpsr/kb_egpsr_dev_cwq_1112.json", epgsr)
 


def trim_cwq_ToG():
    data = []
    with open("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/ToG_cwq.jsonl", 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line)
            data.append(json_obj)
    questions=[]
    for lines in data:
        if lines['question'] in questions:
            continue
        questions.append(lines['question'])

        save_2_jsonl(lines['question'], lines['results'], lines['reasoning_chains'], 'tog_cwq_trimed')


def calculate_avg_kb(file_index):
    print("calculate_avg_kb filename: ", "/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_"+file_index+".json")

    data=readjson_50('/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_'+file_index+'.json')
    golden_kb_len = 0
    egpsr_kb_len = 0
    egpsr_contract_kb_len = 0
    non_zero = 0
    for lines in tqdm(data):
        knowledge_triple_golden = lines['knowledge_triple'].strip("\n")

        knowledge_triples_egpsr = lines['knowledge_triples_egpsr_top1'].strip("\n")
        # if lines['knowledge_triples_SR_top1'] == lines['knowledge_triples_SR_contract_top1']:
        #     continue
        knowledge_triples_egpsr_contract = lines['knowledge_triples_SR_contract_top1_internal'].strip("\n")
        # non_zero+=1

        golden_len=len(knowledge_triple_golden.split('\n'))
        egpsr_len=len(knowledge_triples_egpsr.split('\n'))
        egpsr_contract_len=len(knowledge_triples_egpsr_contract.split('\n'))
        golden_kb_len += golden_len
        egpsr_kb_len += egpsr_len
        egpsr_contract_kb_len += egpsr_contract_len
    
    print("golden avg knowledge: ", golden_kb_len/len(data))
    print("egpsr avg knowledge: ", egpsr_kb_len/len(data))
    print("egpsr contract avg knowledge: ", egpsr_contract_kb_len/len(data))
    # print("egpsr contract avg knowledge: ", egpsr_contract_kb_len/non_zero)


def calculate_avg_kb_egpse():
    data=read_jsonl_file_50("/home/v-sitaocheng/demos/llm_hallu/reasoning-on-graphs/results/gen_rule_path/RoG-cwq/RoG/test/predictions_kg.jsonl")
    
    egpsr_kb_len = 0
    for lines in tqdm(data):
        if len(lines['kg_triples']) == 0:
            continue
        egpsr_kb_len += len(lines['kg_triples'].split("\n"))
    
    print("egpsr avg knowledge: ", egpsr_kb_len/len(data))



def calculate_avg_kb_tog():
    data=read_jsonl_file_50('/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/ToG_test_50_cwq.jsonl')
    golden_kb_len = 0
    total_len = 0
    for lines in tqdm(data):
        knowledge_triple_golden = lines['reasoning_chains']
        if len(knowledge_triple_golden) > 0:
            golden_kb_len += len(knowledge_triple_golden[0])
            total_len += 1

    print("tog avg knowledge: ", golden_kb_len/total_len)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="cwq", help="choose the dataset.")
    parser.add_argument("--max_length", type=int,
                        default=256, help="the max length of LLMs output.")
    parser.add_argument("--temperature_exploration", type=float,
                        default=0, help="the temperature in exploration stage.")
    parser.add_argument("--temperature_reasoning", type=float,
                        default=0, help="the temperature in reasoning stage.")
    parser.add_argument("--width", type=int,
                        default=3, help="choose the search width of ToG.")
    parser.add_argument("--depth", type=int,
                        default=3, help="choose the search depth of ToG.")
    parser.add_argument("--remove_unnecessary_rel", type=bool,
                        default=True, help="whether removing unnecessary relations.")
    parser.add_argument("--LLM_type", type=str,
                        default="gpt-35-turbo-16k-20230613", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=str,
                        default="", help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    parser.add_argument("--num_retain_entity", type=int,
                        default=5, help="Number of entities retained during entities search.")
    parser.add_argument("--prune_tools", type=str,
                        default="llm", help="prune tools for ToG, can be llm (same as LLM_type), bm25 or sentencebert.")
    args = parser.parse_args()

    file_index="1225"

    # 用golden知识来reasoning
    # golden
    # 从logical form提取golden知识
    # trim_sparql()
    # get_knowledge_triple_golden()
    # reasoning_with_golden(file_index)

    # # # epgsr
    # extract_egprs_graph(file_index)
    # build_knowledge_triple_egpsr(file_index)
    # reasoning_with_egpsr(file_index)

    # # # contract
    # egpsr_contract(file_index)
    # reasoning_with_egpsr_contract(file_index)

    # ROG知识推理模块
    # 知识压缩 存在kg_triples_contract字段
    rog_contract(input_file='/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/RoG/test/_home_v-sitaocheng_demos_llm_hallu_reasoning-on-graphs_results_gen_rule_path_RoG-cwq_RoG_test_predictions_3_False_jsonl/predictions_kg_with_input_llm_cwq100_path_onePath_gpt4_1223.jsonl')
    # 答案推理 可以改相应的prompt和对应的字段
    reasoning_with_ROG('/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/RoG/test/_home_v-sitaocheng_demos_llm_hallu_reasoning-on-graphs_results_gen_rule_path_RoG-cwq_RoG_test_predictions_3_False_jsonl/predictions_kg_with_input_llm_cwq100_path_onePath_gpt4_1223.jsonl', file_index)

    # analyse    
    # trim_cwq_ToG()
    # calculate_avg_kb(file_index)
    # calculate_avg_kb_egpse()
    # calculate_avg_kb_tog()
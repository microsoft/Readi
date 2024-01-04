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
import numpy as np
from pyserini.search import FaissSearcher, LuceneSearcher
from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import AutoQueryEncoder
import pandas as pd
import json
from utils import *
from config import *
import Levenshtein


def most_similar_string(input_str, string_list):
    similarity_scores = [(s, Levenshtein.distance(input_str.lower(), s.lower())) for s in string_list]
    similarity_scores.sort(key=lambda x: x[1])
    return similarity_scores[0][0]


def reasoning(file_index):
    data=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/golden/kb_golden_test_cwq_1115.json")
    for lines in tqdm(data):
        prompts = answer_prompt_kb_interwined + "Q: " + lines['question'] + "\nKnowledge Triplets: " + lines['golden_knowledge_enumerate'] + "\nA: "
        response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
        if len(response)==0 or len(lines['golden_knowledge_enumerate'])==0:
            prompts = cot_prompt + "\n\nQ: " + lines['question'] + "\nA: "
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            lines['golden_knowledge_enumerate'] = "COT"

        save_2_jsonl(lines['question'], response, lines['golden_knowledge_enumerate'], 'cwq_golden_1123_'+file_index)



def get_relation_path(input_file="data/datasets/cwq_test.json", output_file="data/initial_plan/cwq_test_1221.json"):

    cwq=readjson_50(input_file)[:100]
    for index, item in enumerate(tqdm(cwq)):
        topic_ent = [v for k,v in item['topic_entity'].items()]
        prompts = relation_reasoning_prompt_new  + "Question: " + item['question'] + "\nTopic Entities:" + str(topic_ent)+ "\nThought:"
        while True:
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            try:
                cwq[index]['relation_path_candidates'] = eval(response.split("Path:")[-1].strip())
                break
            except:
                print("**********************************************************************************")
                print(prompts)
                print(response)
                time.sleep(10)
                print("**********************************************************************************")
                # cwq[index]['relation_path_candidates']= response

        savejson(output_file, cwq)


def dump():
    cwq=readjson_50("data/datasets/cwq_test.json")
    for lines in cwq:
        for key in lines['relation_path_candidates']['relation_paths'].keys():
            lines['relation_path_candidates']['relation_paths'][key] = list(set(lines['relation_path_candidates']['relation_paths'][key]))

    savejson("data/datasets/cwq_test_new.json", cwq)


def grounding_relations():
    cwq=readjson_50("data/datasets/cwq_test.json")
    query_encoder = AutoQueryEncoder(encoder_dir='facebook/contriever', pooling='mean')
    corpus = LuceneSearcher('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/KB-BINDER/contriever_fb_relation/index_relation_fb')
    bm25_searcher = LuceneSearcher('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/KB-BINDER/contriever_fb_relation/index_relation_fb')
    contriever_searcher = FaissSearcher('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/KB-BINDER/contriever_fb_relation/freebase_contriever_index', query_encoder)

    hsearcher = HybridSearcher(contriever_searcher, bm25_searcher)

    for index, items in tqdm(enumerate(cwq)):
        relation_path_candidates = items['relation_path_candidates']
        question = items['question']
        cwq[index]['relation_path_candidates']['grounded_relations'] = {}
        cwq[index]['relation_path_candidates']['grounded_relations_no_q'] = {}

        for key in relation_path_candidates['topic_entities']:
            for relations in relation_path_candidates['relation_paths'][key]:
                for rel in relations:
                    if rel in cwq[index]['relation_path_candidates']['grounded_relations'].keys():
                        continue

                    result= []
                    relation_tokens = rel.replace("."," ").replace("_", " ").strip() + " "+ question
                    hits = hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:10]
                    for hit in hits:
                        result.append(json.loads(corpus.doc(str(hit.docid)).raw())['rel_ori'])


                    result_no_q= []
                    relation_tokens = rel.replace("."," ").replace("_", " ").strip()
                    hits = hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:10]
                    for hit in hits:
                        result_no_q.append(json.loads(corpus.doc(str(hit.docid)).raw())['rel_ori'])


                    cwq[index]['relation_path_candidates']['grounded_relations'][rel] = result
                    cwq[index]['relation_path_candidates']['grounded_relations_no_q'][rel] = result_no_q

        savejson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/candidate_rel/cwq_test_new_top10.json", cwq)


def run():
    cwq_origin=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/data/cwq.json")
    cwq=readjson_50("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/candidate_rel/cwq_test_new.json")
    one_hop_relations = readjson_50('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/data/pred_conn_fb.jsonl')
    for index, items in tqdm(enumerate(cwq)):
        topic_entity_dict = cwq_origin[index]
        paths=[]
        predict_topic_entity_labels_list = items['relation_path_candidates']['topic_entities']
        predict_relation_paths_dict = items['relation_path_candidates']['relation_paths']
        grounded_relations_dict = items['grounded_relations']
        for entity in topic_entity_dict.keys():
            current_path = "" + entity
            ent_rel_one_hop = get_ent_one_hop_rel(entity_id=entity, pre_relations=[], pre_head=-1)
            golden_ent_label = topic_entity_dict[entity]
            source_entity = most_similar_string(golden_ent_label, predict_topic_entity_labels_list)
            cur_path_list = predict_relation_paths_dict[source_entity]

            one_hop_connected = []
            # for rel in ent_rel_one_hop:
                # if rel not in grounding_relations[]
                # one_hop_connected.append()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, choices=DATASET.keys(), default="cwq", help="choose the dataset.")
    parser.add_argument("--max_length", type=int, default=4096, help="the max length of LLMs output.")
    parser.add_argument("--temperature_exploration", type=float, default=0.4, help="the temperature in exploration stage.")
    parser.add_argument("--temperature_reasoning", type=float, default=0.4, help="the temperature in reasoning stage.")
    parser.add_argument("--width", type=int, default=3, help="choose the search width of ToG.")
    parser.add_argument("--depth", type=int, default=3, help="choose the search depth of ToG.")
    parser.add_argument("--remove_unnecessary_rel", type=bool, default=True, help="whether removing unnecessary relations.")
    parser.add_argument("--llm", type=str,choices=LLM_BASE.keys(), default="gpt4", help="base LLM model.")
                        # default="gpt-35-turbo-16k-20230613", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=str, default="", help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    parser.add_argument("--num_retain_entity", type=int, default=5, help="Number of entities retained during entities search.")
    parser.add_argument("--prune_tools", type=str, default="llm", help="prune tools for ToG, can be llm (same as LLM_type), bm25 or sentencebert.")
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]

    input_file = os.path.join(DATASET_BASE, DATASET[args.dataset])
    output_file = os.path.join(INIT_PLAN_BASE,f"{args.dataset}_{args.llm}_{get_timestamp()}.json")
    get_relation_path(input_file=input_file, output_file=output_file)
    # grounding_relations()
    # run()
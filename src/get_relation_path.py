import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.freebase_func import *
from utils.prompt_list import *
from utils.utils import readjson
from pyserini.search import FaissSearcher, LuceneSearcher
from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import AutoQueryEncoder
import time
from tqdm import tqdm
import argparse
import os
from utils import *
from config import *


def dump():
    cwq=readjson("data/datasets/cwq_test.json")
    for lines in cwq:
        for key in lines['relation_path_candidates']['relation_paths'].keys():
            lines['relation_path_candidates']['relation_paths'][key] = list(set(lines['relation_path_candidates']['relation_paths'][key]))

    savejson("data/datasets/cwq_test_new.json", cwq)


def grounding_relations():
    cwq=readjson("data/datasets/cwq_test.json")
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
    cwq_origin=readjson("/home/v-sitaocheng/demos/llm_hallu/ToG/data/cwq.json")
    cwq=readjson("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/candidate_rel/cwq_test_new.json")
    one_hop_relations = readjson('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/data/pred_conn_fb.jsonl')
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


def get_relation_path(input_file, output_file):

    items=readjson(input_file)[:100]
    for index, item in enumerate(tqdm(items)):
        topic_ent = [v for k,v in item['topic_entity'].items()]
        if topic_ent == []:
            print(f"{index} topic entity is empty, item: {item}")
            continue

        question_str = get_question_string(args.dataset)
        prompts = relation_reasoning_prompt_new  + "Question: " + item[question_str] + "\nTopic Entities:" + str(topic_ent)+ "\nThought:"

        default_relation_path = {
            k: [k]
            for k in topic_ent
        }
        item['relation_path_candidates'] = default_relation_path
        MAX_RETRY_TIME = 5
        for _ in range(MAX_RETRY_TIME):
            response = run_llm(prompts, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
            try:
                item['relation_path_candidates'] = eval(response.split("Path:")[-1].strip())
                break
            except:
                error_line = "*" * 20
                print(response)
                time.sleep(1)
                print(error_line)


        savejson(output_file, items)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default=CWQ, help="Dataset alias or prefix")
    parser.add_argument("--max_length", type=int, default=4096, help="the max length of LLMs output.")
    parser.add_argument("--temperature_reasoning", type=float, default=0.3, help="the temperature in reasoning stage.")
    parser.add_argument("--width", type=int, default=3, help="choose the search width of ToG.")
    parser.add_argument("--depth", type=int, default=3, help="choose the search depth of ToG.")
    parser.add_argument("--remove_unnecessary_rel", type=bool, default=True, help="whether removing unnecessary relations.")
    parser.add_argument("--llm", type=str,choices=LLM_BASE.keys(), default="gpt35", help="base LLM model.")
                        # default="gpt-35-turbo-16k-20230613", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=str, default="", help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    parser.add_argument("--num_retain_entity", type=int, default=5, help="Number of entities retained during entities search.")
    parser.add_argument("--prune_tools", type=str, default="llm", help="prune tools for ToG, can be llm (same as LLM_type), bm25 or sentencebert.")
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]

    input_file = get_dataset_file(args.dataset)
    output_file = os.path.join(INIT_PLAN_BASE,f"{args.dataset}_{args.llm}_{get_timestamp()}.json")

    print("save result to: ",output_file)
    get_relation_path(input_file=input_file, output_file=output_file)
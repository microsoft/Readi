from typing import *
from glob import glob
import os

DATASET_BASE = "data/datasets"
CONTRIEVER_PATH = "data/"
# RESULT_PATH = "results/KGQA"
OUTPUT_FILE_PATH = "results/"
MAX_LLM_RETRY_TIME = 5
MAX_REFINE_TIME = 5

CWQ = 'cwq'
WEBQSP = 'WebQSP'

DATASET = {
    CWQ: "cwq_test_origin_with_topic_alias.json",
    WEBQSP: "webqsp_simple_test.jsonl",
}

def get_dataset_file(dataset: str) -> str:
    if dataset in DATASET.keys():
        return os.path.join(DATASET_BASE, DATASET[dataset])
    cand_file = glob(os.path.join(DATASET_BASE, f"{dataset}*"))
    if(len(cand_file) != 0):
        return cand_file[0]
    raise FileNotFoundError(f"Dataset {dataset} is not a valid registered alias or prefix")

LLM_BASE = {
    'gpt35': "gpt-3.5-turbo",
    'gpt4': "gpt-4-turbo",
    'gpt4-8k': "gpt-4-0613",
    'gpt4-o': "gpt-4o",
}

QUESTION_STRING = {
    CWQ: 'question',
    WEBQSP: 'Question',
}

def get_question_string(dataset: str) -> str:
    if dataset in QUESTION_STRING.keys():
        return QUESTION_STRING[dataset]
    for cand_dataset in QUESTION_STRING.keys():
            return QUESTION_STRING[cand_dataset]
    raise KeyError(f"Dataset {dataset} has not been configured quesition string yet.")


def get_topic_entity_list(item, input_file):
    if 'webqsp' in input_file.lower():
        topic_ent = [item['TopicEntityName']]
    else:
        topic_ent = [v for k,v in item['topic_entity'].items()]
    return topic_ent

def get_topic_entity_dict(item, input_file):
    if 'webqsp' in input_file.lower():
        entities = {item['TopicEntityID']: item['TopicEntityName']}
    else:
        entities = item['topic_entity']
    return entities

def get_ground_truth(item, dataset_name):
    answer_list= []
    if dataset_name.startswith(CWQ):
        if 'answers' in item:
            answers = item["answers"]
        else:
            answers = item["answer"]

        if type(answers) == str:
            answer_list.append(answers)
        else:
            for answer in answers:
                if type(answer) == str:
                    alias=[answer]
                else:
                    alias = answer['label']

                answer_list.extend(alias)

    elif dataset_name.startswith(WEBQSP):
        answer_list = item['Answers'] + item['Aliases']

    return answer_list

QUESTION_ID = {
    CWQ: "ID",
    WEBQSP: "ID",
}

def get_question_id(dataset:str) -> str:
    if dataset in QUESTION_ID.keys():
        return QUESTION_ID[dataset]
    for cand_dataset in QUESTION_ID.keys():
        if cand_dataset in dataset:
            return QUESTION_ID[cand_dataset]
    raise KeyError(f"Dataset {dataset} has not been configured quesition id yet.")

def get_entity_answer(data, dataset):
    assert dataset in DATASET.keys(), f"Your dataset {dataset} hasn't been inplemented"
    if dataset == WEBQSP:
        entity_answer = data['Answers']
    else:
        if 'answers' in data.keys():
            entity_answer = data['answers']
        else:
            entity_answer = data['answer']
    return entity_answer

if __name__=='__main__':
    alias = "cwq"
    print(get_dataset_file(alias))
    print(get_question_id(alias))
    print(get_question_string(alias))

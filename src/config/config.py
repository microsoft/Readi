from typing import *
from glob import glob
import os

DATASET_BASE = "data/datasets"
KB_BINDER_PATH = "../KB-BINDER/"
INIT_PLAN_BASE = "data/initial_plan"
RESULT_PATH = "results/KGQA"

CWQ = 'cwq'
GRAILQA_DEV = 'grailqa_dev'
GRAILQA_DEV_FILTER = 'grailqa_dev_filter'
GRAILQA = 'grailqa'
WEBQSP = 'WebQSP'
GRAPHQ = 'graphq'

DATASET = {
    CWQ: "cwq_test_origin_with_topic_alias.json",
    GRAILQA_DEV: "grailqa_dev_pyql_topic_entities.json",
    GRAILQA: "grailqa.json",
    # GRAILQA_DEV_FILTER: "grailqa_dev_afilter_empty_topic_entity.json",
    # WEBQSP: "WebQSP.json",
    # WEBQSP: "webqsp_simple_test.jsonl",
    WEBQSP: "webqsp.json",
    GRAPHQ: "graphquestions_v1_fb15_test_091420.json",
}

def get_dataset_file(dataset: str) -> str:
    if dataset in DATASET.keys():
        return os.path.join(DATASET_BASE, DATASET[dataset])
    cand_file = glob(os.path.join(DATASET_BASE, f"{dataset}*"))
    if(len(cand_file) != 0):
        return cand_file[0]
    raise FileNotFoundError(f"Dataset {dataset} is not a valid registered alias or prefix")

LLM_BASE = {
    'gpt35': "gpt-35-turbo-16k-20230613",
    'gpt4': "gpt-4-32k-20230321",
    'gpt4-turbo': "gpt-4-1106-preview",
}

QUESTION_STRING = {
    CWQ: 'question',
    # WEBQSP: 'RawQuestion',
    WEBQSP: 'Question',
    GRAILQA: 'question',
    GRAPHQ: 'question',
    'simpleqa': 'question',
    'qald': 'question',
    'webquestions': 'question',
    'trex': 'input',
    'zeroshotre': 'input',
    'creak': 'sentence'
}

def get_question_string(dataset: str) -> str:
    if dataset in QUESTION_STRING.keys():
        return QUESTION_STRING[dataset]
    for cand_dataset in QUESTION_STRING.keys():
            return QUESTION_STRING[cand_dataset]
    raise KeyError(f"Dataset {dataset} has not been configured quesition string yet.")

QUESTION_ID = {
    CWQ: "ID",
    # WEBQSP:"QuestionId",
    WEBQSP: "ID",
    GRAILQA: "qid",
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
        # answer_list = data['Parses'][0]['Answers']
        # entity_answer = [
        #     ans.get('EntityName', ans.get('AnswerArgument'))
        #     for ans in answer_list
        # ]
        entity_answer = data['Answers']
    else:
        if 'answers' in data.keys():
            entity_answer = data['answers']
        else:
            entity_answer = data['answer']
    return entity_answer

if __name__=='__main__':
    alias = "grailqa_dev"
    print(get_dataset_file(alias))
    print(get_question_id(alias))
    print(get_question_string(alias))

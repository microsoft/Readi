from typing import *
DATASET_BASE = "data/datasets"

CWQ = 'cwq'
GRAILQA_DEV = 'grailqa_dev'
GRAILQA = 'grailqa'
WEBQSP = 'WebQSP'

DATASET = {
    CWQ: "cwq_test.json",
    GRAILQA_DEV: "grailqa_dev_pyql_topic_entities.json",
    GRAILQA: "grailqa.json",
    WEBQSP: "WebQSP.json",
}

LLM_BASE = {
    'gpt35': "gpt-35-turbo-16k-20230613",
    'gpt4': "gpt-4-32k-20230321"
}

QUESTION_STRING = {
    CWQ: 'question',
    WEBQSP: 'RawQuestion',
    GRAILQA: 'question',
    GRAILQA_DEV: 'question',
    'simpleqa': 'question',
    'qald': 'question',
    'webquestions': 'question',
    'trex': 'input',
    'zeroshotre': 'input',
    'creak': 'sentence'
}

QUESTION_ID = {
    CWQ: "ID",
    WEBQSP:"QuestionId",
    GRAILQA: "qid",
    GRAILQA_DEV: "qid"
}

def get_entity_answer(data, dataset):
    assert dataset in DATASET.keys(), f"Your dataset {dataset} hasn't been inplemented"
    if dataset == WEBQSP:
        answer_list = data['Parses'][0]['Answers']
        entity_answer = [
            ans.get('EntityName', ans.get('AnswerArgument'))
            for ans in answer_list
        ]
    else:
        entity_answer = data['answer']
    return entity_answer

INIT_PLAN_BASE = "data/initial_plan"
RESULT_PATH = "results/KGQA"
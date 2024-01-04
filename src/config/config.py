DATASET_BASE = "data/datasets"
DATASET = {
    'cwq': "cwq_test.json",
    'grailqa_dev': "grailqa_dev_pyql_topic_entities.json",
    'grailqa': "grailqa.json",
    'WebQSP': "WebQSP.json",
}

LLM_BASE = {
    'gpt35': "gpt-35-turbo-16k-20230613",
    'gpt4': "gpt-4-32k-20230321"
}

QUESTION_STRING = {
    'cwq': 'question',
    'WebQSP': 'RawQuestion',
    'grailqa': 'question',
    'grailqa_dev': 'question',
    'simpleqa': 'question',
    'qald': 'question',
    'webquestions': 'question',
    'trex': 'input',
    'zeroshotre': 'input',
    'creak': 'sentence'
}

INIT_PLAN_BASE = "data/initial_plan"
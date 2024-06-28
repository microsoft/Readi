# Call Me When Necessary: LLMs can Efficiently and Faithfully Reason over Structured Environments

<!-- <img width="1237" alt="readi_framework" src=""> -->

This repository contains the open-sourced official implementation of the paper

[Call Me When Necessary: LLMs can Efficiently and Faithfully Reason over Structured Environments](https://arxiv.org/abs/2403.08593). Honored to be published at ACL 2024 Findings.


## Setup 

1. Install all required libraries:
```
$ pip install -r requirements.txt
```
2. **Query Engine Deployment** (Required for cwq and WebQSP)

    a. Please refer to [Freebase Setup](https://github.com/dki-lab/Freebase-Setup) to deploy your Freebase engine to run for cwq and WebQSP. \
    (Just clone the code and follow the readme to setup a server port)
    
    b. Set up the port according to the deployed port in utils/freebase_func.py (e.g. SPARQLPATH = "http://127.0.0.1:3002/sparql")

3. Deploy the retrieval module for relation binding (Required for cwq and WebQSP)

    The resource is from repo: [KB-BINDER](https://github.com/ltl3A87/KB-BINDER).
    
    **Please download** the **index** file and put it under `contriever_fb_relation/freebase_contriever_index/` with this [link](https://drive.google.com/file/d/1hnyW-_k0YaAUZDTdYzhbKDTnFuLEW-W2/view?usp=sharing)

    You can also MODIFY  the path `CONTRIEVER_PATH` in config.py.


4. Create results/(KGQA or MQA or tableqa) folder.

## Run

`MAX_LLM_RETRY_TIME`, `MAX_REFINE_TIME`,`OUTPUT_FILE_PATH` can be modified in config.py.

LLM openai engine can be modifed with `LLM_BASE` in config.py.

### run kgqa (cwq or WebQSP)

Main experiments
```
python src/kgqa.py
--dataset cwq \
--temperature 0.3 \
--max_token 2048 \
--max_token_reasoning 4096 \ 
--max_que 150 \
--llm gpt35 \
--openai_api_key [specify your openai key] \ 
--verbose False
```

Analysis (ablation study, compared methods, etc)
```
python src/kgqa_analysis.py
--dataset cwq \
--temperature 0.3 \
--max_token 2048 \
--max_token_reasoning 4096 \ 
--max_que 150 \
--llm gpt35 \
--openai_api_key [specify your openai key] \
--analysis_strategy [specify your experiments, could be "llm_refine", "init_only", "init_empty", "init_corrupt", "compared_method"] \
--compared_method [choose compared methods if analysis_strategy=='compared_method', could be "rog" or "sr"] \
--verbose False
```


### run metaQA
```
python src/mqa.py
--hop [could be '1hop', '2hop', '3hop'] \
--temperature 0.3 \
--max_token 2048 \
--llm gpt35 \
--verbose False
```
    
### run tableqa  (WTQ or WikiSQL)
WikiTableQuestions
```
python src/tableqa_wtq.py
--temperature 0.3 \
--max_token 2048 \
--llm gpt35 \
--verbose False
```
WikiSQL
```
python src/tableqa_wikisql.py
--hop [could be '1hop', '2hop', '3hop'] \
--temperature 0.3 \
--max_token 2048 \
--llm gpt35 \
--verbose False
```

## File Trees
```
├── data  \\ including experiment datasets, extracted reasoning path for compared methods, index for contriever, and openai_embeddings
│   ├── compare_model_path       \\ extracted reasoning path for compared methods
│   ├── contriever_fb_relation   \\ index for contriever 
│   ├── datasets                 \\ experiment datasets
│   └── openai_embeddings       \\ you can use get_openai_embedding at utils/utils.py to cache embeddings and modify similar_search_list at utils/utils.py to load the cache. (only useful for CWQ and WebQSP).
├── prompt
│   ├── kgqa
│   ├── metaQA
│   └── table_qa
├── README.md
├── requirements.txt
├── results  \\ result files (We do not release our outputfiles, because the results is generated by chatGPT which needs further Review. Feel free to reach out if your have any question of our results.)
│   ├── KGQA
│   └── tableqa
├── src
│   ├── config
│   ├── kg_instantiation.py     \\ code for instantiation module in Readi framework
│   ├── kgqa_analysis.py        \\ code for the analysis experiments on CWQ
│   ├── kgqa.py                 \\ code for cwq, WebQSP.
│   ├── mqa.py
│   ├── sub_graph_evaluation.py  \\ code for calculating features of subgraphs
│   ├── tableqa_wikisql.py
│   └── tableqa_wtq.py
└── utils
    ├── freebase_func.py         \\ knowledge base tools for querying. Should replace the SPARQLPATH according to your deployment (For cwq and WebQSP experiments.)
    └── utils.py
```

## Citation

If you find this paper or code useful, please cite by:

```
@misc{cheng2024necessaryllmsefficientlyfaithfully,
      title={Call Me When Necessary: LLMs can Efficiently and Faithfully Reason over Structured Environments}, 
      author={Sitao Cheng and Ziyuan Zhuang and Yong Xu and Fangkai Yang and Chaoyun Zhang and Xiaoting Qin and Xiang Huang and Ling Chen and Qingwei Lin and Dongmei Zhang and Saravan Rajmohan and Qi Zhang},
      year={2024},
      eprint={2403.08593},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2403.08593}, 
}
```
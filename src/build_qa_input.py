import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
import utils
import random
from typing import Callable
import numpy as np
from pyserini.search import FaissSearcher, LuceneSearcher
from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import AutoQueryEncoder
import json
import time
import openai
from utils.cloudgpt_aoai_new import *
from utils.prompt_list import *
import time



class PromptBuilder(object):
    MCQ_INSTRUCTION = """Please answer the following questions. Please select the answers from the given choices and return the answer only."""
    SAQ_INSTRUCTION = """Please answer the following questions. Please keep the answer as simple as possible and return all the possible answer as a list."""
    MCQ_RULE_INSTRUCTION = """Based on the reasoning paths, please answer the given question. Please select the answers from the given choices and return the answers only."""
    SAQ_RULE_INSTRUCTION = """Based on the reasoning paths, please answer the given question. Please keep the answer as simple as possible and return all the possible answers as a list."""
    COT = """ Let's think it step by step."""
    EXPLAIN = """ Please explain your answer."""
    QUESTION = """Question:\n{question}"""
    GRAPH_CONTEXT = """Reasoning Paths:\n{context}\n\n"""
    CHOICES = """\nChoices:\n{choices}"""
    EACH_LINE = """ Please return each answer in a new line."""

    def __init__(self, prompt_path, add_rule = True, use_true = False, cot = False, explain = False, use_random = False, each_line = False, maximun_token = 4096, tokenize: Callable = lambda x: len(x)):
        self.prompt_template = self._read_prompt_template(prompt_path)
        self.add_rule = add_rule
        self.use_true = use_true
        self.use_random = use_random
        self.cot = cot
        self.explain = explain
        self.maximun_token = maximun_token
        self.tokenize = tokenize
        self.each_line = each_line

        query_encoder = AutoQueryEncoder(encoder_dir='facebook/contriever', pooling='mean')
        self.corpus = LuceneSearcher('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/KB-BINDER/contriever_fb_relation/index_relation_fb')
        bm25_searcher = LuceneSearcher('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/KB-BINDER/contriever_fb_relation/index_relation_fb')
        contriever_searcher = FaissSearcher('/home/v-sitaocheng/demos/llm_hallu/KB-Binder/LLM-KBQA/KB-BINDER/contriever_fb_relation/freebase_contriever_index', query_encoder)

        self.hsearcher = HybridSearcher(contriever_searcher, bm25_searcher)
        
    def _read_prompt_template(self, template_file):
        with open(template_file) as fin:
            prompt_template = f"""{fin.read()}"""
        return prompt_template
    
    def apply_rules(self, graph, rules, srouce_entities):
        results = []
        for entity in srouce_entities:
            for rule in rules:
                res = utils.bfs_with_rule(graph, entity, rule)
                results.extend(res)
        return results
    
    def apply_rules_LLM(self, graph, rules, srouce_entities, grounded_relations):
        results = []
        for entity in srouce_entities:
            for rule in rules:
                reasoning_set = []
                for relation in rule:
                    reasoning_set.append(grounded_relations[relation])
                res = utils.bfs_with_rule_LLM(graph, entity, rule, reasoning_set)
                results.extend(res)
                
        return results
    


    def apply_rules_LLM_revised(self, graph, rules, srouce_entities, grounded_relations):
        results = []
        result_paths = []
        grounded_knowledge_current = []
        ungrounded_neighbor_relation_dict = {}
        path = True
        one_path = True
        if path is True:
            new_rules = {}
            for k, v in rules.items():
                if type(v)==list:
                    new_rules[k] = utils.string_to_path(v[0])
                else:
                    new_rules[k] = utils.string_to_path(v)
            rules = new_rules

        for entity in srouce_entities:

            # for rule in rules[entity]:
            #   grounded relations for each relation in rules
            if entity not in rules.keys():
                continue

            # 注意,每次得到的grounded knowledge和result只会和一个topic entity有关!!!!
            grounded_reasoning_set = []
            if type(rules[entity][0])==str:
                for relation in rules[entity]:
                    grounded_reasoning_set.append(grounded_relations[relation])
            else:
                for relation in rules[entity][0]:
                    grounded_reasoning_set.append(grounded_relations[relation])

            if type(rules[entity][0])==str:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM(graph, entity, rules[entity], grounded_reasoning_set)
            else:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM(graph, entity, rules[entity][0], grounded_reasoning_set)


            # 当前实体出发  如果非空,说明grounding成功, 加入路径
            if len(result_paths) > 0:
                results.extend(result_paths)

            # grounding出来是空的 那么就break, 重新, 根据返回结果来 refine 这条路径, 其他路径不变!
            else:
                return results, result_paths, entity, grounded_knowledge_current, ungrounded_neighbor_relation_dict
                
        

        return results, result_paths, entity, grounded_knowledge_current, ungrounded_neighbor_relation_dict
    


    def apply_rules_LLM_revised_engine(self, rules, srouce_entities, grounded_relations):
        results = []
        result_paths = []
        grounded_knowledge_current = []
        ungrounded_neighbor_relation_dict = {}
        path = True

        entity_id_list = [k for k, v in srouce_entities.items()]

        if path is True:
            new_rules = {}
            for k, v in rules.items():
                if type(v)==list:
                    new_rules[k] = utils.string_to_path(v[0])
                else:
                    new_rules[k] = utils.string_to_path(v)
            rules = new_rules

        for entity in entity_id_list:

            entity_label = srouce_entities[entity]
            if entity_label not in rules.keys():
                continue

            # 注意,每次得到的grounded knowledge和result只会和一个topic entity有关!!!!
            grounded_reasoning_set = []
            if type(rules[entity_label][0])==str:
                for relation in rules[entity_label]:
                    grounded_reasoning_set.append(grounded_relations[relation])
            else:
                for relation in rules[entity_label][0]:
                    grounded_reasoning_set.append(grounded_relations[relation])

            if type(rules[entity_label][0])==str:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity, entity_label, rules[entity_label], grounded_reasoning_set)
            else:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity, entity_label, rules[entity_label][0], grounded_reasoning_set)


            # 当前实体出发  如果非空,说明grounding成功, 加入路径
            if len(result_paths) > 0:
                results.extend(result_paths)

            # grounding出来是空的 那么就break, 重新, 根据返回结果来 refine 这条路径, 其他路径不变!
            else:
                return results, result_paths, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict
                


        return results, result_paths, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict
    

    def apply_rules_LLM_one_path_engine(self, rules, entity_id_label, grounded_relations):
        # results = []
        result_paths = []
        grounded_knowledge_current = []
        ungrounded_neighbor_relation_dict = {}
        path = True

        entity_id, entity_label = entity_id_label
        if path is True:
            if type(rules)==list:
                relation_path_array = utils.string_to_path(rules[0])
            else:
                relation_path_array = utils.string_to_path(rules)

        # grounded_reasoning_set 存储从前往后的 每一个grounded set
        grounded_reasoning_set = []
        for relation in relation_path_array:
            grounded_reasoning_set.append(grounded_relations[relation])

        result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity_id, entity_label, relation_path_array, grounded_reasoning_set)

        # # 当前实体出发  如果非空,说明grounding成功, 加入路径
        # if len(result_paths) > 0:
        #     results.extend(result_paths)

        # # grounding出来是空的 那么就break, 重新, 根据返回结果来 refine 这条路径, 其他路径不变!
        # else:
        #     return results, result_paths, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict
                


        return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict
    


    def direct_answer(self, question_dict):
        graph = utils.build_graph(question_dict['graph'])
        entities = question_dict['q_entity']
        rules = question_dict['predicted_paths']
        prediction = []
        if len(rules) > 0:
            reasoning_paths = self.apply_rules(graph, rules, entities)
            for p in reasoning_paths:
                if len(p) > 0:
                    prediction.append(p[-1][-1])
        return prediction

    def grounding_relations(self, relation, question):
        # relation_path_candidates = items['relation_path_candidates']
        # question = items['question']
        # cwq[index]['relation_path_candidates']['grounded_relations'] = {}
        # cwq[index]['relation_path_candidates']['grounded_relations_no_q'] = {}

        # for key in relation_path_candidates['topic_entities']:
        #     for relations in relation_path_candidates['relation_paths'][key]:
        #         for rel in relations:
        #             if rel in cwq[index]['relation_path_candidates']['grounded_relations'].keys():
        #                 continue
        result= []
        relation_tokens = relation.replace("."," ").replace("_", " ").strip() + " "+ question
        hits = self.hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:10]
        for hit in hits:
            result.append(json.loads(self.corpus.doc(str(hit.docid)).raw())['rel_ori'])

        result_no_q= []
        relation_tokens = relation.replace("."," ").replace("_", " ").strip()
        hits = self.hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:5]
        for hit in hits:
            result_no_q.append(json.loads(self.corpus.doc(str(hit.docid)).raw())['rel_ori'])

        return result, result_no_q


    def ground_relations_from_predictions(self, reasoning_path_LLM_init, question):
        path=True
        # 把所有预测的关系先grounding一下
        rules = []
        if path is False:
            # 用str数组来存路径 效果差一些
            for keys in reasoning_path_LLM_init.keys():
                if type(reasoning_path_LLM_init[keys][0]) == str:
                    rules.append(reasoning_path_LLM_init[keys])
                else:
                    # 这里的rules是LLM生成的路径 initial plan， 现在取每一个topic entity的top1  (因为我最开始实现的的plan 生成了多个)
                    rules.append(reasoning_path_LLM_init[keys][0])
        else:
            for keys in reasoning_path_LLM_init.keys():
                if type(reasoning_path_LLM_init[keys]) == str:
                    rules.append(utils.string_to_path(reasoning_path_LLM_init[keys]))
                else:
                    # 这里的rules是LLM生成的路径 initial plan， 现在取每一个topic entity的top1  (因为我最开始实现的的plan 生成了多个)
                    rules.append(utils.string_to_path(reasoning_path_LLM_init[keys][0]))
        # 对所有路径的每一个关系 grounding （faiss）
        grounded_relations = {}
        for r in rules:
            for rel in r:
                relations, relations_no_q = self.grounding_relations(rel, question)
                if rel not in grounded_relations.keys():
                    grounded_relations[rel] = relations_no_q
                else:
                    grounded_relations[rel] = list(set(grounded_relations[rel]+relations_no_q))
                    
        return grounded_relations


    def get_graph_knowledge(self, question_dict, reasoning_path_LLM):
        question = question_dict['question']
        if not question.endswith('?'):
            question += '?'

        if self.add_rule:
            graph = utils.build_graph(question_dict['graph'])
            entities = question_dict['q_entity']
            if self.use_true:
                rules = question_dict['ground_paths']
            elif self.use_random:
                _, rules = utils.get_random_paths(entities, graph)
            else:
                rules = question_dict['predicted_paths']
            # 这个rules是RoG预测的planning
                
            # if len(rules) > 0:
            if len(reasoning_path_LLM.keys()) > 0:
                # 这里的rules是LLM生成的路径 plan， 现在取每一个topic的top1
                rules = []
                for keys in reasoning_path_LLM:
                    rules.append(reasoning_path_LLM[keys][0])

                reasoning_paths = self.apply_rules_LLM(graph, rules, entities, reasoning_path_LLM['grounded_relations'])
                lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]
                # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])
            else:
                lists_of_paths = []
        
        return reasoning_paths, lists_of_paths

    # def run_llm(self, prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-4-32k-20230321"):
    def run_llm(self, prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-35-turbo-16k-20230613"):
        if "llama" not in engine.lower():           
            openai.api_type = "azure"
            openai.api_base = "https://cloudgpt-openai.azure-api.net/"
            openai.api_version = "2023-07-01-preview"
            openai.api_key = get_openai_token()
        else:
            openai.api_key = opeani_api_keys
            openai.api_key = get_openai_token()

        # messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}]
        messages = []
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
                print(len(messages[-1]["content"]))
                result = ""
                time.sleep(2)
        # print("end openai")
        return result



    def LLM_refine(self, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, End_loop_cur_path):
        # 初始路径 refine之前
        init_path = reasoning_path_LLM_init[entity_label]
        if type(init_path) == list:
            init_path=init_path[0]

        grounded_know = []
        ungrounded_cand_rel = {}

        # 已有的知识, 其他topic的路径   (加不加看效果考虑)
        # for entity, knowledge in grounded_revised_knowledge.items():
        #     if len(knowledge)>0:
        #         grounded_know.append(knowledge)

        # 已有的知识,当前路径   这里可以有一个优化, 同类grounding对的知识 是不是取一个就够了????
        if len(grounded_knowledge_current) < 30:
            for know in grounded_knowledge_current:
                grounded_know.append(know[1])
            ungrounded_cand_rel = ungrounded_neighbor_relation_dict
        else:
            # 非CVT节点
            for i in grounded_knowledge_current:
                node_label = utils.id2entity_name_or_type_en(i[0])
                if node_label.startswith("m.")==False and i[2]!=0:
                    if node_label in ungrounded_neighbor_relation_dict.keys():
                        ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
                    grounded_know.append(i[1])

            if len(grounded_know) > 30 :
                grounded_know = random.sample(grounded_know, 15)

            # cvt可能很多 随机抽10个吧
            cvt_know = [(i[0], i[1]) for i in grounded_knowledge_current if utils.id2entity_name_or_type_en(i[0]).startswith("m.") and len(i[1])>0]
            if len(cvt_know) > 10:
                cand_cvt = random.sample(cvt_know, 10)
            else:
                cand_cvt = cvt_know

            for cvt in cand_cvt:
                if cvt[0] in ungrounded_neighbor_relation_dict.keys():
                    ungrounded_cand_rel[cvt[0]] = ungrounded_neighbor_relation_dict[cvt[0]]
                grounded_know.append(cvt[1])

        # candidate relation用集合方式 不用dict方式 尝试一下
        candidate_rel = []
        for k, v in ungrounded_cand_rel.items():
            candidate_rel.extend(v)
        candidate_rel = list(set(candidate_rel))

        # 关系给太多会爆炸 超过50随机抽50
        if len(candidate_rel) > 50:
            candidate_rel = random.sample(candidate_rel, 50)

        grounded_know_string = ""
        for know in grounded_know:
            if know == []:
                continue
            grounded_know_string+=utils.path_to_string(know) + "\n"

        # prompts = refine_prompt_path_one_path_1222  + "\nQuestion: " + question + "\nInitial Path:" + str(init_path) + "\nGrounded Knowledge:" + grounded_know_string +"\nCandidate Relations:" + str(ungrounded_cand_rel) + "\nThought:"
        prompts = refine_prompt_path_one_path_1224  + "\nQuestion: " + question + "\nInitial Path:" + str(init_path) + "\nGrounded Knowledge:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel) + "\nThought:"
        call_time=0
        while call_time<10:
            response = self.run_llm(prompts, temperature=0.4, max_tokens=4096, opeani_api_keys="")
            try:
                new_rule_path = response.split("Refined Path:")[-1].strip().strip("\"").strip()
                thought = response
                if entity_label not in new_rule_path or "->" not in new_rule_path:
                    raise ValueError("entity_label or -> is not in path")
                reasoning_path_LLM_init[entity_label] = new_rule_path
                refine_time += 1
                if new_rule_path == init_path:
                    refine_time += 10
                # new_reasoning_path_LLM_init=eval(response.split("Refined Path:")[-1].strip())
                # if type(new_reasoning_path_LLM_init) != dict:
                #     raise ValueError("GPT generate type no match, regenerate")
                
                # if len(new_reasoning_path_LLM_init.keys()) == 0:
                #     raise ValueError("GPT generate topics entities no match, regenerate")
                
                # if not path:
                #     for k, v in new_reasoning_path_LLM_init.items():
                #         if type(v) != list:
                #             raise ValueError("GPT generate format no match, regenerate")
                # refine_time += 1

                # if one_path is True:
                #     for key in new_reasoning_path_LLM_init.keys():
                #         if reasoning_path_LLM_init[key] == new_reasoning_path_LLM_init[key]:
                #             refine_time += 10
                #             print(response)
                #             print("****************************************************************************************")
                #         reasoning_path_LLM_init[key]=new_reasoning_path_LLM_init[key]
                # else:
                #     reasoning_path_LLM_init = new_reasoning_path_LLM_init

                break
            except:
                print(response)
                call_time+=1
                print("****************************************************************************************")
                time.sleep(5)

        return reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought


    # Refine framework
    def get_graph_knowledge_LLM_revised_engine(self, question_dict):
        reasoning_path_LLM_init = question_dict['relation_path_candidates']
        question = question_dict['question']
        entities = question_dict['topic_entity']
        if not question.endswith('?'):
            question += '?'
        print("Question:", question)
        # path表示用"->"分割的路径,prompt的一种尝试  如果用数组的话效果会差一些
        path = True

        one_path = True
        refine_time = 0

        # 开始进入框架   可能会套两层while循环 外层对所有实体（整个知识）判断path是否要继续refine。 内层对单个实体的一条路径判断是否需要继续refine
        # while True:
        # 确保有初始路径 or refine过的路径
        if len(reasoning_path_LLM_init.keys()) > 0:
            # 准备用这个来存所有的路径 最后merge
            grounded_revised_knowledge = {}
            reasoning_paths = []
            thought = ""
            lists_of_paths = []

            # 获取对所有路径上的relation 做搜索召回 （top5） 结果是dict {relation: grounded array}

            # 对每一个entity 引导的路径进行grounding
            for entity_id, entity_label in entities.items():
                if entity_label not in reasoning_path_LLM_init.keys():
                    continue
                print("Topic entity: ",entity_label)
                # 每一个entity都要进入refine loop
                while True:
                    grounded_relations = self.ground_relations_from_predictions(reasoning_path_LLM_init, question)

                    # result_path表示 grounding过程中的path,如果是空的,说明当前grounding遇到了问题,需要refine
                    result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = self.apply_rules_LLM_one_path_engine(reasoning_path_LLM_init[entity_label], [entity_id,entity_label], grounded_relations)

                    print(result_paths)
                    print(grounded_knowledge_current)
                    print(ungrounded_neighbor_relation_dict)

                    End_loop_cur_path = True

                    # 硬性判断什么时候停   后续考虑加上LLM来判断是否停下
                    if len(result_paths) > 0:
                        max_path_len =  len(result_paths[-1])
                        for path in result_paths:
                            if len(path) < max_path_len:
                                continue
                            # 最后一个知识以m.结尾 说明遇到了空白节点
                            if path[-1][-1].startswith("m."):
                                End_loop_cur_path = False
                    else:
                        End_loop_cur_path = False        

                    if End_loop_cur_path:
                        reasoning_paths.extend(result_paths)
                        grounded_revised_knowledge[entity_label] = result_paths

                    # llm refine and stop condition
                    if End_loop_cur_path==False:
                        reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought = self.LLM_refine(reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, End_loop_cur_path)


                    if End_loop_cur_path or refine_time > 16:
                        lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]

                        if len(grounded_knowledge_current) > 0:
                            for grounded_path in grounded_knowledge_current:
                                string_path = utils.path_to_string(grounded_path[1])
                                if len(string_path) > 0:

                                    if string_path not in lists_of_paths:
                                        lists_of_paths.append(string_path)

                                    if len(reasoning_paths) == 0:
                                        reasoning_paths.append([])

                                    reasoning_paths[0] += grounded_path[1]
                        # 路径集合
                        lists_of_paths = list(set(lists_of_paths))
                        # 知识集合
                        if len(reasoning_paths)>0:
                            reasoning_paths[0] = list(set(reasoning_paths[0]))

                        break

                    # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])

            # # TODO 遍历完了所有的路径 应该merge一下
            # if len(entities)>1:
            #     for k, v in grounded_revised_knowledge.items():
                    
        return reasoning_paths, lists_of_paths, thought



    def get_graph_knowledge_LLM_revised(self, question_dict, reasoning_path_LLM_init):
        question = question_dict['question']
        if not question.endswith('?'):
            question += '?'

        graph = utils.build_graph(question_dict['graph'])
        entities = question_dict['q_entity']

        path = True
        one_path = True

        refine_time = 0
        # 这个rules是RoG预测的planning
        # if len(rules) > 0:
        while True:
            if len(reasoning_path_LLM_init.keys()) > 0:

                # 这里的rules是LLM生成的路径 plan， 现在取每一个topic的top1
                rules = []
                if path is False:
                    for keys in reasoning_path_LLM_init.keys():
                        if type(reasoning_path_LLM_init[keys][0]) == str:
                            rules.append(reasoning_path_LLM_init[keys])
                        else:
                            rules.append(reasoning_path_LLM_init[keys][0])

                else:
                    for keys in reasoning_path_LLM_init.keys():
                        if type(reasoning_path_LLM_init[keys]) == str:
                            rules.append(utils.string_to_path(reasoning_path_LLM_init[keys]))
                        else:
                            rules.append(utils.string_to_path(reasoning_path_LLM_init[keys][0]))

                # grounding 每一个关系
                grounded_relations = {}
                for r in rules:
                    for rel in r:
                        relations, relations_no_q = self.grounding_relations(rel, question)
                        if rel not in grounded_relations.keys():
                            grounded_relations[rel] = relations_no_q
                        else:
                            grounded_relations[rel] = list(set(grounded_relations[rel]+relations_no_q))
            
                # grounding路径
                # result_path表示 grounding过程中的path,如果是空的,说明当前grounding遇到了问题,需要refine
                reasoning_paths, result_paths, entity, grounded_knowledge_current, ungrounded_neighbor_relation_dict = self.apply_rules_LLM_revised(graph, reasoning_path_LLM_init, entities, grounded_relations)

                if len(result_paths) > 0 or refine_time > 10:
                    lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]
                    if len(grounded_knowledge_current) > 0:
                        for grounded_path in grounded_knowledge_current:
                            string_path = utils.path_to_string(grounded_path[1])
                            if len(string_path) > 0:

                                if string_path not in lists_of_paths:
                                    lists_of_paths.append(string_path)

                                if len(reasoning_paths) == 0:
                                    reasoning_paths.append([])

                                reasoning_paths[0] += grounded_path[1]
                    # 路径集合
                    lists_of_paths = list(set(lists_of_paths))
                    # 知识集合
                    if len(reasoning_paths)>0:
                        reasoning_paths[0] = list(set(reasoning_paths[0]))
                    # for grounded_path in grounded_knowledge_current:
                    #     if len(reasoning_paths) == 0:
                    #         reasoning_paths.append([])
                    #     reasoning_paths[0] += grounded_path[1]

                    break
                else:
                    # llm_REVISE
                    init_path = {}

                    # 初始路径
                    if one_path is True:
                        if path is False:
                            if type(reasoning_path_LLM_init[ent][0]) == str:
                                init_path[entity] = reasoning_path_LLM_init[entity]
                            else:
                                init_path[entity] = reasoning_path_LLM_init[entity][0]
                        else:
                            if type(reasoning_path_LLM_init[entity]) == str:
                                init_path[entity] = reasoning_path_LLM_init[entity]
                            else:
                                init_path[entity] = reasoning_path_LLM_init[entity][0]
                    else:
                        if path is False:
                            for ent in reasoning_path_LLM_init.keys():
                                if type(reasoning_path_LLM_init[ent][0]) == str:
                                    init_path[ent] = reasoning_path_LLM_init[ent]
                                else:
                                    init_path[ent] = reasoning_path_LLM_init[ent][0]
                        else:
                            for ent in reasoning_path_LLM_init.keys():
                                if type(reasoning_path_LLM_init[ent]) == str:
                                    init_path[ent] = reasoning_path_LLM_init[ent]
                                else:
                                    init_path[ent] = reasoning_path_LLM_init[ent][0]


                    grounded_know = []
                   # 已有的知识, 其他topic的路径
                    if len(reasoning_paths)>0:
                        for know in reasoning_paths:
                            grounded_know.append(know)
                    # 已有的知识,当前路径
                    for know in grounded_knowledge_current:
                        grounded_know.append(know[1])

 
                    grounded_know_string = ""
                    for know in grounded_know:
                        if know == []:
                            continue
                        grounded_know_string+=utils.path_to_string(know) + "\n"

                    prompts = refine_prompt_path_one_path_1222  + "\nQuestion: " + question + "\nInitial Path:" + str(init_path) + "\nGrounded Knowledge:" + grounded_know_string +"\nCandidate Relations:" + str(ungrounded_neighbor_relation_dict) + "\nThought:"
                    
                    while True:
                        response = self.run_llm(prompts, temperature=0.4, max_tokens=4096, opeani_api_keys="")
                        try:
                            new_reasoning_path_LLM_init=eval(response.split("Refined Path:")[-1].strip())
                            if type(new_reasoning_path_LLM_init) != dict:
                                raise ValueError("GPT generate type no match, regenerate")
                            
                            if len(new_reasoning_path_LLM_init.keys()) == 0:
                                raise ValueError("GPT generate topics entities no match, regenerate")
                            
                            if not path:
                                for k, v in new_reasoning_path_LLM_init.items():
                                    if type(v) != list:
                                        raise ValueError("GPT generate format no match, regenerate")
                            refine_time += 1
                            if one_path is True:
                                for key in new_reasoning_path_LLM_init.keys():
                                    if reasoning_path_LLM_init[key] == new_reasoning_path_LLM_init[key]:
                                        refine_time += 10
                                        print(response)
                                        print("****************************************************************************************")
                                    reasoning_path_LLM_init[key]=new_reasoning_path_LLM_init[key]
                            else:
                                reasoning_path_LLM_init = new_reasoning_path_LLM_init

                            break
                        except:
                            print(prompts)
                            print(response)
                            time.sleep(5)
                # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])
            
        return reasoning_paths, lists_of_paths



    def process_input(self, question_dict):
        '''
        Take question as input and return the input with prompt
        '''
        question = question_dict['question']
        
        if not question.endswith('?'):
            question += '?'

        if self.add_rule:
            graph = utils.build_graph(question_dict['graph'])
            entities = question_dict['q_entity']
            if self.use_true:
                rules = question_dict['ground_paths']
            elif self.use_random:
                _, rules = utils.get_random_paths(entities, graph)
            else:
                rules = question_dict['predicted_paths']
            if len(rules) > 0:
                reasoning_paths = self.apply_rules(graph, rules, entities)
                lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]
                # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])
            else:
                lists_of_paths = []
            #input += self.GRAPH_CONTEXT.format(context = context)
            
        input = self.QUESTION.format(question = question)
        # MCQ
        if len(question_dict['choices']) > 0:
            choices = '\n'.join(question_dict['choices'])
            input += self.CHOICES.format(choices = choices)
            if self.add_rule:
                instruction = self.MCQ_RULE_INSTRUCTION
            else:
                instruction = self.MCQ_INSTRUCTION
        # SAQ
        else:
            if self.add_rule:
                instruction = self.SAQ_RULE_INSTRUCTION
            else:
                instruction = self.SAQ_INSTRUCTION
        
        if self.cot:
            instruction += self.COT
        
        if self.explain:
            instruction += self.EXPLAIN
            
        if self.each_line:
            instruction += self.EACH_LINE
        
        if self.add_rule:
            other_prompt = self.prompt_template.format(instruction = instruction, input = self.GRAPH_CONTEXT.format(context = "") + input)
            context = self.check_prompt_length(other_prompt, lists_of_paths, self.maximun_token)
            
            input = self.GRAPH_CONTEXT.format(context = context) + input
        
        input = self.prompt_template.format(instruction = instruction, input = input)
            
        return input
    
    def check_prompt_length(self, prompt, list_of_paths, maximun_token):
        '''Check whether the input prompt is too long. If it is too long, remove the first path and check again.'''
        all_paths = "\n".join(list_of_paths)
        all_tokens = prompt + all_paths
        if self.tokenize(all_tokens) < maximun_token:
            return all_paths
        else:
            # Shuffle the paths
            random.shuffle(list_of_paths)
            new_list_of_paths = []
            # check the length of the prompt
            for p in list_of_paths:
                tmp_all_paths = "\n".join(new_list_of_paths + [p])
                tmp_all_tokens = prompt + tmp_all_paths
                if self.tokenize(tmp_all_tokens) > maximun_token:
                    return "\n".join(new_list_of_paths)
                new_list_of_paths.append(p)
            
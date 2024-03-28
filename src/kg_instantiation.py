import os
import utils
from utils import *
from config import *
from pyserini.search import FaissSearcher, LuceneSearcher
from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import AutoQueryEncoder
from collections import deque

query_encoder = AutoQueryEncoder(encoder_dir='facebook/contriever', pooling='mean')
corpus = LuceneSearcher(os.path.join(CONTRIEVER_PATH, "contriever_fb_relation/index_relation_fb"))
bm25_searcher = LuceneSearcher(os.path.join(CONTRIEVER_PATH, 'contriever_fb_relation/index_relation_fb'))
contriever_searcher = FaissSearcher(os.path.join(CONTRIEVER_PATH, 'contriever_fb_relation/freebase_contriever_index'), query_encoder)
hsearcher = HybridSearcher(contriever_searcher, bm25_searcher)

def similar_relation_from_question(question, topk=5):
    result= []
    hits = hsearcher.search(question, k=1000)[:topk]
    for hit in hits:
        result.append(json.loads(corpus.doc(str(hit.docid)).raw())['rel_ori'])
    return result

def grounding_relations(relation, topk=5):
    result_no_q= []
    relation_tokens = relation.replace("."," ").replace("_", " ").strip()
    hits = hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:topk]
    for hit in hits:
        result_no_q.append(json.loads(corpus.doc(str(hit.docid)).raw())['rel_ori'])

    return result_no_q

def relation_binding(reasoning_path_LLM_init, topk=5):
    path=True
    # 把所有预测的关系先grounding一下
    rules = []
    if path is False:
        # 用str数组来存路径 效果差一些
        for keys in reasoning_path_LLM_init.keys():
            if type(reasoning_path_LLM_init[keys][0]) == str:
                rules.append(reasoning_path_LLM_init[keys])
            else:
                # 这里的rules是LLM生成的路径 initial plan， 现在取每一个topic entity的top1  (init plan 实现了多个)
                rules.append(reasoning_path_LLM_init[keys][0])
    else:
        for keys in reasoning_path_LLM_init.keys():
            if type(reasoning_path_LLM_init[keys]) == str:
                rules.append(utils.string_to_path(reasoning_path_LLM_init[keys]))
            elif len(reasoning_path_LLM_init[keys])>0:
                # 这里的rules是LLM生成的路径 initial plan， 现在取每一个topic entity的top1  (init plan 实现了多个)
                rules.append(utils.string_to_path(reasoning_path_LLM_init[keys][0]))
                
    # 对所有路径的每一个关系 grounding （faiss）
    grounded_relations = {}
    for r in rules:
        for rel in r:
            relations_no_q = grounding_relations(rel, topk=topk)
            if rel not in grounded_relations.keys():
                grounded_relations[rel] = relations_no_q
            else:
                grounded_relations[rel] = list(set(grounded_relations[rel]+relations_no_q))

    return grounded_relations


def apply_rules_LLM_one_path_engine(rules, entity_id_label, grounded_relations):
    result_paths = []
    grounded_knowledge_current = []
    ungrounded_neighbor_relation_dict = {}

    entity_id, entity_label = entity_id_label
    relation_path_array = utils.string_to_path(rules[0]) if type(rules)==list else utils.string_to_path(rules)

    grounded_reasoning_set = []
    for relation in relation_path_array:
        grounded_reasoning_set.append(grounded_relations[relation])

    result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity_id, entity_label, relation_path_array, grounded_reasoning_set)

    return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict



def bfs_for_each_path(entity_id, target_rule, grounded_reasoning_set, options, max_que = 300):
    result_paths = []
    current_position = 0
    queue = deque([(entity_id, [], current_position)])  # 使用队列存储待探索节点和对应路径
    grounded_knowledge_current = []
    ungrounded_neighbor_relation_dict={}

    while queue:
        size = len(queue)
        ungrounded_neighbor_relation_dict.clear()
        # 遍历当前层
        if options.verbose:
            print("current layer size when BFS", size)

        while size > 0:
            size -= 1
            current_node, current_path, current_position = queue.popleft()

            # 先存储当前层grounded过的路径  注意,这里面每一个都是路径 包括从0 到当前长度的所有路径
            grounded_knowledge_current.append((current_node, current_path, current_position))

            if current_position == len(target_rule) and current_path not in result_paths and len(current_path)>0:
                result_paths.append(current_path)

            # 如果当前路径长度小于规则长度，继续探索
            if current_position < len(target_rule):
                # 当前已有的relation
                pre_relations = [rel[1] for rel in current_path]
                edge_set = utils.get_ent_one_hop_rel(current_node, pre_relations=pre_relations)
                
                if len(edge_set) == 0:
                    continue
                # 取交集
                # LLM预测的grounded的relation结果
                list1 = grounded_reasoning_set[current_position]
                # 实际的下一跳的relation
                list2 = edge_set
                list3 = pre_relations

                intersection_grounded = list(set(list1) & set(list2))    
                intersection_have_grounded = list(set(intersection_grounded) & set(list3))    
                intersection = list(set(intersection_grounded) - set(intersection_have_grounded))

                # 当前层的当前节点没有交集 要存储一下当前节点的邻居 用来refine
                if len(intersection) <= 0:
                    ungrounded_neighbor_relation_dict[utils.id2entity_name_or_type_en(current_node)] = edge_set
                    continue
                # 当前层的当前节点有交集，说明grounded到了  加入队列（等待下一层)
                else:
                    for relation in intersection:
                        if len(queue)>=max_que:
                            break
                        # 前向 后向关系
                        neighbors_with_relation = [neighbor for neighbor in utils.entity_search(current_node, relation, True) + utils.entity_search(current_node, relation, False)]
                        for neighbor in neighbors_with_relation:
                            if len(queue) < max_que:
                                queue.append((neighbor, current_path + [(utils.id2entity_name_or_type_en(current_node), relation, utils.id2entity_name_or_type_en(neighbor))], current_position + 1))
                            else:
                                break
                            
        if len(ungrounded_neighbor_relation_dict.keys()) == 0 and len(grounded_knowledge_current)==1 and grounded_knowledge_current[-1][-1]==0:
            ungrounded_neighbor_relation_dict[utils.id2entity_name_or_type_en(grounded_knowledge_current[-1][0])] = utils.get_ent_one_hop_rel(grounded_knowledge_current[-1][0])

    return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict


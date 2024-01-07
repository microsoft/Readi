import networkx as nx
from collections import deque
import walker
from utils import *
import utils

def build_graph(graph: list) -> nx.Graph:
    G = nx.Graph()
    for triplet in graph:
        h, r, t = triplet
        G.add_edge(h, t, relation=r.strip())
        G.add_edge(t, h, relation=r.strip()) #double direction
    return G

# 定义一个函数来进行宽度优先搜索
def bfs_with_rule(graph, start_node, target_rule, max_p = 10):
    result_paths = []
    queue = deque([(start_node, [])])  # 使用队列存储待探索节点和对应路径
    while queue:
        current_node, current_path = queue.popleft()

        # 如果当前路径符合规则，将其添加到结果列表中
        if len(current_path) == len(target_rule):
            result_paths.append(current_path)
            # if len(result_paths) >= max_p:
            #     break
            
        # 如果当前路径长度小于规则长度，继续探索
        if len(current_path) < len(target_rule):
            if current_node not in graph:
                continue
            for neighbor in graph.neighbors(current_node):
                # 剪枝：如果当前边类型与规则中的对应位置不匹配，不继续探索该路径
                rel = graph[current_node][neighbor]['relation']
                if rel != target_rule[len(current_path)] or len(current_path) > len(target_rule):
                    continue
                queue.append((neighbor, current_path + [(current_node, rel, neighbor)]))
    
    return result_paths


def bfs_with_rule_LLM_heuristic(graph, start_node, target_rule, reasoning_set, max_p = 10):
    result_paths = []
    current_position = 0

    queue = deque([(start_node, [], current_position)])  # 使用队列存储待探索节点和对应路径

    while queue:
        current_node, current_path, current_position = queue.popleft()

        # print(current_node, current_path, current_position)
        # 如果当前路径符合规则，将其添加到结果列表中
        # if len(current_path) == len(target_rule):
        if current_position == len(target_rule) and current_path not in result_paths:
            result_paths.append(current_path)
            
        if len(current_path) >= len(target_rule) + 3:
            continue

        # 如果当前路径长度小于规则长度，继续探索
        if current_position < len(target_rule):
            if current_node not in graph:
                continue

            for neighbor in graph.neighbors(current_node):
                # 剪枝：如果当前边类型与规则中的对应位置不匹配，不继续探索该路径
                if current_position > len(target_rule):
                    continue
            
                rel = graph[current_node][neighbor]['relation']

                # 当前关系在候选列表 直接加入 并往前走一步. 分两种情况，该节点可能是空白节点，也可能不是
                if rel in reasoning_set[current_position]:
                    # 是空白节点，判断是否前进
                    if neighbor.startswith("m.") or neighbor.startswith('g.'):
                        for neibor_cvt in graph.neighbors(neighbor):
                            rel_onemore = graph[neighbor][neibor_cvt]['relation']
                            if rel_onemore == rel:
                                continue
                            if rel_onemore in reasoning_set[current_position]:
                                # neighbor是cvt， cvt的下一条也表示的是这个语义，则多走一步
                                queue.append((neibor_cvt, current_path + [(current_node, rel, neighbor), (neighbor, rel_onemore, neibor_cvt)], current_position+1))
                    # 不是空白节点，直接加入
                    else:
                        queue.append((neighbor, current_path + [(current_node, rel, neighbor)], current_position+1))
                        
                # 当前关系不在候选列表  多走一步看看
                else:
                    for neibor_2 in graph.neighbors(neighbor):
                        rel_onemore = graph[neighbor][neibor_2]['relation']

                        if rel_onemore == rel or (current_node, rel, neighbor) not in current_path:
                            continue

                        # 漏了一个关系
                        if rel_onemore in reasoning_set[current_position]:

                            # 是空白节点，判断是否前进
                            if neibor_2.startswith("m.") or neighbor.startswith('g.'):
                                for neibor_cvt in graph.neighbors(neibor_2):
                                    rel_twomore = graph[neibor_2][neibor_cvt]['relation']
                                    if rel_twomore == rel_onemore:
                                        continue
                                    if rel_twomore in reasoning_set[current_position]:
                                        # neighbor是cvt， cvt的下一条也表示的是这个语义，则多走一步
                                        queue.append((neibor_2, current_path + [(current_node, rel, neighbor), (neighbor, rel_onemore, neibor_2), (neibor_2, rel_twomore, neibor_cvt)], current_position+1))
                            # 不是空白节点，直接加入
                            else:
                                queue.append((neighbor, current_path + [(current_node, rel, neighbor), (neighbor, rel_onemore, neibor_2)], current_position+1))

                            if current_position+1==len(reasoning_set):
                                if current_path not in result_paths:
                                    result_paths.append(current_path)

                            break
                        # 当前关系可能是错的，下一跳能match上
                        if current_position+1 < len(reasoning_set) and rel_onemore in reasoning_set[current_position+1] and (current_node, rel, neighbor) not in current_path:
                            queue.append((neighbor, current_path + [(current_node, rel, neighbor)], current_position+1))

    return result_paths


def bfs_with_rule_LLM(graph, start_node, target_rule, grounded_reasoning_set, max_p = 10):
    result_paths = []
    current_position = 0
    queue = deque([(start_node, [], current_position)])  # 使用队列存储待探索节点和对应路径
    grounded_knowledge_current=[]
    ungrounded_neighbor_relation_dict={}

    while queue:
        size = len(queue)
        # grounded_knowledge_current.clear()
        # ungrounded_neighbor_relation_dict.clear()

        # 遍历当前层
        while size > 0:
            size -= 1
            current_node, current_path, current_position = queue.popleft()

            # 先存储当前层grounded过的路径  注意,这里面每一个都是路径 包括从0 到当前长度的所有路径
            grounded_knowledge_current.append((current_node, current_path, current_position))

            if current_position == len(target_rule) and current_path not in result_paths:
                result_paths.append(current_path)

            # 如果当前路径长度小于规则长度，继续探索
            if current_position < len(target_rule):
                if current_node not in graph:
                    continue
                edge_set = []
                neighbor_set = []

                for neighbor in graph.neighbors(current_node):
                    edge_set.append(graph[current_node][neighbor]['relation'])
                    neighbor_set.append(neighbor)
                
                # 取交集
                # LLM预测的grounded的relation结果
                list1 = grounded_reasoning_set[current_position]
                # 实际的下一跳的relation
                list2 = edge_set

                # 当前已有的relation
                list3 = [rel[1] for rel in current_path]

                intersection_grounded = list(set(list1) & set(list2))    
                
                intersection_have_grounded = list(set(intersection_grounded) & set(list3))    
                intersection = list(set(intersection_grounded) - set(intersection_have_grounded))

                # 当前层的当前节点没有交集 要存储一下当前节点的邻居 用来refine
                if len(intersection) <= 0:
                    ungrounded_neighbor_relation_dict[current_node] = edge_set
                    continue

                # 当前层的当前节点有交集，说明grounded到了  加入队列（等待下一层)
                else:
                    for relation in intersection:
                        neighbors_with_relation = [neighbor for neighbor, attrs in graph[current_node].items() if attrs['relation'] == relation]
                        for neighbor in neighbors_with_relation:
                            queue.append((neighbor, current_path + [(current_node, relation, neighbor)], current_position + 1))

    return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict


def grounding_with_engine(entity_id, entity_label, target_rule, grounded_reasoning_set):
    relation_values_dict = {}
    entity_values_dict = {}
    size_of_path = len(grounded_reasoning_set)
    size_of_entities = size_of_path+1

    for i in range(size_of_path):
        key = "?relation"+str(i)
        relation_values_dict[key] = ""
        for relation in grounded_reasoning_set[i]:
            relation_values_dict[key] += "ns:"+relation + " "
        relation_values_dict[key] = "VALUES " + key +" {" + relation_values_dict[key].strip() + "}."

    for i in range(size_of_entities):
        key = "?entity" + str(i)
        entity_values_dict[key] = ""
        if i == 0:
            entity_values_dict[key] += "ns:" + str(entity_id)
            entity_values_dict[key] = "VALUES " + key +" {" + entity_values_dict[key].strip() + "}."


    return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict
  

def bfs_with_rule_LLM_engine(entity_id, entity_label, target_rule, grounded_reasoning_set, max_p = 10):
    result_paths = []
    current_position = 0
    queue = deque([(entity_id, [], current_position)])  # 使用队列存储待探索节点和对应路径
    grounded_knowledge_current = []
    ungrounded_neighbor_relation_dict={}

    while queue:
        size = len(queue)
        # grounded_knowledge_current.clear()
        # ungrounded_neighbor_relation_dict.clear()
        # 遍历当前层
        print("current layer size when BFS", size)

        # size太大了 应该是遇到了超级大节点 这时候如果是cvt可以考虑剪枝一下
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
                    #这里也可以考虑来一个相似度排序!!!TODO
                    ungrounded_neighbor_relation_dict[utils.id2entity_name_or_type_en(current_node)] = edge_set
                    continue
                # 当前层的当前节点有交集，说明grounded到了  加入队列（等待下一层)
                else:
                    for relation in intersection:
                        if len(queue)>=500:
                            break
                        # 前向 后向关系
                        neighbors_with_relation = [neighbor for neighbor in utils.entity_search(current_node, relation, True) + utils.entity_search(current_node, relation, False)]
                        for neighbor in neighbors_with_relation:
                            if len(queue) < 500:
                                queue.append((neighbor, current_path + [(utils.id2entity_name_or_type_en(current_node), relation, utils.id2entity_name_or_type_en(neighbor))], current_position + 1))
                            else:
                                break
                            
        if len(ungrounded_neighbor_relation_dict.keys()) == 0 and len(grounded_knowledge_current)==1 and grounded_knowledge_current[-1][-1]==0:
            ungrounded_neighbor_relation_dict[utils.id2entity_name_or_type_en(grounded_knowledge_current[-1][0])] = utils.get_ent_one_hop_rel(grounded_knowledge_current[-1][0])

    return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict


def get_truth_paths(q_entity: list, a_entity: list, graph: nx.Graph) -> list:
    '''
    Get shortest paths connecting question and answer entities.
    '''
    # Select paths
    paths = []
    for h in q_entity:
        if h not in graph:
            continue
        for t in a_entity:
            if t not in graph:
                continue
            try:
                for p in nx.all_shortest_paths(graph, h, t):
                    paths.append(p)
            except:
                pass
    # Add relation to paths
    result_paths = []
    for p in paths:
        tmp = []
        for i in range(len(p)-1):
            u = p[i]
            v = p[i+1]
            tmp.append((u, graph[u][v]['relation'], v))
        result_paths.append(tmp)
    return result_paths
    
def get_simple_paths(q_entity: list, a_entity: list, graph: nx.Graph, hop=2) -> list:
    '''
    Get all simple paths connecting question and answer entities within given hop
    '''
    # Select paths
    paths = []
    for h in q_entity:
        if h not in graph:
            continue
        for t in a_entity:
            if t not in graph:
                continue
            try:
                for p in nx.all_simple_edge_paths(graph, h, t, cutoff=hop):
                    paths.append(p)
            except:
                pass
    # Add relation to paths
    result_paths = []
    for p in paths:
        result_paths.append([(e[0], graph[e[0]][e[1]]['relation'], e[1]) for e in p])
    return result_paths

def get_negative_paths(q_entity: list, a_entity: list, graph: nx.Graph, n_neg: int, hop=2) -> list:
    '''
    Get negative paths for question witin hop
    '''
    # sample paths
    start_nodes = []
    end_nodes = []
    node_idx = list(graph.nodes())
    for h in q_entity:
        if h in graph:
            start_nodes.append(node_idx.index(h))
    for t in a_entity:
        if t in graph:
            end_nodes.append(node_idx.index(t))
    paths = walker.random_walks(graph, n_walks=n_neg, walk_len=hop, start_nodes=start_nodes, verbose=False)
    # Add relation to paths
    result_paths = []
    for p in paths:
        tmp = []
        # remove paths that end with answer entity
        if p[-1] in end_nodes:
            continue
        for i in range(len(p)-1):
            u = node_idx[p[i]]
            v = node_idx[p[i+1]]
            tmp.append((u, graph[u][v]['relation'], v))
        result_paths.append(tmp)
    return result_paths

# def get_random_paths(q_entity: list, graph: nx.Graph, n=3, hop=2) -> tuple [list, list]:
    '''
    Get negative paths for question witin hop
    '''
    # sample paths
    start_nodes = []
    node_idx = list(graph.nodes())
    for h in q_entity:
        if h in graph:
            start_nodes.append(node_idx.index(h))
    paths = walker.random_walks(graph, n_walks=n, walk_len=hop, start_nodes=start_nodes, verbose=False)
    # Add relation to paths
    result_paths = []
    rules = []
    for p in paths:
        tmp = []
        tmp_rule = []
        for i in range(len(p)-1):
            u = node_idx[p[i]]
            v = node_idx[p[i+1]]
            tmp.append((u, graph[u][v]['relation'], v))
            tmp_rule.append(graph[u][v]['relation'])
        result_paths.append(tmp)
        rules.append(tmp_rule)
    return result_paths, rules
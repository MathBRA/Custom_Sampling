import networkx as nx
import random
from collections import deque


def RWEB(G, n):
    
    """
    RANDOM WALK EDGE BLOCKING

    Parâmetros:
        G (networkx.Graph): grafo original
        n (int): número de nós a visitar

    Retorna:
        networkx.Graph: subgrafo com os nós e arestas visitados
    """
    
    G = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_graph = nx.Graph()

    nodes = list(G.nodes())
    if not nodes:
        return sampled_graph

    # Inicializa pilha e primeiro nó aleatório
    start_node = random.choice(nodes)
    stack = [start_node]
    sampled_graph.add_node(start_node)

    while sampled_graph.number_of_nodes() < n and stack:
        current_node = stack[-1]  # topo da pilha
        neighbors = list(G.neighbors(current_node))
        if neighbors:
            # Escolhe vizinho aleatório e remove a aresta do grafo original
            next_node = random.choice(neighbors)
            G.remove_edge(current_node, next_node)

            # Adiciona ao grafo amostrado
            sampled_graph.add_node(next_node)
            sampled_graph.add_edge(current_node, next_node)

            # Empilha o próximo nó
            stack.append(next_node)
        else:
            # Backtrack (desempilha)
            stack.pop()

    return sampled_graph


def IRWEB(G, n):
    """
    
    - Caminha aleatoriamente como SRW
    - A cada nó visitado, adiciona todos os seus vizinhos ao subgrafo (indução local)
    - Não remove arestas do grafo original, mas as marca como "usadas" para a caminhada
    - Usa pilha para backtracking

    Parâmetros:
        G (networkx.Graph): grafo original
        n (int): número de nós a visitar via caminhada (não contando vizinhos induzidos)
    
    Retorna:
        networkx.Graph: subgrafo induzido a partir dos nós visitados
    """
    # Sempre trabalhe com uma cópia para evitar modificar o grafo original
    G = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_graph = nx.Graph()

    nodes = list(G.nodes())
    if not nodes:
        return sampled_graph

    current_node = random.choice(nodes)
    stack = [current_node]
    visited = set() # Conjunto de NÓS visitados pela caminhada (para contar até 'n')
    walk_edges_visited = set() # Conjunto de ARESTAS percorridas pela caminhada (para evitar revisitações)
    
    # --- INDUÇÃO LOCAL INICIAL OTIMIZADA ---
    # Adiciona o nó inicial e todos os seus vizinhos imediatos (e arestas entre eles)
    nodes_in_neighborhood = {current_node}
    nodes_in_neighborhood.update(G.neighbors(current_node))

    # Obtém a "view" do subgrafo induzido para esses nós
    initial_induced_subgraph_view = G.subgraph(nodes_in_neighborhood)
    # Adiciona os nós e arestas dessa "view" ao grafo amostrado
    sampled_graph.add_nodes_from(initial_induced_subgraph_view.nodes())
    sampled_graph.add_edges_from(initial_induced_subgraph_view.edges())
    
    # Marca o nó inicial como visitado pela caminhada
    visited.add(current_node)

    while len(visited) < n and stack:
        # Encontra vizinhos disponíveis que ainda não foram "percorridos" a partir de current_node
        neighbors = list(G.neighbors(current_node))
        available_next_nodes = []
        for neighbor in neighbors:
            # Verifica se a aresta (current_node, neighbor) não foi usada na caminhada
            # Como grafos são não direcionados, verifica ambas as direções da tupla da aresta
            if (current_node, neighbor) not in walk_edges_visited and \
               (neighbor, current_node) not in walk_edges_visited:
                available_next_nodes.append(neighbor)

        if available_next_nodes:
            next_node = random.choice(available_next_nodes)
            
            # Marca a aresta como "percorrida" para futuras verificações
            # IMPORTANTE: Adiciona ao walk_edges_visited, NÃO ao visited
            walk_edges_visited.add((current_node, next_node))
            walk_edges_visited.add((next_node, current_node)) # Para grafos não direcionados

            # Se o próximo nó ainda não foi visitado pela caminhada principal
            if next_node not in visited:
                visited.add(next_node) # Adiciona o NÓ ao conjunto de nós visitados
                stack.append(next_node)
                current_node = next_node

                # --- INDUÇÃO LOCAL OTIMIZADA PARA O NÓ RECÉM-VISITADO ---
                # Adiciona o current_node e todos os seus vizinhos imediatos (e arestas entre eles)
                nodes_in_neighborhood = {current_node}
                nodes_in_neighborhood.update(G.neighbors(current_node))

                # Obtém a "view" do subgrafo induzido e adiciona ao sampled_graph
                induced_subgraph_view = G.subgraph(nodes_in_neighborhood)
                sampled_graph.add_nodes_from(induced_subgraph_view.nodes())
                sampled_graph.add_edges_from(induced_subgraph_view.edges())
            else:
                # Se o next_node já foi visitado pela caminhada, apenas move para ele
                # e não o conta novamente para 'n' nem adiciona seus vizinhos novamente
                current_node = next_node
        else:
            # Backtrack se não houver arestas disponíveis do current_node
            stack.pop()
            if stack:
                current_node = stack[-1]
            # else: stack está vazia, não pode mais fazer backtracking

    return sampled_graph

def SB(G, n, k):
    """
    Snowball Sampling baseado em BFS com limite de k vizinhos por nó.

    - Inicia a partir de um nó aleatório.
    - Expande em largura, mas cada nó visita até k vizinhos aleatórios.
    - Utiliza fila (BFS) para explorar em camadas.
    - Garante que no máximo n nós sejam visitados.

    Parâmetros:
        G (networkx.Graph): grafo original
        n (int): número máximo de nós a visitar
        k (int): número máximo de vizinhos explorados por nó

    Retorna:
        networkx.Graph: subgrafo amostrado
    """
    G = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_graph = nx.Graph()

    nodes = list(G.nodes())
    if not nodes:
        return sampled_graph

    visited = set()
    queue = deque()

    # Começa com nó aleatório
    start_node = random.choice(nodes)
    visited.add(start_node)
    sampled_graph.add_node(start_node)
    queue.append(start_node)

    while queue and len(visited) < n:
        current_node = queue.popleft()
        neighbors = list(G.neighbors(current_node))
        random.shuffle(neighbors)
        
        # Limita a até k vizinhos não visitados
        count = 0
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                sampled_graph.add_node(neighbor)
                sampled_graph.add_edge(current_node, neighbor)
                queue.append(neighbor)
                count += 1
                if len(visited) >= n or count >= k:
                    break
            elif sampled_graph.has_node(neighbor):
                sampled_graph.add_edge(current_node, neighbor)

    return sampled_graph

def TIES(G, n, p):
    """
    Total Induction Edge Sampling (TIES)

    - Amostra arestas aleatórias do grafo original.
    - Adiciona os dois nós da aresta à amostra.
    - Repete até atingir uma fração p * n de nós amostrados.
    - Em seguida, forma o subgrafo induzido contendo todas as arestas entre os nós amostrados.

    Parâmetros:
        G (networkx.Graph): grafo original
        n (int): número total de nós do grafo original
        p (float): fração de nós desejada (ex: 0.1 para 10%)

    Retorna:
        networkx.Graph: subgrafo induzido com os nós amostrados
    """
    G = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_nodes = set()
    edges = list(G.edges())
    random.shuffle(edges)

    target_num_nodes = max(1, int(p * n))

    # Etapa 1: amostragem de arestas
    for u, v in edges:
        sampled_nodes.add(u)
        sampled_nodes.add(v)
        if len(sampled_nodes) >= target_num_nodes:
            break

    # Etapa 2: indução de subgrafo
    induced_graph = nx.Graph()
    induced_graph.add_nodes_from(sampled_nodes)
    for u, v in G.edges():
        if u in sampled_nodes and v in sampled_nodes:
            induced_graph.add_edge(u, v)

    return induced_graph

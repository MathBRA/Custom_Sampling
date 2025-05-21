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
    - Remove arestas já usadas do grafo original
    - Usa pilha para backtracking

    Parâmetros:
        G (networkx.Graph): grafo original
        n (int): número de nós a visitar via caminhada (não contando vizinhos induzidos)
    
    Retorna:
        networkx.Graph: subgrafo induzido a partir dos nós visitados
    """
    G = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_graph = nx.Graph()

    nodes = list(G.nodes())
    if not nodes:
        return sampled_graph

    current_node = random.choice(nodes)
    stack = [current_node]
    visited = set()
    
    # Adiciona o nó inicial e seus vizinhos ao subgrafo
    sampled_graph.add_node(current_node)
    visited.add(current_node)
    
    neighbors = list(G.neighbors(current_node))
    for nb in neighbors:
        sampled_graph.add_node(nb)
        if G.has_edge(current_node, nb):
            sampled_graph.add_edge(current_node, nb)
        # Adiciona também vizinho <-> vizinho, se houver
        for other_nb in neighbors:
            if nb != other_nb and G.has_edge(nb, other_nb):
                sampled_graph.add_edge(nb, other_nb)

    while len(visited) < n and stack:
        neighbors = list(G.neighbors(current_node))

        if neighbors:
            next_node = random.choice(neighbors)
            G.remove_edge(current_node, next_node)

            if next_node not in visited:
                visited.add(next_node)
                stack.append(next_node)
                current_node = next_node

                sampled_graph.add_node(current_node)

                neighbors = list(G.neighbors(current_node))
                for nb in neighbors:
                    sampled_graph.add_node(nb)
                    if G.has_edge(current_node, nb):
                        sampled_graph.add_edge(current_node, nb)
                    for other_nb in neighbors:
                        if nb != other_nb and G.has_edge(nb, other_nb):
                            sampled_graph.add_edge(nb, other_nb)
            else:
                current_node = next_node  # mesmo já visitado, anda mesmo assim
        else:
            stack.pop()
            if stack:
                current_node = stack[-1]

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

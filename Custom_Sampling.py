import networkx as nx
import random
from collections import deque


def RWEB(G, max_n, checkpoint_sizes):
    """
    RANDOM WALK EDGE BLOCKING com checkpoints.

    - Caminha aleatoriamente, removendo arestas percorridas do grafo original.
    - Utiliza uma pilha para backtracking.
    - Retorna o subgrafo amostrado em pontos específicos (checkpoints).

    Parâmetros:
        G (networkx.Graph): grafo original.
        max_n (int): número MÁXIMO de nós que o subgrafo amostrado deve atingir.
        checkpoint_sizes (list): Lista de inteiros, tamanhos de nós do subgrafo
                                 amostrado nos quais uma cópia deve ser salva.
                                 A lista DEVE estar em ordem crescente.

    Retorna:
        list: Uma lista de networkx.Graph, onde cada grafo é o sampled_graph
              no momento em que seu número de nós atingiu um checkpoint.
              A ordem dos grafos na lista corresponde à ordem de checkpoint_sizes.
    """
    # Sempre trabalha com uma cópia, pois as arestas serão removidas
    G_copy = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_graph = nx.Graph()

    nodes = list(G_copy.nodes())
    if not nodes:
        # Se não há nós no grafo original, retorna grafos vazios para os checkpoints
        return [sampled_graph] * len(checkpoint_sizes)

    # Inicializa pilha e primeiro nó aleatório
    start_node = random.choice(nodes)
    stack = [start_node]
    sampled_graph.add_node(start_node) # Adiciona o nó inicial à amostra

    # Lista para armazenar os grafos nos checkpoints
    checkpoint_graphs = [None] * len(checkpoint_sizes)
    current_checkpoint_idx = 0
    
    # Garantir que os checkpoints estão em ordem crescente
    checkpoint_sizes.sort()

    # --- VERIFICAÇÃO DO PRIMEIRO CHECKPOINT (se start_node já atende) ---
    while current_checkpoint_idx < len(checkpoint_sizes) and \
          sampled_graph.number_of_nodes() >= checkpoint_sizes[current_checkpoint_idx]:
        
        checkpoint_graphs[current_checkpoint_idx] = sampled_graph.copy() # Copia o estado atual
        current_checkpoint_idx += 1


    # Loop principal da caminhada
    # Continua enquanto não atingir max_n e a pilha não estiver vazia
    while sampled_graph.number_of_nodes() < max_n and stack:
        current_node = stack[-1] # Pega o nó no topo da pilha

        # Encontra vizinhos do nó atual no grafo G_copy (que está sendo modificado)
        neighbors = list(G_copy.neighbors(current_node))

        if neighbors:
            # Escolhe um vizinho aleatório
            next_node = random.choice(neighbors)
            
            # Remove a aresta do grafo original G_copy (característica do RWEB)
            G_copy.remove_edge(current_node, next_node)

            # Adiciona o próximo nó e a aresta ao grafo amostrado
            # Verifica se o nó já está na amostra para não contá-lo novamente no checkpoint
            node_added_to_sample = False
            if next_node not in sampled_graph:
                sampled_graph.add_node(next_node)
                node_added_to_sample = True # Indica que um novo nó foi adicionado à amostra real
            
            sampled_graph.add_edge(current_node, next_node)

            # Empilha o próximo nó
            stack.append(next_node)

            # --- VERIFICAÇÃO DE CHECKPOINTS NO LOOP ---
            # Se um novo nó foi adicionado à amostra, verifica se um checkpoint foi atingido
            if node_added_to_sample:
                while current_checkpoint_idx < len(checkpoint_sizes) and \
                      sampled_graph.number_of_nodes() >= checkpoint_sizes[current_checkpoint_idx]:
                    
                    # Copia o estado atual da sampled_graph e armazena
                    checkpoint_graphs[current_checkpoint_idx] = sampled_graph.copy()
                    current_checkpoint_idx += 1
        else:
            # Se não há vizinhos disponíveis no grafo G_copy, faz backtracking (desempilha)
            stack.pop()
    
    # Preenche checkpoints não atingidos:
    # Se a caminhada terminou antes de atingir todos os checkpoints ou max_n,
    # os checkpoints restantes recebem uma cópia do grafo amostrado final
    for i in range(len(checkpoint_sizes)):
        if checkpoint_graphs[i] is None:
            # Se a amostra final tem nós, usa-a. Caso contrário, usa um grafo vazio.
            if sampled_graph.number_of_nodes() > 0:
                checkpoint_graphs[i] = sampled_graph.copy()
            else:
                checkpoint_graphs[i] = nx.Graph() # Retorna grafo vazio se a amostra não cresceu

    return checkpoint_graphs


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

def SB(G, max_n, k, checkpoint_sizes):
    """
    Snowball Sampling baseado em BFS com limite de k vizinhos por nó e checkpoints.

    - Inicia a partir de um nó aleatório.
    - Expande em largura, mas cada nó visita até k vizinhos aleatórios.
    - Utiliza fila (BFS) para explorar em camadas.
    - O amostragem continua até que o sampled_graph atinja max_n nós.
    - Retorna o subgrafo amostrado em pontos específicos (checkpoints).

    Parâmetros:
        G (networkx.Graph): grafo original
        max_n (int): número MÁXIMO de nós para o subgrafo amostrado.
        k (int): número máximo de vizinhos explorados por nó.
        checkpoint_sizes (list): Lista de inteiros, tamanhos de nós do subgrafo
                                 amostrado nos quais uma cópia deve ser salva.
                                 A lista DEVE estar em ordem crescente.

    Retorna:
        list: Uma lista de networkx.Graph, onde cada grafo é o sampled_graph
              no momento em que seu número de nós atingiu um checkpoint.
              A ordem dos grafos na lista corresponde à ordem de checkpoint_sizes.
    """
    G_copy = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_graph = nx.Graph()

    nodes = list(G_copy.nodes())
    if not nodes:
        return [sampled_graph] * len(checkpoint_sizes)

    visited = set()
    queue = deque()

    checkpoint_graphs = [None] * len(checkpoint_sizes)
    current_checkpoint_idx = 0
    
    checkpoint_sizes.sort()

    start_node = random.choice(nodes)
    
    visited.add(start_node)
    sampled_graph.add_node(start_node)
    queue.append(start_node)

    while current_checkpoint_idx < len(checkpoint_sizes) and \
          sampled_graph.number_of_nodes() >= checkpoint_sizes[current_checkpoint_idx]:
        
        checkpoint_graphs[current_checkpoint_idx] = sampled_graph.copy()
        current_checkpoint_idx += 1

    while queue and sampled_graph.number_of_nodes() < max_n:
        current_node = queue.popleft()
        
        neighbors = list(G_copy.neighbors(current_node))
        random.shuffle(neighbors)

        neighbors_to_explore_count = 0 
        for neighbor in neighbors:
            # Verifica se o vizinho ainda não foi adicionado ao sampled_graph
            if neighbor not in visited:
                # Se o limite de nós para a amostra já foi atingido, para
                if sampled_graph.number_of_nodes() >= max_n:
                    break

                visited.add(neighbor)
                sampled_graph.add_node(neighbor)
                sampled_graph.add_edge(current_node, neighbor)
                queue.append(neighbor)
                neighbors_to_explore_count += 1

                # Verifica se o limite de 'k' vizinhos para o current_node foi atingido
                # Este é o uso correto do parâmetro 'k' do seu SB original
                if neighbors_to_explore_count >= k:
                    break

                # --- VERIFICAÇÃO DE CHECKPOINTS ---
                while current_checkpoint_idx < len(checkpoint_sizes) and \
                      sampled_graph.number_of_nodes() >= checkpoint_sizes[current_checkpoint_idx]:
                    
                    checkpoint_graphs[current_checkpoint_idx] = sampled_graph.copy()
                    current_checkpoint_idx += 1
            elif sampled_graph.has_node(neighbor):
                if not sampled_graph.has_edge(current_node, neighbor):
                    sampled_graph.add_edge(current_node, neighbor)

    for i in range(len(checkpoint_sizes)):
        if checkpoint_graphs[i] is None:
            if sampled_graph.number_of_nodes() > 0:
                checkpoint_graphs[i] = sampled_graph.copy()
            else:
                checkpoint_graphs[i] = nx.Graph()

    return checkpoint_graphs

def TIES(G, max_n, checkpoint_sizes):
    """
    Total Induction Edge Sampling (TIES) com checkpoints, usando valores absolutos para nós.

    - Amostra arestas aleatórias do grafo original.
    - Adiciona os dois nós da aresta à amostra.
    - O processo de amostragem continua até que o número ABSOLUTO de nós amostrados
      atinja 'max_n'.
    - Durante esse processo, o subgrafo induzido é salvo em checkpoints definidos
      por números ABSOLUTOS de nós.

    Parâmetros:
        G (networkx.Graph): grafo original.
        max_n (int): número MÁXIMO ABSOLUTO de nós a serem amostrados.
        checkpoint_sizes (list): Lista de inteiros, o número ABSOLUTO de nós
                                 amostrados nos quais um subgrafo induzido
                                 deve ser copiado e retornado.
                                 A lista DEVE estar em ordem crescente.

    Retorna:
        list: Uma lista de networkx.Graph, onde cada grafo é o subgrafo induzido
              no momento em que o número de nós amostrados atingiu um checkpoint.
              A ordem dos grafos na lista corresponde à ordem de checkpoint_sizes.
    """
    G_copy = nx.convert_node_labels_to_integers(G.copy(), 0, 'default', True)
    sampled_nodes = set()
    edges = list(G_copy.edges()) # Pega uma lista de todas as arestas
    random.shuffle(edges) # Embaralha para seleção aleatória de arestas

    # Lista para armazenar os grafos induzidos nos checkpoints
    checkpoint_graphs = [None] * len(checkpoint_sizes)
    current_checkpoint_idx = 0
    
    # Garantir que os checkpoints estão em ordem crescente
    checkpoint_sizes.sort()

    # --- Lógica de Amostragem de Arestas e Checkpoints ---
    for u, v in edges:
        # Se já atingimos o número máximo de nós alvo, paramos de adicionar novos
        if len(sampled_nodes) >= max_n:
            break

        nodes_before_add = len(sampled_nodes) # Para verificar se novos nós foram adicionados

        # Adiciona os nós da aresta atual à amostra (se ainda não estiverem lá)
        # Tenta adicionar o primeiro nó
        if u not in sampled_nodes:
            sampled_nodes.add(u)
        # Tenta adicionar o segundo nó, mas verifica se já excedeu max_n com o primeiro
        if v not in sampled_nodes and len(sampled_nodes) < max_n: # Só adiciona V se não ultrapassar max_n
            sampled_nodes.add(v)
        
        # Se nenhum nó novo foi adicionado por esta aresta, continue para a próxima aresta
        if len(sampled_nodes) == nodes_before_add:
            continue

        # --- VERIFICAÇÃO DE CHECKPOINTS ---
        # Itera por todos os checkpoints que podem ter sido atingidos com a adição dos últimos nós
        while current_checkpoint_idx < len(checkpoint_sizes) and \
              len(sampled_nodes) >= checkpoint_sizes[current_checkpoint_idx]:
            
            # Forma o subgrafo induzido com os nós coletados ATÉ ESTE CHECKPOINT
            # É FUNDAMENTAL copiar, pois sampled_nodes continuará crescendo
            current_induced_graph = G_copy.subgraph(sampled_nodes).copy()
            
            checkpoint_graphs[current_checkpoint_idx] = current_induced_graph
            current_checkpoint_idx += 1

    # --- PREENCHE CHECKPOINTS NÃO ATINGIDOS ---
    # Se a amostragem terminou antes de atingir todos os checkpoints,
    # os checkpoints restantes recebem uma cópia do grafo amostrado final
    for i in range(len(checkpoint_sizes)):
        if checkpoint_graphs[i] is None:
            # Se houver nós amostrados até o final da iteração, cria o grafo induzido final.
            # Caso contrário, retorna um grafo vazio.
            if sampled_nodes: # Se o conjunto sampled_nodes não estiver vazio
                final_induced_graph = G_copy.subgraph(sampled_nodes).copy()
                checkpoint_graphs[i] = final_induced_graph
            else:
                checkpoint_graphs[i] = nx.Graph() # Grafo vazio

    return checkpoint_graphs

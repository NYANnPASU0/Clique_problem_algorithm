def bron_kerbosch_original(graph):
    result = []    
    def bk(R, P, X):
        if len(P) == 0 and len(X) == 0:
            result.append(R.copy())
            return
        
        for v in list(P):
            new_R = R.copy()
            new_R.add(v)
            
            new_P = set()
            for vertex in P:
                if vertex in graph[v]:
                    new_P.add(vertex)
            
            new_X = set()
            for vertex in X:
                if vertex in graph[v]:
                    new_X.add(vertex)
            
            bk(new_R, new_P, new_X)
            
            P.remove(v)
            X.add(v)
    
    R = set()
    P = set(graph.keys())
    X = set()
    
    bk(R, P, X)
    return result


def bron_kerbosch_tomita(graph):
    result = []
    
    def func(R, P, X):

        if len(P) == 0 and len(X) == 0:
            result.append(R.copy())
            return
        
        union = P.union(X)
        main = None
        max_neighbors_in_p = -1
        
        for i in union:
            neighbors_in_p = 0
            for neighbor in graph[i]:
                if neighbor in P:
                    neighbors_in_p += 1
            
            if neighbors_in_p > max_neighbors_in_p:
                max_neighbors_in_p = neighbors_in_p
                main = i
        
        # Перебираем только вершины из P, которые НЕ являются соседями pivot
        vertices_to_process = []
        for v in P:
            if v not in graph[main]:
                vertices_to_process.append(v)
        
        for v in vertices_to_process:
            R.add(v)
            
            # Новые кандидаты: пересечение P с соседями v
            new_P = set()
            for vertex in P:
                if vertex in graph[v]:
                    new_P.add(vertex)
            
            # Новые обработанные: пересечение X с соседями v
            new_X = set()
            for vertex in X:
                if vertex in graph[v]:
                    new_X.add(vertex)
            
            func(R, new_P, new_X)
            
            R.remove(v)
            P.remove(v)
            X.add(v)
    
    func(set(), set(graph.keys()), set())
    return result


def find_cliques(graph, algorithm='tomita'):
    if algorithm == 'original':
        return bron_kerbosch_original(graph)
    elif algorithm == 'tomita':
        return bron_kerbosch_tomita(graph)


def find_maximum_clique(graph, algorithm='tomita'):
    all_cliques = find_cliques(graph, algorithm)
    if len(all_cliques) == 0:
        return set()
    
    maximum_clique = all_cliques[0]
    for clique in all_cliques:
        if len(clique) > len(maximum_clique):
            maximum_clique = clique
    
    return maximum_clique


if __name__ == "__main__":
    graph = {
        0: {1, 2},
        1: {0, 2},
        2: {0, 1},
        3: {4},
        4: {3},
        5: set()
    }
    
    alg = 'original'
    
    print(f"Алгоритм: {'Томиты' if alg == 'tomita' else 'Брона-Кербоша'}")
    print("-" * 50)
    
    print("Все максимальные клики:")
    cliques = find_cliques(graph, alg)
    for i, clique in enumerate(cliques, 1):
        print(f"Клика {i}: {clique}")
    
    max_clique = find_maximum_clique(graph, alg)
    print(f"\nНаибольшая клика: {max_clique}")
    print(f"Размер наибольшей клики: {len(max_clique)}")
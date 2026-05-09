import sys
import time
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

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
            
            new_P = set()
            for vertex in P:
                if vertex in graph[v]:
                    new_P.add(vertex)
            
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


def read_graph_from_file(filename):
    graph = {} 
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip() # удаление пробелов и переносов строк
            if not line: # пропуск пустых строк
                continue
            if line.endswith(','): #если строка заканчивается запятой, убираем её
                line = line[:-1]
            
            parts = line.split(':', 1) # разделение строки 1 раз по первому двоеточию
            
            node_str = parts[0].strip() # номер вершины
            neighbors_str = parts[1].strip() 
            
            node = int(node_str)
            if neighbors_str.startswith('{') and neighbors_str.endswith('}'):
                neighbors_str = neighbors_str[1:-1]
            
            neighbors = set()
            if neighbors_str:
                for n_str in neighbors_str.split(','):
                    n_str = n_str.strip()
                    if n_str:
                        neighbors.add(int(n_str))
            
            graph[node] = neighbors 
            
    return graph


def benchmark_algorithms(graphs_data): #сравнивает производительность алгоритмов и выводит таблицу
    timeout_sec = 15
    
    print("\n" + "="*80)
    print("ТАБЛИЦА СРАВНЕНИЯ АЛГОРИТМОВ")
    print("="*80)
    print(f"{'Вершины':<10} | {'Алгоритм':<20} | {'Время (сек)':<15} | {'Макс. клика':<15} ")
    print("-"*80)
    
    results = {}
    
    for n, graph in graphs_data.items():
        # алгоритм Брона-Кербоша
        start_orig = time.perf_counter()
        timed_out_orig = False
        with ThreadPoolExecutor() as executor:
            future = executor.submit(bron_kerbosch_original, graph)
            cliques_orig = future.result(timeout=timeout_sec)
        time_orig = time.perf_counter() - start_orig
        max_clique_orig = max(len(c) for c in cliques_orig) if cliques_orig else 0
        
        print(f"{n:<10} | {'Брон-Кербош':<20} | {time_orig:<15.4f} | {str(max_clique_orig):<15}")
        
        # алгоритм с опорной точкой
        start_tomita = time.perf_counter()
        cliques_tomita = bron_kerbosch_tomita(graph)
        time_tomita = time.perf_counter() - start_tomita
        max_clique_tomita = max(len(c) for c in cliques_tomita) if cliques_tomita else 0
        
        print(f"{n:<10} | {'Томита':<20} | {time_tomita:<15.4f} | {str(max_clique_tomita):<15} | ✓")
        
        # Сохраняем результаты
        results[n] = {
            'original_time': time_orig,
            'tomita_time': time_tomita,
            'max_clique': max_clique_tomita,
            'clique_tomita': find_maximum_clique(graph, 'tomita')
        }
        
        # Выводим сравнение
        if not timed_out_orig:
            speedup = time_orig / time_tomita if time_tomita > 0 else float('inf')
            print(f"{'':<10} | {'Ускорение Томиты:':<20} | {speedup:<15.2f}x |")
        print("-"*80)

    return results


class GraphVisualizerApp:
    def __init__(self, root, graphs_data, benchmark_results):
        self.root = root
        self.root.title("Визуализация графов и максимальных клик")
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.state('zoomed')
        
        self.graphs_data = graphs_data
        self.benchmark_results = benchmark_results
        
        self.create_widgets()
        self.draw_all_graphs()
    
    def create_widgets(self):
        # Главный контейнер с прокруткой
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Сравнение алгоритмов поиска максимальной клики", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Создаем фрейм для графиков (3 в ряд)
        graphs_frame = ttk.Frame(main_frame)
        graphs_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Настройка сетки для 3 графиков
        for i in range(3):
            graphs_frame.grid_columnconfigure(i, weight=1)
        graphs_frame.grid_rowconfigure(0, weight=1)
        
        # Создаем по одному холсту для каждого графа
        self.canvases = []
        self.figures = []
        
        sizes = sorted(self.graphs_data.keys())
        
        for i, n in enumerate(sizes):
            # Создаем фрейм для одного графа
            graph_frame = ttk.LabelFrame(graphs_frame, text=f"Граф с {n} вершинами", padding="5")
            graph_frame.grid(row=0, column=i, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
            
            # Создаем фигуру matplotlib
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # Создаем canvas
            canvas = FigureCanvasTkAgg(fig, graph_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            
            self.figures.append((fig, ax, n))
            self.canvases.append(canvas)
        
        # Панель с информацией о производительности
        info_frame = ttk.LabelFrame(main_frame, text="Результаты сравнения", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        # Создаем текстовый виджет для отображения таблицы
        self.info_text = tk.Text(info_frame, height=8, font=('Courier', 10))
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        self.update_info_text()
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.draw_all_graphs()
        ttk.Button(button_frame, text="Закрыть", command=self.root.destroy).pack(side=tk.LEFT, padx=5)
    
    def update_info_text(self): #добавление таблицы на экран
        self.info_text.delete(1.0, tk.END)
        
        info = "СРАВНЕНИЕ АЛГОРИТМОВ\n"
        info += "="*70 + "\n"
        info += f"{'Вершин':<8} | {'Брон-Кербош (сек)':<20} | {'Томита (сек)':<15} | {'Макс. клика':<12} | {'Ускорение'}\n"
        info += "-"*70 + "\n"
        
        for n in sorted(self.graphs_data.keys()):
            result = self.benchmark_results[n]
            orig_time = result['original_time']
            tomita_time = result['tomita_time']
            max_clique = result['max_clique']
            
            if orig_time >= 15:
                orig_str = "> 15 (прервано)"
            else:
                orig_str = f"{orig_time:.4f}"
            
            speedup = orig_time / tomita_time if tomita_time > 0 else float('inf')
            
            info += f"{n:<8} | {orig_str:<20} | {tomita_time:<15.4f} | {max_clique:<12} | {speedup:.2f}x\n"
        
        self.info_text.insert(1.0, info)
    
    def draw_all_graphs(self): #отрисовка трех графов
        sizes = sorted(self.graphs_data.keys())
        
        for i, (fig, ax, n) in enumerate(self.figures):
            ax.clear()
            
            graph = self.graphs_data[n]
            max_clique = self.benchmark_results[n]['clique_tomita']
            
            # Создаем граф networkx
            G = nx.Graph()
            for node, neighbors in graph.items():
                for neighbor in neighbors:
                    if node < neighbor:
                        G.add_edge(node, neighbor)
                    if node not in G:
                        G.add_node(node)
            
            if n <= 20:
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            else:
                pos = nx.circular_layout(G)

            #pos = nx.spring_layout(G, k=2, iterations=50, seed=42) - пружинный (силовой) алгоритм
            #pos = nx.circular_layout(G) - по кругу
            #pos = nx.shell_layout(G) - болочки (ракушки)
            #pos = nx.spiral_layout(G) - спиральное расположение
            #pos = nx.random_layout(G, seed=42) - случайное расположение
     
            
            clique_nodes = max_clique if max_clique else set()
            non_clique_nodes = set(G.nodes()) - clique_nodes
            
            clique_edges = []
            non_clique_edges = []
            
            for edge in G.edges():
                if edge[0] in clique_nodes and edge[1] in clique_nodes:
                    clique_edges.append(edge)
                else:
                    non_clique_edges.append(edge)
            
            # Рисуем граф
            nx.draw_networkx_edges(G, pos, edgelist=non_clique_edges, 
                                  edge_color='black', width=1.0, alpha=0.6, ax=ax)
            
            nx.draw_networkx_edges(G, pos, edgelist=clique_edges, 
                                  edge_color='red', width=2.5, ax=ax)
            
            nx.draw_networkx_nodes(G, pos, nodelist=list(non_clique_nodes),
                                  node_color='lightgray', node_size=300,
                                  edgecolors='black', linewidths=1.5, ax=ax)
            
            nx.draw_networkx_nodes(G, pos, nodelist=list(clique_nodes),
                                  node_color='red', node_size=400,
                                  edgecolors='darkred', linewidths=2, ax=ax)
            
            # Подписываем вершины
            labels = {node: str(node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax)
            
            # убирает числовые метки осей
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"Размер клики: {len(max_clique)}", fontsize=12, fontweight='bold')
            
            # Добавляем легенду для первого графика
            if i == 0:
                from matplotlib.patches import Patch
                from matplotlib.lines import Line2D
                legend_elements = [
                    Patch(facecolor='red', edgecolor='darkred', label='Клика'),
                    Patch(facecolor='lightgray', edgecolor='black', label='Вершины'),
                    Line2D([0], [0], color='red', linewidth=2.5, label='Ребра клики'),
                    Line2D([0], [0], color='black', linewidth=1.0, label='Ребра')
                ]
                ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
        
        for canvas in self.canvases:
            canvas.draw()


def main():
    sizes = [10, 30, 50]
    probability = 0.3
    
    graphs_data = {}
    
    for n in sizes:
        print(f"\nГраф с {n} вершинами")
        G = nx.gnp_random_graph(n, probability, seed=42)
        graph = {node: set(G.neighbors(node)) for node in G.nodes()}
        graphs_data[n] = graph
        
        edge_count = sum(len(neighbors) for neighbors in graph.values()) // 2
        print(f"Граф: {n} вершин, {edge_count} ребер")
    
    benchmark_results = benchmark_algorithms(graphs_data)
    
    root = tk.Tk()
    app = GraphVisualizerApp(root, graphs_data, benchmark_results)
    root.mainloop()

if __name__ == "__main__":
    main()
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
            
            bk(new_R, P.intersection(graph[v]), X.intersection(graph[v]))
            
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
            neighbors_in_p = len(graph[i].intersection(P))
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
            
            func(R, P.intersection(graph[v]), X.intersection(graph[v]))
            
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
            neighbors_str = parts[1].strip() # список соседей
            
            node = int(node_str) # преобразование из строки в целое число 
            if neighbors_str.startswith('{') and neighbors_str.endswith('}'): # проверка на фигурные скобки
                neighbors_str = neighbors_str[1:-1] # убираем их
            
            neighbors = set()
            if neighbors_str:
                for n_str in neighbors_str.split(','): # разделение строки с соседями по запятым
                    n_str = n_str.strip() # очистка от пробелов 
                    if n_str:
                        neighbors.add(int(n_str)) # преобразование и добавление
            
            graph[node] = neighbors 
            
    return graph


def benchmark_algorithms(graphs_data): #сравнивает производительность алгоритмов и выводит таблицу
    timeout_sec = 15
    
    print("\n" + "="*80)
    print("ТАБЛИЦА СРАВНЕНИЯ АЛГОРИТМОВ")
    print("="*80)
    print(f"{'Кол-во вершин':<10} | {'Алгоритм':<20} | {'Время (сек)':<15} | {'Макс. клика':<15} ")
    print("-"*80)
    
    results = {}
    
    for n, graph in graphs_data.items():
        # алгоритм Брона-Кербоша
        timed_out_orig = False

        start_orig = time.perf_counter()
        cliques_orig = bron_kerbosch_original(graph)
        time_orig = time.perf_counter() - start_orig
        max_clique_orig = max(len(c) for c in cliques_orig) if cliques_orig else 0
        
        print(f"{n:<10} | {'Брон-Кербош':<20} | {time_orig:<15.4f} | {str(max_clique_orig):<15}")
        
        # алгоритм с опорной точкой
        start_tomita = time.perf_counter()
        cliques_tomita = bron_kerbosch_tomita(graph)
        time_tomita = time.perf_counter() - start_tomita
        max_clique_tomita = max(len(c) for c in cliques_tomita) if cliques_tomita else 0
        
        print(f"{n:<10} | {'Томита':<20} | {time_tomita:<15.4f} | {str(max_clique_tomita):<15} | ✓")
        
        results[n] = {
            'original_time': time_orig,
            'tomita_time': time_tomita,
            'max_clique': max_clique_tomita,
            'clique_tomita': find_maximum_clique(graph, 'tomita')
        }
        
        if not timed_out_orig:
            speedup = time_orig / time_tomita if time_tomita > 0 else float('inf')
            print(f"{'':<10} | {'Ускорение Томиты:':<20} | {speedup:<15.2f}x |")
        print("-"*80)

    return results


class Visualise_Graph:
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
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="Сравнение алгоритмов поиска максимальной клики", font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        graphs_frame = ttk.Frame(main_frame)
        graphs_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # настройка сетки для 3-х графиков
        for i in range(3):
            graphs_frame.grid_columnconfigure(i, weight=1)
        graphs_frame.grid_rowconfigure(0, weight=1)
        
        self.canvases = []
        self.figures = []
        
        sizes = sorted(self.graphs_data.keys())
        
        for i, n in enumerate(sizes):
            graph_frame = ttk.LabelFrame(graphs_frame, text=f"Граф с {n} вершинами", padding="10")
            graph_frame.grid(row=0, column=i, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
            
            # создание фигуры matplotlib
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            canvas = FigureCanvasTkAgg(fig, graph_frame) # встраивает matplotlib в tkinter
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            
            self.figures.append((fig, ax, n))
            self.canvases.append(canvas)
        
        # панель с таблицей и легендой
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=False, pady=10)
        
        bottom_frame.grid_columnconfigure(0, weight=1)  # Таблица
        bottom_frame.grid_columnconfigure(1, weight=1)  # Легенда
        
        info_frame = ttk.LabelFrame(bottom_frame, text="Результаты сравнения", padding="5")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.info_text = tk.Text(info_frame, height=10, font=('Courier', 10))
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        legend_frame = ttk.LabelFrame(bottom_frame, padding="5")
        legend_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.legend_canvas = tk.Canvas(legend_frame, height=150, bg='white', highlightthickness=0)
        self.legend_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.update_info_text()
        self.update_legend()

    def update_info_text(self): #добавление таблицы на экран
        self.info_text.delete(1.0, tk.END)
        
        info = "-"*105 + "\n"
        info += f"{'Кол-во вершин':<10} | {'алг. Брона-Кербоша(сек)':<20} | {'алг. с опорной точкой (Томита)(сек)':<15} | {'Макс. клика':<12} | {'Сравнение'}\n"
        info += "-"*105 + "\n"
        
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
            
            info += f"{n:^13} | {orig_str:<23} | {tomita_time:<15.4f}                     | {max_clique:<12} | {speedup:.2f}x\n"
        
        self.info_text.insert(1.0, info)
    
    def draw_all_graphs(self): #отрисовка трех графов
        sizes = sorted(self.graphs_data.keys())
        
        for i, (fig, ax, n) in enumerate(self.figures):
            ax.clear()
            
            graph = self.graphs_data[n]
            max_clique = self.benchmark_results[n]['clique_tomita']
            
            # создаю граф networkx
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
            
            nx.draw_networkx_edges(G, pos, edgelist=non_clique_edges, edge_color='black', width=1.0, alpha=0.5, ax=ax) # ребра графа
            nx.draw_networkx_edges(G, pos, edgelist=clique_edges, edge_color='red', width=2, ax=ax) # ребра клики
            
            nx.draw_networkx_nodes(G, pos, nodelist=list(non_clique_nodes), node_color='lightgray', node_size=250,
                                   edgecolors='black', linewidths=1, ax=ax) # вершины графа
            nx.draw_networkx_nodes(G, pos, nodelist=list(clique_nodes), node_color='red', node_size=280,
                                   edgecolors='black', linewidths=1.5, ax=ax) # вершины клики
            
            labels = {node: str(node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=7, font_weight='bold', ax=ax) # подпись вершин
            
            # убирает числовые метки осей
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"Размер клики: {len(max_clique)}", fontsize=12, fontweight='bold')
            
        for canvas in self.canvases:
            canvas.draw()
        
        self.update_legend() # добавляю легенду


    def update_legend(self): 
        self.legend_canvas.delete("all")
        w = self.legend_canvas.winfo_width()
        h = self.legend_canvas.winfo_height()
            
        x_start = 20
        y_start = 20
        spacing = 35
        
        self.legend_canvas.create_oval(x_start, y_start-8, x_start+18, y_start+10, fill='red', outline='black', width=1)
        self.legend_canvas.create_text(x_start+30, y_start, text="Вершины макс. клики", anchor='w', font=('Arial', 10))
        
        y2 = y_start + spacing
        self.legend_canvas.create_oval(x_start, y2-8, x_start+18, y2+10, fill='lightgray', outline='black', width=1)
        self.legend_canvas.create_text(x_start+30, y2, text="Вершины графа", anchor='w', font=('Arial', 10))
        
        y3 = y_start + spacing*2
        self.legend_canvas.create_line(x_start, y3, x_start+18, y3, fill='red', width=2.5)
        self.legend_canvas.create_text(x_start+30, y3, text="Рёбра макс. клики", anchor='w', font=('Arial', 10))
        
        y4 = y_start + spacing*3
        self.legend_canvas.create_line(x_start, y4, x_start+18, y4, fill='black', width=1.0)
        self.legend_canvas.create_text(x_start+30, y4, text="Рёбра графа", anchor='w', font=('Arial', 10))


def main():
    sizes = [10, 30, 50]
    probability = 0.5
    
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
    app = Visualise_Graph(root, graphs_data, benchmark_results)
    root.mainloop()

if __name__ == "__main__":
    main()
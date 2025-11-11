import matplotlib.pyplot as plt
import re
import os

def leer_gramatica(archivo="gramatica.txt"):
    gramatica = {}
    with open(archivo, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "->" in linea:
                izquierda, derecha = linea.split("->", 1)
                izquierda = izquierda.strip()
                producciones = [p.strip().split() for p in derecha.split("|")]
                gramatica[izquierda] = gramatica.get(izquierda, []) + producciones
    return gramatica

class NodoAST:
    def __init__(self, tipo, texto, valor=None):
        self.tipo = tipo
        self.texto = texto
        self.valor = valor
        self.hijos = []

    def agregar_hijo(self, n):
        self.hijos.append(n)

class TablaSimbolos:
    def __init__(self):
        self.ids = {}
        self.literales = {}

def calcular_first(gramatica):
    first = {nt: set() for nt in gramatica}
    cambio = True
    while cambio:
        cambio = False
        for nt, prods in gramatica.items():
            for prod in prods:
                if not prod:
                    first[nt].add("ε")
                    continue
                for s in prod:
                    if s not in gramatica:
                        if s not in first[nt]:
                            first[nt].add(s)
                            cambio = True
                        break
                    else:
                        antes = len(first[nt])
                        first[nt] |= (first[s] - {"ε"})
                        if "ε" not in first[s]:
                            break
                        if len(first[nt]) != antes:
                            cambio = True
    return first

def calcular_follow(gramatica, simbolo_inicial, first):
    follow = {nt: set() for nt in gramatica}
    follow[simbolo_inicial].add("$")
    cambio = True
    while cambio:
        cambio = False
        for A, prods in gramatica.items():
            for prod in prods:
                for i, B in enumerate(prod):
                    if B in gramatica:
                        beta = prod[i+1:]
                        conjunto = set()
                        if beta:
                            for b in beta:
                                if b in gramatica:
                                    conjunto |= (first[b] - {"ε"})
                                    if "ε" not in first[b]:
                                        break
                                else:
                                    conjunto.add(b)
                                    break
                            antes = len(follow[B])
                            follow[B] |= conjunto
                            if len(follow[B]) != antes:
                                cambio = True
                        else:
                            antes2 = len(follow[B])
                            follow[B] |= follow[A]
                            if len(follow[B]) != antes2:
                                cambio = True
    return follow

def calcular_predict(gramatica, first, follow):
    predict = {}
    for A, prods in gramatica.items():
        for prod in prods:
            conjunto = set()
            for s in prod:
                if s in gramatica:
                    conjunto |= (first[s] - {"ε"})
                    if "ε" not in first[s]:
                        break
                else:
                    conjunto.add(s)
                    break
            else:
                conjunto |= follow[A]
            predict[(A, tuple(prod))] = conjunto
    return predict

def tokenizar(expr):
    tokens, i = [], 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1; continue
        if c in "+-*/()":
            tokens.append({'tipo':'op','texto':c}); i += 1; continue
        if c.isdigit() or (c == '.' and i+1 < len(expr) and expr[i+1].isdigit()):
            j = i; punto = False
            while j < len(expr) and (expr[j].isdigit() or (expr[j]=='.' and not punto)):
                if expr[j]=='.': punto = True
                j += 1
            tokens.append({'tipo':'num','texto':expr[i:j]}); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j]=='_'): j += 1
            tokens.append({'tipo':'id','texto':expr[i:j]}); i = j; continue
        raise SyntaxError(f"Caracter inesperado: {c}")
    return tokens

PRECEDENCIA = {'+':1, '-':1, '*':2, '/':2}

def construir_ast(tokens):
    valores, ops = [], []
    def aplicar():
        op = ops.pop()
        der = valores.pop()
        izq = valores.pop()
        nodo = NodoAST('operador', op)
        nodo.agregar_hijo(izq); nodo.agregar_hijo(der)
        valores.append(nodo)
    for t in tokens:
        if t['tipo'] in ('num','id'):
            tipo = 'numero' if t['tipo']=='num' else 'id'
            nodo = NodoAST(tipo, t['texto'], float(t['texto']) if tipo=='numero' else None)
            valores.append(nodo)
        elif t['texto'] == '(':
            ops.append('(')
        elif t['texto'] == ')':
            while ops and ops[-1] != '(':
                aplicar()
            ops.pop()
        else:
            while ops and ops[-1] in PRECEDENCIA and PRECEDENCIA[ops[-1]] >= PRECEDENCIA[t['texto']]:
                aplicar()
            ops.append(t['texto'])
    while ops:
        aplicar()
    if not valores:
        raise SyntaxError("Expresion vacia o invalida")
    return valores[0]

def recolectar_tabla(nodo, tabla):
    
    if nodo.tipo == 'numero':
        if nodo.texto not in tabla.literales:
            tabla.literales[nodo.texto] = {'valor': nodo.valor, 'veces': 1}
        else:
            tabla.literales[nodo.texto]['veces'] += 1

    elif nodo.tipo == 'id':
        if nodo.texto not in tabla.ids:
            tabla.ids[nodo.texto] = {
                'nombre': nodo.texto,
                'valor': None,
                'tipo': 'desconocido',
                'alcance': 'global',
                'veces': 1
            }
        else:
            tabla.ids[nodo.texto]['veces'] += 1

    elif nodo.tipo == 'operador':
        if nodo.texto not in tabla.ids:
            tabla.ids[nodo.texto] = {
                'nombre': nodo.texto,
                'valor': None,
                'tipo': 'operador',
                'alcance': 'global',
                'veces': 1
            }
        else:
            tabla.ids[nodo.texto]['veces'] += 1

    for h in nodo.hijos:
        recolectar_tabla(h, tabla)

def evaluar_ast(nodo, tabla=None):
    if nodo.tipo == 'numero':
        return nodo.valor
    if nodo.tipo == 'id':
        if tabla is None:
            raise NameError(f"Identificador {nodo.texto} sin tabla de símbolos")
        info = tabla.ids.get(nodo.texto)
        if info is None or info.get('valor') is None:
            raise NameError(f"Identificador {nodo.texto} sin valor asignado")
        nodo.valor = info['valor']
        return nodo.valor
    if nodo.tipo == 'operador':
        iz = evaluar_ast(nodo.hijos[0], tabla)
        de = evaluar_ast(nodo.hijos[1], tabla)
        if nodo.texto == '+': nodo.valor = iz + de
        elif nodo.texto == '-': nodo.valor = iz - de
        elif nodo.texto == '*': nodo.valor = iz * de
        elif nodo.texto == '/':
            if de == 0: raise ZeroDivisionError("Division por cero")
            nodo.valor = iz / de
        return nodo.valor
    return None

def graficar_ast(nodo, filename):
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_title("Punto 4 - Arbol de Sintaxis Decorado (AST) Descendente", fontsize=12)
    ax.axis('off')

    colores = {'operador': '#FFB347', 'id': '#82E0AA', 'numero': '#85C1E9'}

    def calcular_posiciones(n, x=0, y=0, nivel=0, posiciones=None, separacion=2.0):
        if posiciones is None:
            posiciones = {}
        posiciones[n] = (x, -nivel)
        if n.hijos:
            total_hijos = len(n.hijos)
            ancho = separacion * (total_hijos - 1)
            inicio_x = x - ancho / 2
            for i, h in enumerate(n.hijos):
                posiciones = calcular_posiciones(h, inicio_x + i * separacion, y - 1, nivel + 1, posiciones, separacion/1.3)
        return posiciones

    posiciones = calcular_posiciones(nodo)

    for padre, (x, y) in posiciones.items():
        for hijo in padre.hijos:
            xh, yh = posiciones[hijo]
            ax.plot([x, xh], [y - 0.05, yh + 0.05], color='black', linewidth=1.2, zorder=1)

    for n, (x, y) in posiciones.items():
        color = colores.get(n.tipo, '#D7BDE2')
        texto = f"{n.texto}"
        if n.tipo == "operador":
            texto += f"\n({n.tipo})"
            if n.valor is not None:
                texto += f"\n={round(n.valor, 4)}"
        elif n.tipo == "numero":
            texto += f"\n({n.valor})"
        elif n.tipo == "id":
            texto += "\n(id)"
        ax.scatter(x, y, s=2000, color=color, edgecolor='black', zorder=2)
        ax.text(x, y, texto, ha='center', va='center', fontsize=9, weight='bold')

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

def graficar_tabla(tabla, filename):
    filas = []
    for nombre in sorted(tabla.ids.keys()):
        info = tabla.ids[nombre]
        filas.append([
            info.get('nombre'),
            'identificador',
            info.get('tipo', 'desconocido'),
            info.get('valor'),
            info.get('veces', 1),
            info.get('alcance', 'global')
        ])
    for lit in sorted(tabla.literales.keys(), key=lambda x: float(x) if x.replace('.','',1).isdigit() else x):
        info = tabla.literales[lit]
        filas.append([
            lit,
            'literal',
            'numero',
            info.get('valor'),
            info.get('veces', 1),
            '-'  
        ])

    if not filas:
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.axis('off')
        ax.text(0.5, 0.5, "Tabla de símbolos vacia", ha='center', va='center', fontsize=12)
        plt.savefig(filename, dpi=180, bbox_inches='tight')
        plt.close()
        return

    col_labels = ["Simbolo", "Categoria", "Tipo", "Valor", "Veces", "Alcance"]
    nfil = len(filas)
    fig, ax = plt.subplots(figsize=(10, max(2.5, 0.45 * nfil + 1)))
    ax.axis('off')

    tabla_mpl = ax.table(cellText=filas, colLabels=col_labels, cellLoc='center', loc='center')
    tabla_mpl.auto_set_font_size(False)
    tabla_mpl.set_fontsize(10)
    tabla_mpl.scale(1, 1.2)

    for (i, j), cell in tabla_mpl.get_celld().items():
        if i == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2E7D32')  
        else:
            if i % 2 == 0:
                cell.set_facecolor('#F1F8E9')  
            else:
                cell.set_facecolor('white')

    plt.title("Punto 5 - Tabla de Simbolos", fontsize=12)
    plt.savefig(filename, dpi=180, bbox_inches='tight')
    plt.close()

def graficar_texto(heading, texto, filename):
    plt.figure(figsize=(10, 8))
    plt.text(0.02, 0.98, heading + "\n\n" + texto, fontsize=10, va='top', family='monospace')
    plt.axis('off')
    plt.title(heading)
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()

def graficar_conjuntos(first, follow, predict, filename):
    lines = []
    lines.append("FIRST:\n")
    for nt in sorted(first.keys()):
        lines.append(f"  {nt}: {sorted(list(first[nt]))}")
    lines.append("\nFOLLOW:\n")
    for nt in sorted(follow.keys()):
        lines.append(f"  {nt}: {sorted(list(follow[nt]))}")
    lines.append("\nPREDICT  (A -> prod) : conjunto\n")
    for (A, prod), conj in sorted(predict.items(), key=lambda x: (x[0][0], ' '.join(x[0][1]))):
        prod_str = " ".join(prod) if prod else "ε"
        lines.append(f"  {A} -> {prod_str}  : {sorted(list(conj))}")

    texto = "\n".join(lines)
    plt.figure(figsize=(10, 10))
    plt.text(0.01, 0.99, "FIRST / FOLLOW / PREDICT\n\n" + texto, fontsize=9, va='top', family='monospace')
    plt.axis('off')
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()

def extraer_atributos_para_texto(nodo, lines=None, nivel=0):
    if lines is None:
        lines = []
    indent = "  " * nivel
    valor = nodo.valor if getattr(nodo, 'valor', None) is not None else "None"
    lines.append(f"{indent}- {nodo.tipo}: '{nodo.texto}' -> val = {valor}")
    for h in nodo.hijos:
        extraer_atributos_para_texto(h, lines, nivel+1)
    return lines

def ast_a_postfija(nodo, salida=None):
    if salida is None:
        salida = []
    if nodo.hijos:
        for h in nodo.hijos:
            ast_a_postfija(h, salida)
        salida.append(nodo.texto)
    else:
        salida.append(nodo.texto)
    return salida

def procesar_expresion(expr, gramatica, first, follow, predict):
    import re
    nombre = re.sub(r'[^A-Za-z0-9]', '_', expr)[:40]

    tokens = tokenizar(expr)
    ast = construir_ast(tokens)
    tabla = TablaSimbolos()
    recolectar_tabla(ast, tabla)

    try:
        evaluar_ast(ast, tabla)
    except Exception as e:
        print("Aviso durante evaluacion:", e)

    graficar_ast(ast, f"P4_AST_{nombre}.png")
    graficar_tabla(tabla, f"P5_Tabla_{nombre}.png")

    graficar_conjuntos(first, follow, predict, f"P3_Conjuntos_{nombre}.png")

    texto_gram = []
    texto_gram.append("Gramática de atributos (S-atribuida) - atributos sintetizados 'val':\n")
    texto_gram.append("E -> E1 + T    { E.val = E1.val + T.val }")
    texto_gram.append("E -> E1 - T    { E.val = E1.val - T.val }")
    texto_gram.append("E -> T         { E.val = T.val }")
    texto_gram.append("")
    texto_gram.append("T -> T1 * F    { T.val = T1.val * F.val }")
    texto_gram.append("T -> T1 / F    { T.val = T1.val / F.val }")
    texto_gram.append("T -> F         { T.val = F.val }")
    texto_gram.append("")
    texto_gram.append("F -> ( E )     { F.val = E.val }")
    texto_gram.append("F -> num       { F.val = strToNum(num.lexeme) }")
    texto_gram.append("F -> id        { F.val = lookup(id) }")
    texto_gram.append("")
    texto_gram.append("Notas:")
    texto_gram.append("- Atributos sintetizados: E.val, T.val, F.val.")
    

    attr_lines = extraer_atributos_para_texto(ast)
    texto_gram.append(f"Evaluacion real para la entrada: {expr}\n")
    texto_gram.extend(attr_lines)

    texto_gram = "\n".join(texto_gram)
    graficar_texto("Punto 6 - Gramatica de Atributos (con evaluacion real)", texto_gram, f"P6_Gram_{nombre}.png")

    texto_etds = []
    texto_etds.append("Esquema de Traducción Dirigida por la Sintaxis (ETDS):\n")
    texto_etds.append("E -> T E'")
    texto_etds.append("E' -> + T { print('+'); } E' | - T { print('-'); } E' | ε")
    texto_etds.append("")
    texto_etds.append("T -> F T'")
    texto_etds.append("T' -> * F { print('*'); } T' | / F { print('/'); } T' | ε")
    texto_etds.append("")
    texto_etds.append("F -> ( E ) | num { print(num.lexeme); } | id { print(id); }")
    texto_etds.append("")


    postfija = ast_a_postfija(ast)
    postfija_str = " ".join(postfija)
    acciones = []
    for tok in postfija:
        if tok in ['+', '-', '*', '/']:
            acciones.append(f"emitir operador: {tok}")
        else:
            acciones.append(f"emitir operando: {tok}")

    texto_etds.append(f"Entrada: {expr}")
    texto_etds.append(f"Traducción: {postfija_str}")
    texto_etds.append("Acciones generadas (orden postfijo):")
    texto_etds.extend(acciones)

    texto_etds = "\n".join(texto_etds)
    graficar_texto("Punto 7 - ETDS (con traduccion real)", texto_etds, f"P7_ETDS_{nombre}.png")

    print(f"Generadas todas las graficas para la expresion '{expr}'.")

def main():
    if not os.path.exists("gramatica.txt"):
        print("Error: coloque 'gramatica.txt' en el mismo directorio.")
        return
    gramatica = leer_gramatica("gramatica.txt")
    simbolo_ini = list(gramatica.keys())[0]
    first = calcular_first(gramatica)
    follow = calcular_follow(gramatica, simbolo_ini, first)
    predict = calcular_predict(gramatica, first, follow)

    print("Gramatica cargada. .")
    while True:
        expr = input("\nIngrese una expresion (o 'salir'): ").strip()
        if expr.lower() == "salir":
            break
        try:
            procesar_expresion(expr, gramatica, first, follow, predict)
        except Exception as e:
            print("Error al procesar la expresion:", e)

if __name__ == "__main__":
    main()

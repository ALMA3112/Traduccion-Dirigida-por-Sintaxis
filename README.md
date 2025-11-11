# Analizador de Expresiones Aritméticas con EDTS

Sistema de análisis sintáctico y semántico para expresiones aritméticas que implementa un Esquema de Traducción Dirigida por la Sintaxis (EDTS).

## Descripción

Este proyecto implementa un compilador de expresiones aritméticas que realiza análisis léxico, sintáctico y semántico, generando visualizaciones de cada etapa del proceso.

### Características principales

- Análisis basado en gramática libre de contexto (GIC)
- Generación de conjuntos FIRST, FOLLOW y PREDICT
- Construcción de Árbol de Sintaxis Abstracta (AST) decorado
- Tabla de símbolos con identificadores y literales
- Gramática de atributos (S-atribuida)
- Esquema de Traducción Dirigida por la Sintaxis
- Traducción a notación postfija

## Requisitos

```bash
pip install matplotlib
```

## Estructura del Proyecto

```
proyecto/
│
├── Sintaxis.py          # Programa principal
└── gramatica.txt        # Definición de la gramática
```

## Componentes del Proyecto

### **Punto 1: Diseño de la Gramática**
La gramática está definida en `gramatica.txt`:
```
E -> T E'
E' -> + T E' | - T E' | EPS
T -> F T'
T' -> * F T' | / F T' | EPS
F -> ( E ) | numero | id
```

### **Punto 2: Definir Atributos**
Implementado en la clase `NodoAST`:
- Atributo `valor`: almacena valores sintetizados
- Atributo `tipo`: identifica el tipo de nodo (operador, número, id)
- Función `evaluar_ast()`: evalúa los atributos del árbol

### **Punto 3: Calcular los Conjuntos F, S, P**
Funciones implementadas:
- `calcular_first()` → Conjunto FIRST
- `calcular_follow()` → Conjunto FOLLOW
- `calcular_predict()` → Conjunto PREDICT
- **Salida**: `P3_Conjuntos_{expresion}.png`

### **Punto 4: Generar el AST Decorado**
Funciones implementadas:
- `tokenizar()`: análisis léxico
- `construir_ast()`: construcción del árbol
- `graficar_ast()`: visualización del árbol con valores
- **Salida**: `P4_AST_{expresion}.png`

### **Punto 5: Tabla de Símbolos**
Clase `TablaSimbolos`:
- `ids`: diccionario de identificadores
- `literales`: diccionario de literales numéricos
- Función `recolectar_tabla()`: llena la tabla
- **Salida**: `P5_Tabla_{expresion}.png`

### **Punto 6: Gramática de Atributos**
Implementación de gramática S-atribuida:
- Atributos sintetizados (E.val, T.val, F.val)
- Función `extraer_atributos_para_texto()`: muestra la evaluación
- **Salida**: `P6_Gram_{expresion}.png`

### **Punto 7: Generar el EDTS**
Esquema de traducción:
- Función `ast_a_postfija()`: traduce a notación postfija
- Acciones semánticas para cada producción
- **Salida**: `P7_ETDS_{expresion}.png`

## Uso

### Ejecución básica

```bash
python Sintaxis.py
```

### Ejemplo de uso

```
Gramática cargada. .

Ingrese una expresion (o 'salir'): 3 + 5 * 2

Generadas todas las graficas para la expresion '3 + 5 * 2'.
```
### Salida generada

Para cada expresión se generan 5 imágenes:

1. **P3_Conjuntos_*.png** - Conjuntos FIRST, FOLLOW y PREDICT
   
   ![imagen1](https://github.com/ALMA3112/Traduccion-Dirigida-por-Sintaxis/blob/main/Imagenes/P3_Conjuntos_3___5___2.png)
   
2. **P4_AST_*.png** - Árbol de Sintaxis Abstracta decorado
   
   ![imagen2](https://github.com/ALMA3112/Traduccion-Dirigida-por-Sintaxis/blob/main/Imagenes/P4_AST_3___5___2.png)
   
3. **P5_Tabla_*.png** - Tabla de símbolos

   ![imagen3](https://github.com/ALMA3112/Traduccion-Dirigida-por-Sintaxis/blob/main/Imagenes/P5_Tabla_3___5___2.png)

4. **P6_Gram_*.png** - Gramática de atributos con evaluación

   ![imagen4](https://github.com/ALMA3112/Traduccion-Dirigida-por-Sintaxis/blob/main/Imagenes/P6_Gram_3___5___2.png)

5. **P7_ETDS_*.png** - Esquema de traducción y notación postfija

   ![imagen5](https://github.com/ALMA3112/Traduccion-Dirigida-por-Sintaxis/blob/main/Imagenes/P7_ETDS_3___5___2.png)

   
### Operadores soportados

- Suma: `+`
- Resta: `-`
- Multiplicación: `*`
- División: `/`
- Paréntesis: `(` `)`

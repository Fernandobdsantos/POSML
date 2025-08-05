"""Colar e rodar o código da sua API (TODAS AS ROTAS GERAM TABELAS)"""
import os
import pandas as pd
# render_template_string usado para criar a página HTML
from flask import Flask, jsonify, request, render_template_string
from pyngrok import ngrok
from snowflake.connector import connect
from functools import lru_cache

""" Configuração da Aplicação Flask """

app = Flask(__name__)

# --- Credenciais e Conexão com o Snowflake - PONTO CRÍTICO ---
SNOWFLAKE_CONFIG = {
    "user": "fernando_bastos",
    "password": "Tayane11031997",
    "account": "ZAPPZJT-RCB40816",
    "warehouse": "COMPUTE_WH",
    "database": "DB_SCRAPE",
    "schema": "SC_SCRAPE"
}

# --- NOME DA TABELA NO SNOWFLAKE ---
SNOWFLAKE_TABLE = "TB_BOOKS_TO_SCRAPE"

# ------------------------------------------------------------------- #
# --- CÓDIGO HTML CRIADO NO CHAT GPT ---
# ------------------------------------------------------------------- #

# Template principal para exibir listas de dados em uma tabela
HTML_TABLE_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; }
        h1 { color: #333; text-align: center; margin-bottom: 25px;}
        table { width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); background-color: #fff; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; border-bottom: 1px solid #ddd; text-align: left; }
        thead { background-color: #007bff; color: white; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.05em;}
        tr:nth-child(even) { background-color: #f8f9fa; }
        tr:hover { background-color: #e9ecef; }
        .container { max-width: 1200px; margin: auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);}
        p.error { text-align: center; color: #721c24; background-color: #f8d7da; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px;}
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        {% if data %}
            <table>
                <thead>
                    <tr>
                        {% for header in headers %}
                            <th>{{ header }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row in data %}
                    <tr>
                        {% for header in headers %}
                            <td>{{ row.get(header.replace(' ', '_').lower(), '') }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p class="error">Nenhum dado encontrado para os critérios fornecidos.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# Template para a página de estatísticas gerais
HTML_OVERVIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estatísticas Gerais</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; }
        h1, h2 { color: #333; text-align: center; }
        .container { max-width: 800px; margin: auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);}
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; text-align: center;}
        .stat-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;}
        .stat-card h3 { margin-top: 0; color: #007bff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
        thead { background-color: #007bff; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Estatísticas Gerais</h1>
        {% if stats %}
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total de Livros</h3>
                    <p>{{ stats.total_books }}</p>
                </div>
                <div class="stat-card">
                    <h3>Preço Médio</h3>
                    <p>£ {{ "%.2f"|format(stats.average_price) }}</p>
                </div>
            </div>
            <h2>Distribuição por Rating</h2>
            <table>
                <thead><tr><th>Rating</th><th>Quantidade de Livros</th></tr></thead>
                <tbody>
                    {% for item in stats.rating_distribution %}
                    <tr><td>{{ item.rating }}</td><td>{{ item.count }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p>Não foi possível carregar as estatísticas.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# --- conexão Snowflake ---
def get_snowflake_connection():
    """Estabelece uma conexão com o Snowflake."""
    try:
        return connect(**SNOWFLAKE_CONFIG)
    except Exception as e:
        print(f"Erro ao conectar ao Snowflake: {e}")
        return None

@lru_cache(maxsize=32)
def query_snowflake(query):
    """Executa uma consulta no Snowflake e retorna um DataFrame Pandas."""
    conn = get_snowflake_connection()
    if not conn:
        return pd.DataFrame()

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        df = cursor.fetch_pandas_all()
        # Garante que os nomes das colunas fiquem minusculo para o template
        df.columns = df.columns.str.lower()
        return df
    except Exception as e:
        print(f"Erro ao executar a consulta no Snowflake: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# --- Endpoints da API (TODOS RETORNAM HTML) ---
# Inicio da rota

@app.route("/")
def index():
    """Página inicial com links para todas as visualizações."""
    try:
        public_url = ngrok.get_tunnels()[0].public_url
        links_html = f"""
        <h1>API de Livros - Visualizações</h1>
        <p>Use os links abaixo para visualizar os dados em tabelas:</p>
        <ul>
            <li><a href="{public_url}/stats/overview">Estatísticas Gerais</a></li>
            <li><a href="{public_url}/stats/categories">Estatísticas por Categoria</a></li>
            <li><a href="{public_url}/books/all">Ver Todos os Livros</a></li>
            <li><a href="{public_url}/books/top-rated?limit=10">Top 10 Livros Mais Bem Avaliados</a></li>
        </ul>
        <p>Você também pode usar os endpoints com parâmetros, como:</p>
        <ul>
            <li><code>{public_url}/books/price-range?min=10&max=20</code></li>
            <li><code>{public_url}/books/search?category=Music</code></li>
        </ul>
        """
        return links_html
    except IndexError:
        return "API de Livros iniciando, o túnel do ngrok ainda não está pronto."

@app.route('/stats/overview')
def get_overview_stats():
    """Retorna uma página HTML com as estatísticas gerais."""
    query = f"""
    SELECT
        COUNT(*) as total_books,
        rating,
        COUNT(*) as rating_count
    FROM {SNOWFLAKE_TABLE}
    GROUP BY rating
    ORDER BY rating DESC
    """
    df = query_snowflake(query)

    if df.empty:
        return render_template_string(HTML_OVERVIEW_TEMPLATE, stats=None)

    total_books = int(df['total_books'].sum())
    avg_price_query = f"SELECT AVG(price::FLOAT) as avg_price FROM {SNOWFLAKE_TABLE}"
    avg_df = query_snowflake(avg_price_query)
    average_price = round(float(avg_df['avg_price'].iloc[0]), 2) if not avg_df.empty else 0.0

    rating_dist = df.rename(columns={"rating_count": "count"}).to_dict('records')

    result = {
        "total_books": total_books,
        "average_price": average_price,
        "rating_distribution": rating_dist
    }
    return render_template_string(HTML_OVERVIEW_TEMPLATE, stats=result)

@app.route('/stats/categories')
def get_category_stats():
    """Retorna uma tabela HTML com estatísticas por categoria."""
    query = f"""
    SELECT
        category,
        COUNT(*) as book_count,
        AVG(price::FLOAT) as avg_price,
        MIN(price::FLOAT) as min_price,
        MAX(price::FLOAT) as max_price
    FROM {SNOWFLAKE_TABLE}
    GROUP BY category
    ORDER BY book_count DESC
    """
    df = query_snowflake(query)
    headers = ["Category", "Book Count", "Avg Price", "Min Price", "Max Price"]
    return render_template_string(HTML_TABLE_TEMPLATE, title="Estatísticas por Categoria", headers=headers, data=df.to_dict('records'))

@app.route('/books/all')
def view_all_books_table():
    """Busca todos os livros e os exibe em uma tabela HTML."""
    query = f"SELECT id, title, price, rating, category, availability FROM {SNOWFLAKE_TABLE}"
    df = query_snowflake(query)
    headers = ["ID", "Title", "Price", "Rating", "Category", "Availability"]
    return render_template_string(HTML_TABLE_TEMPLATE, title="Catálogo de Livros ", headers=headers, data=df.to_dict('records'))

@app.route('/books/top-rated')
def get_top_rated_books():
    """Retorna uma tabela HTML com os livros mais bem avaliados."""
    limit = request.args.get('limit', 10, type=int)
    query = f"SELECT title, price, rating, availability, category FROM {SNOWFLAKE_TABLE} ORDER BY rating DESC, price ASC LIMIT {limit}"
    df = query_snowflake(query)
    headers = ["Title", "Price", "Rating", "Availability", "Category"]
    return render_template_string(HTML_TABLE_TEMPLATE, title=f"Top {limit} Livros Mais Bem Avaliados", headers=headers, data=df.to_dict('records'))

@app.route('/books/price-range')
def get_books_by_price_range():
    """Retorna uma tabela HTML com livros em uma faixa de preço."""
    min_price = request.args.get('min', type=float)
    max_price = request.args.get('max', type=float)

    if min_price is None or max_price is None:
        return "<p>Erro: Parâmetros 'min' e 'max' são obrigatórios.</p>", 400

    query = f"SELECT title, price, rating, availability, category FROM {SNOWFLAKE_TABLE} WHERE price::FLOAT BETWEEN {min_price} AND {max_price} ORDER BY price ASC"
    df = query_snowflake(query)
    headers = ["Title", "Price", "Rating", "Availability", "Category"]
    return render_template_string(HTML_TABLE_TEMPLATE, title=f"Livros com Preço entre £{min_price} e £{max_price}", headers=headers, data=df.to_dict('records'))

@app.route('/books/search')
def search_books():
    """Retorna uma tabela HTML com os resultados da busca."""
    title_q = request.args.get('title', default="", type=str).lower().strip()
    category_q = request.args.get('category', default="", type=str).lower().strip()

    if not title_q and not category_q:
        return "<p>Erro: Forneça pelo menos um critério de busca: 'title' ou 'category'.</p>", 400

    base_query = f"SELECT title, price, rating, availability, category FROM {SNOWFLAKE_TABLE} WHERE 1=1"
    filters = []
    if title_q:
        filters.append(f" AND LOWER(title) LIKE '%{title_q}%'")
    if category_q:
        filters.append(f" AND LOWER(category) LIKE '%{category_q}%'")

    query = base_query + "".join(filters) + " ORDER BY rating DESC, price ASC LIMIT 100"
    df = query_snowflake(query)
    headers = ["Title", "Price", "Rating", "Availability", "Category"]
    return render_template_string(HTML_TABLE_TEMPLATE, title=f"Resultados da Busca", headers=headers, data=df.to_dict('records'))


# --- Bloco de Execução Principal - Necessário usar o token do NGROK - PRONTO CRITICO---
if __name__ == '__main__':
  NGROK_AUTH_TOKEN = "2zE5u5sZGpav3hOX4fMwEpuKOUe_5YFq6Vs3Ypym6Y8Fmoum2"
    # dominio fixo registrado no ngrok
  NGROK_STATIC_DOMAIN = "hagfish-delicate-jaybird.ngrok-free.app"
  os.environ["NGROK_AUTH_TOKEN"] = NGROK_AUTH_TOKEN
  try:
        # ... (desconectar túneis antigos)
    ngrok.set_auth_token(os.environ["NGROK_AUTH_TOKEN"])
        # Passe o parâmetro 'domain' para a função connect
    public_url = ngrok.connect(5000, domain=NGROK_STATIC_DOMAIN) # <--- CRIA UM TÚNEL ESTÁTICO
    print(f"✅ API disponível em: {public_url}")
    app.run(port=5000)
  except Exception as e:
    print(f"❌ Ocorreu um erro ao iniciar o ngrok ou o Flask: {e}")
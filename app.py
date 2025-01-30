from flask import Flask, request, jsonify, render_template
import sqlite3
import openai
import os
import logging
from flask_cors import CORS  # Enable frontend-backend communication

logging.basicConfig(level=logging.DEBUG)

# Set up OpenAI API key
openai.api_key = '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'  # Ensure API key is set via environment variable

# openai.api_key = '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'
# Set up Flask app
app = Flask(__name__)
CORS(app)  # Allow frontend access

# Path to the SQLite database
db_path = 'podcasts.db'

print("hello from top")

# Function to query the database
def query_database(query):
    try:
        print("Executing query:", query)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This ensures results are returned as dictionaries
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if rows:
            column_names = rows[0].keys()  # Extract column names
            results = [dict(row) for row in rows]  # Convert each row into a dictionary
            return {"columns": column_names, "data": results}
        else:
            return {"columns": [], "data": []}
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return {"error": f"Database error: {str(e)}"}

def generate_sql_from_question(question):
    try:
        prompt = f"""
        You are an assistant tasked with generating SQL queries for the following table structure:

        Table name: podcasts  
        Columns:  
        - id (INTEGER PRIMARY KEY)  
        - title (TEXT)  
        - language (TEXT)  
        - avg_rating (REAL)  
        - total_ratings (INTEGER)  
        - genre_names (TEXT)  
        - website (TEXT)
        - author_name (TEXT)
        - owner_name (TEXT)
        - owner_email (TEXT)
        - rss_url (TEXT)
        - audience_size (INTEGER)
        - itunes_id (INTEGER)
        - copyright (TEXT)

        Given the following question, generate the corresponding SQL query with no explanation. The question may contain typos, incomplete words, or partial terms—interpret them and generate the most accurate SQL query based on the intent. also include the table names if there is any
        no sql written in the start and also no commas
        Genre names in my table are like 
        Health, Podcasts, Fitness, Science, Animation, Manga, Leisure, Comedy, Fiction, Drama, Interviews, News, Earth Sciences, Entertainment News, Fashion, Beauty, Arts, Business, Film History, TV, Film, Education, Self-Improvement, How To, Pets, Animals, Kids, Family, Social Sciences, Society, Culture, Stories for Kids, Visual Arts, Basketball, Books, Careers, Christianity, Religion, Spirituality, Documentary, Design, Government, History, Hobbies, Improv, Investing, Islam, Judaism, Marketing, Medicine, Music, Non-Profit, Philosophy, Politics, Relationships, Sexuality, Soccer, Sports, Stand-Up, Technology, Tech News, Wrestling, Personal Journals, Natural Sciences, News Commentary, Video Games, Health & Fitness, Alternative Health, Management, Mental Health, Home & Garden, Business News, Daily News, Film Interviews, Places & Travel, True Crime, Performing Arts, Parenting, Food, Automotive, Comedy Interviews, Music Commentary, Film Reviews, Courses, Religion & Spirituality, Science Commentary, Entrepreneurship, Crafts
        and hundreds more categories
        Each cell may contain many or even any one of them, so search within the  cell too
        language in my tables are as "en", "fr", "id", "en-us", "ko-kr", "pt-br", "in", "fi", "de", "es-do" and so on
        Question: {question}
        show only first 500 results"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Error generating SQL: {str(e)}")
        return {"error": f"Error generating SQL: {str(e)}"}

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "Question cannot be empty."}), 400

        sql_query = generate_sql_from_question(question)
        if isinstance(sql_query, dict) and "error" in sql_query:
            return jsonify(sql_query), 500

        query_results = query_database(sql_query)
        if isinstance(query_results, dict) and "error" in query_results:
            return jsonify(query_results), 500

        return jsonify({
            "question": question,
            "sql_query": sql_query,
            "columns": query_results["columns"],
            "results": query_results["data"]
        })
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

# Route to serve the frontend page
@app.route('/')
def index():
    return render_template('index.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

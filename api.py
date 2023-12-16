from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from newsapi import NewsApiClient
from dotenv import load_dotenv
import os
import json
import difflib

load_dotenv()

newsapi = NewsApiClient(api_key=os.getenv("API_KEY"))

app = Flask(__name__)
CORS(app)

client = MongoClient(
        host=os.getenv('MONGO_HOST'),
        port=27017,
        username=os.getenv('MONGO_INITDB_ROOT_USERNAME'),
        password=os.getenv('MONGO_INITDB_ROOT_PASSWORD'),
        authSource=os.getenv('MONGO_AUTH_SRC')
    )
db = client[os.getenv('MONGO_INITDB_DATABASE')]
collection_article = db[os.getenv('MONGO_COLLECTION')]

@app.route('/')
def test_server():
    return "Welcome to the server!"

@app.route('/insert-article',methods=['POST'])
def input_article():
    # print("hello world")
    data = request.json  # Assuming the data is sent in JSON format

    # Extracting data from the request
    input_sumber = data.get('sumber')
    input_author = data.get('penulis')
    input_title = data.get('judul')
    input_date = data.get('tanggal_terbit')
    input_description = data.get('deskripsi')
    # input_source = data.get('sumber')
    # input_category = data.get('kategori')
    
    input_content = data.get('konten-artikel')

    # Creating a document to insert into the collection
    article_data = {
        'source':input_sumber,
        'author': input_author,
        'title': input_title,
        'description': input_description,
        'publishedAt': input_date,
        # 'sumber': input_source,
        # 'kategori': input_category,
        
        'content': input_content
    }

    # Inserting data into the MongoDB collection
    result = collection_article.insert_one(article_data)

    if result.inserted_id:
        return jsonify({
            'status' : 200,
            'message': "ok"}
            )
    else:
        return jsonify({
            'status' : 500,
            'message': 'Failed to insert article'
            })

def get_article():
    print("hellow")

@app.route('/search-article',methods=['POST','GET'])
def search_article():
    query = request.args.get('query')

    # query = 
    all_articles = newsapi.get_everything(q=query)

    # Assuming you're interested in the first matching title
   

    articles_json = json.dumps(all_articles, indent=4)
    articles_list = list((json.loads(articles_json))['articles'])

    emp = []
    # print(type(articles_list))
    for i in range(len(articles_list)):
        # print(articles_list[i], "\n")
        items_list = articles_list[i]
        new_date = items_list['publishedAt'].split("T")
        data_new = {
            'author' : items_list['author'],
            'title' : items_list['title'],
            'description' : items_list['description'],
            'url' : items_list['url'],
            'publishedAt' : new_date[0],
            'content' : items_list['content']
        }
        emp.append(data_new)

    mongo_data = collection_article.find()
    for data in mongo_data:
        new_data = {
                'author': data.get('author'),
                'title': data.get('title'),
                'description': data.get('description'),
                'url': data.get('url'),
                'publishedAt': data.get('publishedAt'),
                'content': data.get('content')
            }

        emp.append(new_data)

    title_only = []
    for x in range(len(emp)):
        title_only.append(emp[x]['title'].lower())

    threshold = 0.3
    for titles in title_only:
        sim = difflib.SequenceMatcher(None, titles, query)
        similarity_ratio = sim.ratio()

        for article in emp:
                if article['title'].lower() == titles:
                    if similarity_ratio > threshold : 
                        article['similarity_ratio'] = similarity_ratio
                    else : 
                        article['similarity_ratio'] = None
    # print(emp[2])
    emp = sorted(emp, key=lambda x: x.get('similarity_ratio', 0), reverse=True)   

    with app.app_context():
        
        response_data = {
            "status": 200,
            "data": emp
        }

    return jsonify(response_data)
    
    


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)

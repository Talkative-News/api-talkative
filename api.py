from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from newsapi import NewsApiClient
from dotenv import load_dotenv
import os
import json
import difflib
from google.cloud import firestore
from werkzeug.utils import secure_filename


load_dotenv()

app = Flask(__name__)
CORS(app)
newsapi = NewsApiClient(api_key=os.getenv("API_KEY"))

UPLOAD_FOLDER = '/Users/christinaandrea/api-talkative/UPLOAD_IMG/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

db = firestore.Client.from_service_account_json('./talkative-admin-sdk.json')
@app.route('/admin-data', methods=['GET'])
def get_admin_data():
    
    admin_data = []
    docs = db.collection('admin').stream()
    for doc in docs: 
        admin_data.append({doc.id: doc.to_dict()})

    return jsonify({'status': 200, 'data': admin_data})

@app.route('/insert-data-admin', methods=['POST'])
def insert_data():
    
        data = request.json  # Assuming data is sent in JSON format

        # Extracting data from the request
        name = data.get('name')
        email = data.get('email')
        # password = data.get('password')
        role = data.get('role')
        # Add more fields as needed
        
        # Creating a document to insert into the collection
        doc_ref = db.collection('admin').document()  # Replace 'your_collection' with your actual collection name
        doc_ref.set({
            'name': name,
            'email': email,
            # 'password': password,
            'role' : role
            # Add more fields here
        })

        return jsonify({'status': 'success', 'message': 'Data inserted successfully'}), 200

@app.route('/insert-article',methods=['POST'])
def input_article():
    # print("hello world")
    data = request.json # Assuming the data is sent in JSON format
    image_file = request.files['image']
    # Extracting data from the request
    input_sumber = data.get('sumber')
    input_author = data.get('penulis')
    input_title = data.get('judul')
    input_url = data.get('url')
    input_date = data.get('tanggal_terbit')
    input_description = data.get('deskripsi')
    # input_source = data.get('sumber')
    input_category = data.get('kategori')
    
    input_content = data.get('konten-artikel')

    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            # Storing the image path in the MongoDB document
            image_path = filepath  # You can also store the relative path or filename
    else:
        image_path = ''
    # Creating a document to insert into the collection
    article_data = {
        'source':input_sumber,
        'author': input_author,
        'title': input_title,
        'description': input_description,
        'publishedAt': input_date,
        'url': input_url,
        'urlToImg': image_path,
        'category' : input_category,
        'content': input_content
    }

    # Inserting data into the MongoDB collection
    result = collection_article.insert_one(article_data)

    return jsonify({
            'status' : 200,
            'message': "ok"}
            )
  
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
            'urlToImg':items_list['urlToImage'],
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
                'urlToImg' : data.get('urlToImg'),
                'publishedAt': data.get('publishedAt'),
                'category' : data.get('category'),
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

@app.route('/get-data-pagination', methods=['GET'])
def get_by_pagination():
    query = request.args.get('query')

    # Perform newsapi search and fetch articles
    all_articles = newsapi.get_everything(q=query)
    articles_list = all_articles['articles'] if 'articles' in all_articles else []

    # Prepare articles from NewsAPI
    emp = []
    for item in articles_list:
        new_date = item['publishedAt'].split("T")
        data_new = {
            'author' : item['author'],
            'title' : item['title'],
            'description' : item['description'],
            'url' : item['url'],
            'urlToImg':item['urlToImage'],
            'publishedAt' : new_date[0],
            'content' : item['content']
        }
        emp.append(data_new)

    # Retrieve articles from MongoDB
    mongo_data = collection_article.find()
    for data in mongo_data:
        new_data = {
                'author': data.get('author'),
                'title': data.get('title'),
                'description': data.get('description'),
                'url': data.get('url'),
                'urlToImg' : data.get('urlToImg'),
                'publishedAt': data.get('publishedAt'),
                'category' : data.get('category'),
                'content': data.get('content')
        }
        emp.append(new_data)

    # Calculate similarity ratio
    threshold = 0.3
    for article in emp:
        sim = difflib.SequenceMatcher(None, article['title'].lower(), query.lower())
        similarity_ratio = sim.ratio()
        article['similarity_ratio'] = similarity_ratio if similarity_ratio > threshold else None

    # Pagination logic
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_data = emp[start_idx:end_idx]

    # Prepare response with paginated data
    response_data = {
        "status": 200,
        "data": paginated_data
    }

    return jsonify(response_data)

@app.route('/get-data-db', methods=['GET'])
def get_data_db():

    collect = collection_article.find()
    emp_collection = []
    for data in collect:
        collection_data = {
                'author': data.get('author'),
                'title': data.get('title'),
                'description': data.get('description'),
                'url': data.get('url'),
                'urlToImg' : data.get('urlToImg'),
                'publishedAt': data.get('publishedAt'),
                'category' : data.get('category'),
                'content': data.get('content')
        }
        emp_collection.append(collection_data)

    response_data = {
        "status": 200,
        "data": emp_collection
    }

    return jsonify(response_data)

@app.route('/get-length-news', methods=['GET'])
def get_length_news():
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
            'urlToImg':items_list['urlToImage'],
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
                'urlToImg' : data.get('urlToImg'),
                'publishedAt': data.get('publishedAt'),
                'category' : data.get('category'),
                'content': data.get('content')
            }

        emp.append(new_data)

    news_length = len(emp)

    response_data = {
        "status": 200,
        "data": news_length
    }

    return response_data


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)

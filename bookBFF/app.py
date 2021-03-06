
# IMPORTS 

from flask import Flask, request, json
import requests
app = Flask(__name__)
app.url_map.strict_slashes = False


# CONSTANTS 

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 80

RECC_CIRCUIT_BREAKER_HOST = 'http://10.100.236.41:83/books'
BOOK_SERVICE_HOST = 'http://10.100.144.244:3002/books'
VALID_AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJLUkFNRVJTIiwibHVscyI6IktSQU1FUlMiLCJjcmVhdGVkIjoxNjE3MjMwNzUxMzIwLCJyb2xlcyI6W10sImlzcyI6InRjdS5nb3YuYnIiLCJlaW8iOiIxMC4xMDAuMTkyLjUxIiwibnVzIjoiSk9BTyBBTkRPTklPUyBTUFlSSURBS0lTIiwibG90IjoiU2VnZWMiLCJhdWQiOiJPUklHRU1fUkVRVUVTVF9CUk9XU0VSIiwidHVzIjoiVENVIiwiY3VscyI6MjI1LCJjb2QiOjIyNSwiZXhwIjoxNjE3MjczOTUxMzIwLCJudWxzIjoiSk9BTyBBTkRPTklPUyBTUFlSSURBS0lTIn0.qtJ0Sf2Agqd_JmxGKfqiLw8SldOiP9e21OT4pKC8BqdXrJ0plqOWHf0hHbwQWp-foEBZzAUWX0J-QHtLyQ7SRw'


# VALIDATIONS 

def responseIfInvalidRequest(req):
  agentHeader = req.headers.get('User-Agent', None)
  if agentHeader == None:
    response = app.response_class(
      response=json.dumps({'message': 'User-Agent header required.'}),
      status=400,
      mimetype='application/json'
    )
    return response
  
  auth = req.headers.get('Authorization', None)
  if auth == None or auth != VALID_AUTH_TOKEN:
    response = app.response_class(
      response=json.dumps({'message': 'Valid Authorization Token required.'}),
      status=401,
      mimetype='application/json'
    )
    return response
  
  return None

def isMobileAgent(req):
  agentHeader = req.headers.get('User-Agent', None)
  
  if 'Mobile' in agentHeader:
    return True

  return False

  
# ROUTES 

@app.route('/books/<isbn>/related-books', methods=['GET'])
def getBookReccomendation(isbn=None):
  response = responseIfInvalidRequest(request)
  if response: 
    return response

  path = '/isbn/{}'.format(isbn)
  esResult = requests.get(BOOK_SERVICE_HOST+path)
  bookJson = esResult.json()

  # ES Book not found
  if esResult.status_code == 404:
    return getResponseFor(esResult) 
  
  # ES Book found w/relatedTitles
  if 'relatedTitles' in bookJson:
    return app.response_class(
      response=json.dumps(bookJson['relatedTitles']),
      status=200,
      mimetype='application/json'
    )
  
  # No relatedTitles
  path = '/{}/related-books'.format(isbn)
  breakerRes = requests.get(RECC_CIRCUIT_BREAKER_HOST+path)

  # Reccomendation found
  if breakerRes.status_code == 200: 
    bookJson['relatedTitles'] = breakerRes.json()
    path = '/{}'.format(isbn)
    serviceRes = requests.put(BOOK_SERVICE_HOST+path, data=bookJson)    

  # No Reccomendation found
  if breakerRes.status_code == 204:
    return app.response_class(
      response=json.dumps({}),
      status=204,
      mimetype='application/json'
    )

  return getResponseFor(breakerRes)


@app.route('/books', methods=['POST'])
def addBook():
  response = responseIfInvalidRequest(request)
  if response: 
    return response

  serviceRes = requests.post(BOOK_SERVICE_HOST, data=request.get_json())

  return getResponseFor(serviceRes)


@app.route('/books/<isbn>', methods=['PUT'])
def putBook(isbn=None):
  response = responseIfInvalidRequest(request)
  if response: 
    return response

  path = '/{}'.format(isbn)
  serviceRes = requests.put(BOOK_SERVICE_HOST+path, data=request.get_json())
  
  return getResponseFor(serviceRes)


@app.route('/books/isbn/<isbn>', methods=['GET'])
def getBook(isbn=None):
  response = responseIfInvalidRequest(request)
  if response: 
    return response

  path = '/isbn/{}'.format(isbn)
  serviceRes = requests.get(BOOK_SERVICE_HOST+path)
  
  if isMobileAgent(request):
    returnedCode = serviceRes.status_code
    returnedBody = serviceRes.json()

    if 'genre' in returnedBody and 'non-fiction' == returnedBody['genre']:
      returnedBody['genre'] = 3

      response = app.response_class(
        response=json.dumps(returnedBody),
        status=returnedCode,
        mimetype='application/json'
      )
      return response

  return getResponseFor(serviceRes)


@app.route('/books', methods=['GET'])
def searchBooks():
  response = responseIfInvalidRequest(request)
  if response: 
    return response

  keyword = request.args.get('keyword', '')
  path = '?keyword={}'.format(keyword)
  serviceRes = requests.get(BOOK_SERVICE_HOST+path)

  if serviceRes.status_code == 204:
    return app.response_class(
      response=json.dumps({}),
      status=204,
      mimetype='application/json'
    )
  
  return getResponseFor(serviceRes)

# STATUS ROUTE - for liveness check

@app.route('/status', methods=['GET'])
def getStatus():
  return app.response_class(
    response=json.dumps({}),
    status=200,
    mimetype='application/json'
  )


# HELPERS 

def getResponseFor(serviceRes):
  returnedCode = serviceRes.status_code
  returnedBody = serviceRes.json()

  response = app.response_class(
    response=json.dumps(returnedBody),
    status=returnedCode,
    mimetype='application/json'
  )

  return response


# RUN APP

if __name__ == '__main__':
  print('bookBFF listening @ {}:{}'.format(SERVER_HOST, SERVER_PORT))
  app.run(host=SERVER_HOST, port=SERVER_PORT)
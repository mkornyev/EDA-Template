//################ IMPORTS ################ 

const express = require('express')
const bodyParser = require('body-parser')
const port = 3000

const conn = require('./db-connector')
const esConn = require('./es-connector')
const app = express()

app.use(bodyParser.urlencoded({ extended: true }))
app.use(bodyParser.json())
app.use(bodyParser.raw())


//################ CONSTANTS ################ 

var PRICE_REGEX = /^\d+(\.(\d{2}|0))?$/   // 10 | 10.0 | 10.01 are all valid
const SEARCH_REGEX = /^[a-zA-Z]+$/        // nonempty string caps || lowercase 


//################ BOOK ROUTES ################ 

// Add Book:
app.post('/books', (req, res) => {
  if(!validateBook(req, res)) return
  
  conn.createBook(req.body.ISBN, req.body.title, req.body.Author, req.body.description, req.body.genre, req.body.price, req.body.quantity, () => {
    // If Already Exists
    res.statusCode = 422
    res.json({ message: 'This ISBN already exists in the system.' })
  }, () => {
    // Success
    res.statusCode = 201
    res.location(`${req.headers.host}/books/${req.body.ISBN}`)
    res.json(req.body)
    
    esConn.postBook(req.body.ISBN, req.body) // Update ES
  })
})

// Update Book:
// !!! VALIDATE ADMIN 
app.put('/books/:ISBN', (req, res) => {
  if(!validateBook(req, res)) return
  var oldISBN = req.params.ISBN

  if(oldISBN == req.body.ISBN){
    callToUpdate()
  } else {
    conn.getBook(req.body.ISBN, () => {
      // If Book not found (newISBN)
      callToUpdate()
    }, () => {
      res.statusCode = 422
      res.json({ message: 'The new ISBN already exists in the system.' }) // The logic is inverted — checks whether the NEW isbn exists BEFORE checking the OLD one
    })
  }

  function callToUpdate(){
    conn.updateBook(oldISBN, req.body.ISBN, req.body.title, req.body.Author, req.body.description, req.body.genre, req.body.price, req.body.quantity, () => {
      // If Book not found (oldISBN)
      res.statusCode = 404
      res.json({ message: 'No ISBN Found.' })
    }, () => {
      res.statusCode = 200
      res.json(req.body)

      esConn.putBook(oldISBN, req.body)
    })
  }
})

// Search Books:
app.get('/books', (req, res) => {
  if(!validateSearch(req, res)) return
  var keyword = req.query.keyword

  esConn.searchBooks(keyword, ()=>{
    res.statusCode = 400
    res.json({ message: 'Malformed Input.' })
  }, (esBooks) => {
    if(esBooks.length == 0){ res.statusCode = 204 } 
    else { res.statusCode = 200 }
    res.json(esBooks)
  })
})

// Retrieve Book:
app.get('/books/isbn/:ISBN', (req, res) => {
  var ISBN = req.params.ISBN
  
  esConn.getBook(ISBN, () => {
    // If Book not found
    res.statusCode = 404
    res.json({ message: 'No ISBN Found.' })
  }, (book) => {
    res.statusCode = 200
    res.json( book )
  })
})

// Get Status: Liveness Check
app.get('/status', (req, res) => {
  res.statusCode = 200
  res.json({})
})


//################ VIEW HELPERS ################ 

function validateBook(req, res) {

  if(
    !req.body.ISBN || 
    !req.body.title || 
    !req.body.Author || 
    !req.body.description || 
    !req.body.genre || 
    !req.body.price || 
    !req.body.quantity ||
    !PRICE_REGEX.test(req.body.price) 
  ){
    res.statusCode = 400
    res.json({ message: 'Malformed input.' })
    return false
  }
  return true
}

function validateSearch(req, res) {

  if(
    !req.query.keyword || 
    !SEARCH_REGEX.test(req.query.keyword)
  ){
    res.statusCode = 400
    res.json({ message: 'Malformed input.' })
    return false
  }
  return true
}

//################ =+= ################ 

app.listen(port, () => {
  conn.setRDSConnection()
  console.log(`bookService listening @ http://localhost:${port}`)
})




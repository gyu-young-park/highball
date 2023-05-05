# Highball!
Python Web Framework built for learning purpose

![purpose](https://img.shields.io/badge/purpose-learning-green.svg)
![PyPI](https://img.shields.io/pypi/v/badge.svg)

It's a WSGI framework and can be used with any WSGI application server such as Gunicorn.

It also provides so many features of routes, templates, static files and ORM. Especially ORM has internal sqlite3, so you can make very easy and tiny database logic.

## Installation

```shell
pip install highball
```

# How to use it

### Basic usage:

```python
from highball.api import API
r
app = API()


@app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"


@app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello, {name}"


@app.route("/book")
class BooksResource:
    def get(self, req, resp):
        resp.text = "Books Page"

    def post(self, req, resp):
        resp.text = "Endpoint to create a book"


@app.route("/template")
def template_handler(req, resp):
    resp.body = app.template(
        "index.html", context={"name": "highball", "title": "Best Framework"}).encode()
```

### Unit Tests

The recommended way of writing unit tests is with [pytest](https://docs.pytest.org/en/latest/). There are two built in fixtures
that you may want to use when writing unit tests with highball. The first one is `app` which is an instance of the main `API` class:

```python
def test_route_overlap_throws_exception(app):
    @app.route("/")
    def home(req, resp):
        resp.text = "Welcome Home."

    with pytest.raises(AssertionError):
        @app.route("/")
        def home2(req, resp):
            resp.text = "Welcome Home2."
```

The other one is `client` that you can use to send HTTP requests to your handlers. It is based on the famous [requests](https://requests.readthedocs.io/) and it should feel very familiar:

```python
def test_parameterized_route(app, client):
    @app.route("/{name}")
    def hello(req, resp, name):
        resp.text = f"hey {name}"

    assert client.get("http://testserver/matthew").text == "hey matthew"
```

## Templates

The default folder for templates is `templates`. You can change it when initializing the main `API()` class:

```python
app = API(templates_dir="templates_dir_name")
```

Then you can use HTML files in that folder like so in a handler:

```python
@app.route("/show/template")
def handler_with_template(req, resp):
    resp.html = app.template(
        "example.html", context={"title": "Awesome Framework", "body": "welcome to the future!"})
```

## Static Files

Just like templates, the default folder for static files is `static` and you can override it:

```python
app = API(static_dir="static_dir_name")
```

Then you can use the files inside this folder in HTML files:

```html
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <title>{{title}}</title>

  <link href="/static/main.css" rel="stylesheet" type="text/css">
</head>

<body>
    <h1>{{body}}</h1>
    <p>This is a paragraph</p>
</body>
</html>
```

### Middleware

You can create custom middleware classes by inheriting from the `highball.middleware.Middleware` class and overriding its two methods
that are called before and after each request:

```python
from highball.api import API
from highball.middleware import Middleware


app = API()


class SimpleCustomMiddleware(Middleware):
    def process_request(self, req):
        print("Before dispatch", req.url)

    def process_response(self, req, res):
        print("After dispatch", req.url)


app.add_middleware(SimpleCustomMiddleware)
```

### ORM
You can create table and manipulate table by using python obejct. here are different examples. 

By creating 'Database' object, you can use highball ORM features
```python
from highball.orm import Database

def db():
    DB_PATH = "./test.db"
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = Database(DB_PATH)
    return db
```

You can make table object and set attributes `Column` and `ForeignKey`
```py
from highball.orm import Table, Column, ForeignKey

class Author(Table):
    name = Column(str)
    age = Column(int)
    
class Book(Table):
    title = Column(str)
    published = Column(bool)
    author = ForeignKey(Author)
```
`Author` has attributes of 'name' and 'age'. And `Book` has attributes of 'title', 'published' and 'author', Notice that `Book`'s `author` is 'ForeignKey' so it is connected to `Author` instance

You can create table as the python table instance to database by using 'create' method of 'Database' instance
```py
db.create(Author)
```

And then, you can store the table data in Database by using 'save` method of 'Database' instance
```py
vik = Author(name="Vik Star", age=43)
db.save(vik)
```

You can get all table rows or specific table row by using `all` and `get` of 'Database' instance
```py
authors = db.all(Author)
author_1_from_db = db.get(Author, id=1)
```

Lastly, you can manipulate table data by using `update` and `delete` of 'Database' instance
```py
## update
db.create(Author)
author_instance = Author(name="author_instance", age=23)
db.save(author_instance)

author_instance.age = 43
author_instance.name = "author_instance2"
db.update(author_instance)
## delete
db.delete(Author, id=author_instance.id)
```
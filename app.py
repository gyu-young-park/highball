from api import API

app = API()

@app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"


@app.route("/about")
def about(request, response):
    response.text = "Hello from the ABOUT page"

@app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello, {name}"
    
@app.route("/book")
class BooksResource:
    def get(self, req, resp):
        resp.text = "Books Page"
        
    def post(self, req, resp):
        resp.text = "Endpoint to create a book"
        
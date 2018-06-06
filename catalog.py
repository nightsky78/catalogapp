from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, flash
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests
# Import all the database stuff
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# import the tables from my database class
from cat_db_setup import Base, Category, Item, User

# create the connection to the database
engine = create_engine('postgresql+psycopg2://vagrant:vagrant@192.168.56.3:5432/catalog')

# Bind the class to the physical database
Base.metadata.bind = engine

# Create session to connect to the database.
# Interface sessin
DBSession = sessionmaker(bind=engine)

session = DBSession()
try:
    CLIENT_ID = json.loads(open('../client_secrets.json','r').read())['web']['client_id']
except:
    print("Error loading the client secrets file, go to google get them, and store properly"
          "! See readme.me for details.")
    quit()

# Create instance of this class with the name of the running app as an argument
app = Flask(__name__)

# This defines the path where the application is reachable. If the declarators are stacked on top of each other
# the / redirect to /restaurant and this executes the code in Restaurants menue
# thw URL can contain a variable which the again can be used in the code

# This defines the path where the application is reachable. If the declarators are stacked on top of each other
# the / redirect to /restaurant and this executes the code in Restaurants menue
# thw URL can contain a variable which the again can be used in the code

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('../client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    if not getUserID(login_session['email']):
        createUser(login_session)

    login_session['user_id'] = getUserID(login_session['email'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('Catalog'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    # Create anti-forgery state token this
    # This state token will be generated here and passed to the login template
    # When the login template comes back with the session token, we need to check if its still
    # the same session token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/')
@app.route('/catalog')
def Catalog():
    if 'username' in login_session:
        categories = session.query(Category).all()

        output = render_template('cataloglogin.html', categories=categories)

        return output
    else:
        categories = session.query(Category).all()

        output = render_template('catalog.html', categories=categories)

        return output


@app.route('/catalog/item/add')
def addItem():
    return "This is the catalog add page"

@app.route('/catalog/<int:category>/item')
def showItem(category):
    return "This is the category page with {0}".format(category)

@app.route('/catalog/<int:category>/<int:item>/details')
def showItemDetails(category, item):
    return "This ist the category details page for {0} and {1}".format(category, item)

@app.route('/catalog/<int:category>/<int:item>/edit')
def editItem(category, item):
    return "This ist the category edit page for {0} and {1}".format(category, item)

@app.route('/catalog/<int:category>/<int:item>/delete')
def deleteItem(category, item):
    return "This ist the category delete page for {0} and {1}".format(category, item)

@app.route('/catalog/JSON')
def catalogJson():
    return "This is the jason"

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id

if __name__ == '__main__':
    # The debug True statement ensures that the app is restarted in case there is a code change
#    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
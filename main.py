import os
import uuid
import jwt

from flask import Flask, render_template, request, redirect, jsonify, make_response, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import select

app = Flask(__name__, template_folder="./resources/html")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

app.config['db_images'] = './resources/cats'
app.config['secret_key'] = "QsdaWQEaKDJHASDYasdpo1238ASJDGHa123"

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

class Cat(db.Model):
    """Take data from table and return it in easily serializable format
    Id, Name and Description, Type, Gender and Availability, Image, Colour, Birthday and Date creation of Cat"""
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(200), nullable=False)

    class_type = db.Column(db.String(1), nullable=False)
    gender = db.Column(db.Boolean, nullable=False)  # 0 - мальчик 1 - девочка TODO: сделать проверку, что 0 или 1
    available = db.Column(db.Boolean)  # бронь 0 - забронирован 1 - свободно TODO: сделать проверку, что 0 или 1

    image = db.Column(db.String())

    color = db.Column(db.String(50), nullable=False)  # Окрас

    birthday = db.Column(db.DateTime, nullable=False)  # День рождения
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def serialize(self):
        """Serialization of data
        Return object data in easily serializable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'class_type': self.class_type,
            'gender': 'Male' if self.gender == False else 'Female',
            'available': 'Not available' if self.available == False else 'Available',
            'color': self.color,
            'birthday': self.birthday.strftime('%Y-%m-%d')
        }

    @property
    def serialize_many2many(self):
        """
        Serialization of data 'many to many'
        Return object's relations in easily serializable format.
        NB! Calls many2many's serialize property.
        """
        return [item.serialize for item in self.many2many]


    def __repr__(self):
        """Return string with Id of cat"""
        return '<Cat %r>' % self.id


class Kitty(db.Model):
    """Take data from table
    Id, Mom and Dad, Date creation of Kitty"""
    # маленькое животное
    # id = db.Column(db.Integer, primary_key = True)
    cat_id = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"), primary_key=True)
    mom = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"))
    dad = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"))

    date_created = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        """Return string with id of Kitty"""
        return '<Kitty %r>' % self.id


class User(db.Model):
    """Take data from table
    Id, Name and Surname, Email and phone, Gender, Birthday, City, Date creation of User"""
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)

    gender = db.Column(db.Boolean)  # TODO: сделать проверку, что 0 или 1

    birthday = db.Column(db.DateTime)

    city = db.Column(db.String(50), nullable=False)

    password = db.Column(db.String(50), nullable=False)

    admin = db.Column(db.Boolean, default=False, nullable=False)

    date_created = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        """Return string with id of User"""
        return '<User %r>' % self.id

class Booking(db.Model):
    """Take data from table.
    Id, Cat id, User id, Comment, Date creation of Booking"""
    # маленькое животное
    id = db.Column(db.Integer, primary_key=True)

    cat_id = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    comment = db.Column(db.String(200))

    date_created = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        """Return string with id of Kitty"""
        return '<Kitty %r>' % self.id

class Tokens(db.Model):
    token = db.Column(db.String(500), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))

    def __repr__(self):
        return '<Tokens %r>' % self.id


@app.route("/register", methods=['POST'])
def register():
    """Setting page and path"""
    resp = make_response(redirect('index'))
    if not "first_name" in request.form:
        return resp
    if not "last_name" in request.form:
        return resp
    if not "email" in request.form:
        return resp
    if not "phone_number" in request.form:
        return resp
    if not "city" in request.form:
        return resp
    if not "password" in request.form:
        return resp
    
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone_number = request.form['phone_number']
    gender = request.form['gender']  # TODO: сделать проверку, что 0 или 1
    if gender == 'male':
        gender = 0
    else:
        gender = 1
    birthday = datetime.strptime(request.form['birthday'], "%Y-%m-%d")
    city = request.form['city']
    password = request.form['password']

    user = User(first_name=first_name, last_name=last_name, email=email,
                phone_number=phone_number, gender=gender, birthday=birthday, city=city, 
                password=password
            )

    print(user)
    print(first_name, last_name, email, phone_number, gender, birthday, city)
    try:
        # TODO: навешать логики, если юзер уже создан
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        return resp
    
    encoded_jwt = jwt.encode(
        {
            "first_name": user.first_name, 
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": user.phone_number,
        }, 
        app.config['secret_key'],
        algorithm="HS256"
    )
    token = Tokens.query.filter_by(token=encoded_jwt).one()
    resp.set_cookie('jwt', token.token)

    return resp


@app.route("/login", methods=['POST'])
def login():
    """Setting page and path"""
    resp = make_response(redirect('index'))
    if not "email" in request.form:
        return resp
    if not "password" in request.form:
        return resp
    name = request.form['email']
    password = request.form['password']
    try:
        user =  User.query.filter_by(email=name, password=password).one()
        encoded_jwt = jwt.encode(
            {
                "first_name": user.first_name, 
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
            }, 
            app.config['secret_key'],
            algorithm="HS256"
        )
        try:
            token = Tokens.query.filter_by(token=encoded_jwt).one()
            resp.set_cookie('jwt', token.token)
        except Exception as e:
            token = Tokens(token=encoded_jwt, user_id=user.id)
            try:
                db.session.add(token)
                db.session.commit()
                resp.set_cookie('jwt', token.token)
            except Exception as e:
                print(f'Couldnt insert {e}')
        
        # jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
    except Exception as e:
        print(f'Couldnt insert {e}')
    
    return resp


@app.route("/exit", methods=['GET'])
def exit():
    res = make_response(redirect('index'))
    cookie_val = request.cookies.get("jwt")
    res.set_cookie('jwt', cookie_val, expires=0)
    return res


@app.route("/cats", methods=['GET'])
def cats():
    """Setting page and path"""
    cats = Cat.query.order_by(Cat.class_type).all()
    return render_template('cat.html', cats=cats, title="Наши коты", jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))


@app.route("/cats.json", methods=['GET'])
def cats_json():
    """Setting page and path"""
    cats = Cat.query.order_by(Cat.class_type).all()
    allpets = [cat.serialize for cat in cats]
    return jsonify(allpets)


@app.route("/cat/<int:id>", methods=['GET'])
def cat(id):
    """Setting page and path"""
    cat = Cat.query.filter_by(id=id).first()
    return jsonify(cat.serialize)


@app.route("/admin/cat", methods=['POST'])
def admin_cat_post():
    """Setting page and path"""
    form = request.form
    name = form['name']
    description = form['description']
    class_type = form['class_type']
    available = form['available']  # 0/1
    gender = form['gender']  # 0/1
    color = form['color']
    birthday = form['birthday']
    # image = form['image']

    if gender.lower() == 'male':
        gender = 0
    else:
        gender = 1

    if available.lower() == 'available':
        available = 1
    else:
        available = 0

    birthday = datetime.strptime(birthday, "%Y-%m-%d")

    cat = Cat(name=name, description=description, class_type=class_type,
              available=available, image=bytes([]), gender=gender, color=color,
              birthday=birthday
              )

    print(cat)
    try:
        db.session.add(cat)
        db.session.commit()
        return {"result": "Ok", "id": cat.id}
    except Exception as e:
        return {"result": f'Couldnt insert {e}'}


@app.route("/make_booking", methods=['POST'])
def make_booking():
    """Api handler for booking"""
    
    form = request.form
    cat_id = form['cat_id']
    message = form['message']
    token = request.cookies.get("jwt")
    try:
        token_in_bd = Tokens.query.filter_by(token=token).one()
        user = User.query.filter_by(id=token_in_bd.user_id).one()
        booking = Booking(cat_id=cat_id, user_id = user.id, comment=message)
        db.session.add(booking)
        db.session.commit()
        return {"result": "Ok", "id": booking.id}
    
    except Exception as e:
        return {"result": f'Couldnt insert {e}'}


@app.route("/admin/cat/<int:id>", methods=['GET', 'DELETE', 'UPDATE'])
def admin_cat_change(id):
    """Setting page and path"""
    if request.method == 'GET':
        cat = Cat.query.filter_by(id=id).first()
        return jsonify(cat.serialize)
    elif request.method == 'DELETE':
        cat = Cat.query.filter_by(id=id).delete()
        try:
            db.session.commit()
            return {"result": "Ok"}
        except Exception as e:
            return {"result": f'Couldnt delete {e}'}
    else:
        # Update
        cat = Cat.query.filter_by(id=id).first()
        form = request.get_json()
        name = form['name']
        description = form['description']
        class_type = form['class_type']
        available = form['available']  # 0/1
        gender = form['gender']  # 0/1
        color = form['color']
        birthday = form['birthday']

        if gender.lower() == 'male':
            gender = 0
        else:
            gender = 1

        if available.lower() == 'available':
            available = 1
        else:
            available = 0

        birthday = datetime.strptime(birthday, "%Y-%m-%d")

        cat.name = name
        cat.description = description
        cat.class_type = class_type
        cat.available = available
        cat.gender = gender
        cat.color = color
        cat.birthday = birthday

        try:
            db.session.commit()
            return {"result": "Ok", "id": cat.id}
        except Exception as e:
            return {"result": f'Couldnt insert {e}'}


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_file", methods=['POST'])
def upload_image():
    if 'cat_id' not in request.form or request.form['cat_id'] == "":
        return redirect("admin")
    if 'file' not in request.files:
        return redirect("admin")
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = str(uuid.uuid4())+filename
        save_path = os.path.join(app.config['db_images'],request.form['cat_id'])
        isExist = os.path.exists(save_path)
        if not isExist:
            os.makedirs(save_path)
        file.save(os.path.join(save_path, filename))
    return redirect("admin")

@app.route("/getImages/<int:id>", methods=['GET'])
def get_images(id):
    cat_folder = os.path.join(app.config['db_images'], str(id))

    if not os.path.exists(cat_folder):
        return jsonify({"result":"", "status":"Error"})

    images = os.listdir(cat_folder)
    return jsonify({"result":images, "status":"ok"})

@app.route('/image/<int:cat_id>')
def get_image_thumbnail(cat_id):
    cat_path = app.config['db_images']+"/"+str(cat_id)
    print(cat_path)
    if os.path.exists(cat_path):
        images = os.listdir(cat_path)
        if len(images) == 0:
            return send_from_directory('static', 'images/thumbnail.svg')
        print(images)
        return send_from_directory(cat_path, images[-1])

    return send_from_directory('static', 'images/thumbnail.svg')

@app.route('/image/<int:cat_id>/<path>')
def get_image_direct(cat_id, path):
    return send_from_directory(app.config['db_images']+"/"+str(cat_id), path)

@app.route("/kitty", methods=['GET'])
def kitty():
    """Setting page and path"""
    name = request.cookies.get('userID')
    kitties = Kitty.query.join(Cat, Cat.id == Kitty.cat_id).add_columns(
        Cat.name, Cat.gender, Cat.available, Cat.birthday,
        Cat.description, Cat.class_type, Cat.color
    ).all()

    return render_template('cat.html', cats=kitties, title="Наши детки", jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))


@app.route("/boys", methods=['GET'])
def boys():
    kitties = Kitty.query.join(Cat, Cat.id == Kitty.cat_id).add_columns(
        Cat.name, Cat.gender, Cat.available, Cat.birthday,
        Cat.description, Cat.class_type, Cat.color
    ).filter_by(gender=False).all()

    return render_template('cat.html', cats=kitties, title="Наши мальчики", jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))


@app.route("/girls", methods=['GET'])
def girls():
    kitties = Kitty.query.join(Cat, Cat.id == Kitty.cat_id).add_columns(
        Cat.name, Cat.gender, Cat.available, Cat.birthday,
        Cat.description, Cat.class_type, Cat.color
    ).filter_by(gender=True).all()

    return render_template('cat.html', cats=kitties, title="Наши девочки", jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))


@app.route("/index")
def index():
    """Setting page and path"""
    lang = "ukr"
    return render_template('index.html', jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))

@app.route("/care")
def care():
    """Setting page and path"""
    return render_template('care.html', jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))


@app.route("/")
def landing():
    """Setting page and path"""
    return render_template('landing.html', jwt=request.cookies.get("jwt"), lang=request.cookies.get("lang"))


def all_cats_paths():
    cats = os.listdir(app.config['db_images'])
    final_paths = []
    for i in cats:
        cat_path = os.path.join(app.config['db_images'], i)
        paths = os.listdir(cat_path)

        final_path = [os.path.join("image", i, j) for j in paths]
        for j in final_path: 
            final_paths.append(j)
    return final_paths

@app.route("/gallery")
def gallery():
    """Setting page and path"""
    paths = all_cats_paths()
    return render_template('gallery.html', jwt=request.cookies.get("jwt"), paths=paths, lang=request.cookies.get("lang"))


@app.route("/admin")
def admin_cat():
    """Setting page and path"""
    return render_template('admin_cat.html', lang=request.cookies.get("lang"))


def createdb():
    """Create DB"""
    db.create_all()
    exit()


def fillbd():
    """Filling DB"""
    # todo: добавить картинку
    cat1 = Cat(name="Кузя", description="Первый счастливчик в нашей маленькой воображаемой семье",
               class_type="A", gender=0, available=0, color="red",
               birthday=date(2002, 2, 17)
               )

    cat2 = Cat(name="Ася",
               description="Второй счастливчик в нашей уже не очень маленькой но всё ещё воображаемой семье",
               class_type="A", gender=1, available=0, color="white",
               birthday=date(2003, 12, 17)
               )

    cat3 = Cat(name="Руся", description="Маленькая девочка, родившаяся у наших самопровозглашённых Адама и Евы",
               class_type="B", gender=1, available=1, color="white",
               birthday=date(2004, 12, 17)
               )

    cat4 = Cat(name="Арчи",
               description="Большой мальчик, который чуть не разрушил вселенную своим появлением. Аж на столько дрожали стены от криков Аси",
               class_type="B", gender=0, available=1, color="white",
               birthday=date(2004, 12, 17)
               )

    cat_has_parents1 = Kitty(cat_id=3, mom=2, dad=1)
    cat_has_parents2 = Kitty(cat_id=4, mom=2, dad=1)

    user = User(first_name="Dima", last_name="Dzundza", email="dzun@gm",
                phone_number="+38073354236", gender=0, birthday=date(2002, 2, 17), city="Mykolaiv", 
                password="123123123")

    try:
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.add(cat4)
        db.session.add(cat_has_parents1)
        db.session.add(cat_has_parents2)
        db.session.add(user)
        db.session.commit()
        
    except Exception as e:
        print(f'Couldnt insert {e}')


@app.route("/init")
def init():
    db.create_all()
    fillbd()
    return redirect('/admin')

@app.route("/lang/<language>", methods=['GET'])
def language(language):
    resp = make_response(redirect('/'))
    resp.set_cookie('lang', language)
    return resp

if __name__ == "__main__":
    app.run(debug=True)
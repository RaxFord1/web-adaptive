from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import select

app = Flask(__name__, template_folder="./resources/html")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Cat(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(200), nullable=False)

    class_type = db.Column(db.String(1), nullable=False)
    gender = db.Column(db.Boolean, nullable=False) # 0 - мальчик 1 - девочка TODO: сделать проверку, что 0 или 1
    available = db.Column(db.Boolean) # бронь 0 - забронирован 1 - свободно TODO: сделать проверку, что 0 или 1

    image = db.Column(db.BLOB)

    color = db.Column(db.String(50), nullable=False) # Окрас

    birthday = db.Column(db.DateTime, nullable=False) # День рождения
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Cat %r>' % self.id

class Kitty(db.Model):
    # маленькое животное
    # id = db.Column(db.Integer, primary_key = True)

    cat_id = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"), primary_key = True)
    mom = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"))
    dad = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"))

    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Kitty %r>' % self.id

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    email = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    
    gender = db.Column(db.Boolean) # TODO: сделать проверку, что 0 или 1
    
    birthday = db.Column(db.DateTime)
    
    city = db.Column(db.String(50), nullable=False)

    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.id

class Booking(db.Model):
    # маленькое животное
    id = db.Column(db.Integer, primary_key = True)

    cat_id = db.Column(db.Integer, db.ForeignKey('cat.id', ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    comment = db.Column(db.String(200))

    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Kitty %r>' % self.id

@app.route("/register", methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        gender = request.form['gender'] # TODO: сделать проверку, что 0 или 1
        if gender == 'male':
            gender = 0
        else:
            gender = 1
        birthday = datetime.strptime(request.form['birthday'], "%Y-%M-%d") 
        city = request.form['city']
        
        user = User(first_name=first_name, last_name=last_name, email=email, 
            phone_number=phone_number, gender=gender, birthday=birthday, city=city
        )

        print(user)
        print(first_name, last_name, email, phone_number, gender, birthday, city)
        try:
            # TODO: навешать логики, если юзер уже создан
            db.session.add(user)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f'Couldnt insert {e}'
    
    return render_template('index.html')

@app.route("/login", methods=['POST', 'GET'])
def login():
    
    return render_template('index.html', registered="asd")


@app.route("/cat", methods=['GET'])
def cat():
    cats = Cat.query.order_by(Cat.class_type).all()
    return render_template('cat.html', cats=cats)

@app.route("/kitty", methods=['GET'])
def kitty():
    kitties = Kitty.query.join(Cat, Cat.id == Kitty.cat_id).add_columns(
        Cat.name, Cat.gender, Cat.available, Cat.birthday, 
        Cat.description, Cat.class_type, Cat.color
    ).all()

    return render_template('cat.html', cats=kitties)

@app.route("/index")
def index():
    return render_template('index.html')

@app.route("/")
def landing():
    return render_template('landing.html')

@app.route("/gallery")
def gallery():
    return render_template('gallery.html')




def fillbd():
    # todo: добавить картинку
    cat1 = Cat(name="Кузя", description="Первый счастливчик в нашей маленькой воображаемой семье", 
        class_type="A", gender=0, available=0, color="red", 
        birthday=date(2002, 2, 17)
    )

    cat2 = Cat(name="Ася", description="Второй счастливчик в нашей уже не очень маленькой но всё ещё воображаемой семье", 
        class_type="A", gender=1, available=1, color="white", 
        birthday=date(2003, 12, 17)
    )

    cat3 = Cat(name="Руся", description="Маленькая девочка, родившаяся у наших самопровозглашённых Адама и Евы", 
        class_type="B", gender=1, available=1, color="white", 
        birthday=date(2004, 12, 17)
    )

    cat4 = Cat(name="Арчи", description="Большой мальчик, который чуть не разрушил вселенную своим появлением. Аж на столько дрожали стены от криков Аси", 
        class_type="B", gender=0, available=1, color="white", 
        birthday=date(2004, 12, 17)
    )

    cat_has_parents1 = Kitty(cat_id=3, mom=2, dad=1)
    cat_has_parents2 = Kitty(cat_id=4, mom=2, dad=1)

    user = User(first_name="Dima",last_name="Dzundza",email="dzun@gm",
        phone_number="+38073354236",gender=0,birthday=date(2002, 2, 17),city="Mykolaiv")

    try:
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.add(cat4)
        db.session.add(cat_has_parents1)
        db.session.add(cat_has_parents2)
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f'Couldnt insert {e}'
    
if __name__ == "__main__":
    # fillbd()

    app.run(debug=True)
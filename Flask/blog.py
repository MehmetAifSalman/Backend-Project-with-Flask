from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# KUllanıcı Girişi Decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        
        else:
            flash("Bu Sayfayı Görüntülemek için lütfen giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function


# Kullanıcı Kayıt Formu

class RegisterForm(Form):
    name =StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username =StringField("Kullanıcı Adı",validators=[validators.length(min=5,max=35)])
    email = StringField("E-mail",validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message= "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor...")

    ])
    confirm = PasswordField("Parola Doğurla")

# Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı:")
    password = PasswordField("Parola")

# Makale Form

class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.length(max=100,min=5)])
    content = TextAreaField("Makale İçeriği",validators=[validators.length(min=10)])



app = Flask(__name__)
app.secret_key = "yb_blog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "yb_blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app=app)

@app.route("/")
def index():
    
    return render_template("index.html",numbers= [1,2,3,4,5])

@app.route("/about")
def about():
    return render_template("about.html")

# Makale Sayfası
@app.route("/articals")
def articals():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articals"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articals.html",articles = articles)
    else:
        return render_template("articals.html")


# Register İşlemleri

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name =  form.name.data
        username = form.username.data
        email = form.email.data
        password =  sha256_crypt.encrypt(form.password.data)


        cursor = mysql.connection.cursor()

        sorgu = "INSERT INTO user(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()


        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
    

# Login İşlemi
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()


        sorgu = "SELECT * FROM user where username = %s"

        result = cursor.execute(sorgu,(username,))
    
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuuyor","danger")
            return redirect(url_for("login"))


    return render_template("login.html",form = form)

# Detay Sayfası
@app.route("/artical/<string:id>")
def artical(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articals where id = %s"
    
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        artical = cursor.fetchone()
        return render_template("article.html",artical=artical)

    else:
        return render_template("article.html")
# Logout İşlemi
@app.route("/logout")
def logut():
    session.clear()
    return redirect(url_for("index"))

# Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articals WHERE author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articals = cursor.fetchall()
        return render_template("dashboard.html",articals = articals)
    else:
        return render_template("dashboard.html")
# Makale Ekleme
@app.route("/addarticle",methods = ["GET", "POSt"])
def article():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articals(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla kaydedilmiştir","success")
        return redirect(url_for("dashboard"))


    return render_template("addarticle.html",form = form)


# Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articals where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "DELETE from articals where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))

# Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from articals where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            artical = cursor.fetchone()
            form = ArticleForm()
            form.title.data = artical["title"]
            form.content.data = artical["content"]
            return render_template("update.html",form = form)
    else:
        # Post Request
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "UPDATE articals SET title = %s , content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))


# Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articals where title like'%" +keyword+ "%'"
        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan eklimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articals"))
        else:
            articals = cursor.fetchall()

            return render_template("articals.html",articles = articals)


if __name__ ==  "__main__":
    app.run(debug=True)
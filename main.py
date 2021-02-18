from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL

import requests
import os
from pprint import pprint

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movieinfo.sqlite3"
db = SQLAlchemy(app)

API_KEY = os.environ['API_KEY']
API_ENDPOINT = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&language=en-US&query="
API_ENDPOINT_TAIL = "&page=1&include_adult=false"
TOKEN = os.environ['TOKEN']

IMAGE_URL_HEAD = "https://image.tmdb.org/t/p/w500"


@app.route('/select/<search_title>')
def search_titles(title):
    search_url = API_ENDPOINT + title + API_ENDPOINT_TAIL
    response = requests.get(search_url)
    data = response.json()['results']
    titles = []
    for info in data:
        titles.append(info['original_title'])

    return render_template("select.html", titles=titles)


@app.route('/add-info/<add_title>', methods=['GET', 'POST'])
def add_info(add_title):
    info_form = EditForm()
    if info_form.validate_on_submit():
        url = API_ENDPOINT + add_title + API_ENDPOINT_TAIL
        response = requests.get(url).json()['results'][0]
        img_url = IMAGE_URL_HEAD + response['backdrop_path']
        title = add_title
        description = response['overview']
        year = str(response['release_date']).split('-')[0]
        movie_ranking = response['vote_average']
        new_movie = Movie(title, year, description, info_form.rating.data, movie_ranking, info_form.review.data,
                          img_url)
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=info_form, title=add_title)


class AddForm(FlaskForm):
    title = StringField(label="Title", validators=[DataRequired()])

    submit = SubmitField("Submit")


class EditForm(FlaskForm):
    rating = StringField(label="Rating", validators=[DataRequired()])
    review = StringField(label="Review", validators=[DataRequired()])
    submit = SubmitField("Submit")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(80), nullable=False)
    year = db.Column('year', db.String(80), nullable=False)
    description = db.Column('description', db.String(80), nullable=False)
    rating = db.Column('rating', db.String(80), nullable=False)
    movie_ranking = db.Column('ranking', db.String(80), nullable=False)
    review = db.Column('review', db.String(80), nullable=False)
    img_url = db.Column('img_url', db.String(80), nullable=False)

    def __init__(
            self, title, year, description, rating, ranking, review, img_url
    ):
        self.title = title
        self.year = year
        self.description = description
        self.rating = rating
        self.movie_ranking = ranking
        self.review = review
        self.img_url = img_url


db.create_all()


@app.route("/")
def home():
    return render_template("index.html", movies= db.session.query(Movie).order_by(Movie.rating.desc()).all())


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        return search_titles(title=add_form.title.data)

    return render_template("add.html", form=add_form)


@app.route("/edit/<movie_id>", methods=['GET', 'POST'])
def edit(movie_id):
    edit_form = EditForm()
    movie = Movie.query.filter_by(id=movie_id).first()
    if edit_form.validate_on_submit():
        movie.rating = edit_form.rating.data
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=edit_form, title=movie.title)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Запрос', validators=[DataRequired()])
    submit = SubmitField('Искать')
    submit_yand = BooleanField('Yandex')
    submit_goog = BooleanField('Google')








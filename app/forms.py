from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class PhoneForm(FlaskForm):
    phone = StringField('phone', validators=[DataRequired()], render_kw={"placeholder": "Введите номер телефона"})


class ConfirmationForm(FlaskForm):
    code = StringField('confirmation code', validators=[DataRequired()], render_kw={"placeholder": "Введите полученный код"})


class AddChannelsForm(FlaskForm):
    incoming = StringField(validators=[DataRequired()])
    outgoing = StringField(validators=[DataRequired()])

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class PhoneForm(FlaskForm):
    phone = StringField('phone', validators=[DataRequired()])


class ConfirmationForm(FlaskForm):
    code = StringField('confirmation code', validators=[DataRequired()])


class AddChannelsForm(FlaskForm):
    incoming = StringField(validators=[DataRequired()])
    outgoing = StringField(validators=[DataRequired()])

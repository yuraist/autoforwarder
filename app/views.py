from flask import render_template, redirect, url_for, session, request

from app import app, db, monitor, q
from app.forms import PhoneForm, ConfirmationForm, AddChannelsForm
from app.models import ChannelChain


@app.before_request
def check_authorization():
    if request.endpoint != 'login' and request.endpoint != 'confirm':
        if not monitor.check_auth():
            # Try to connect to the existing TelegramClient session
            phone = session.get('phone', None)
            if phone is not None:
                # Send code and receive result.
                # True if the code has been sent and an error string if a query caught an error
                code_sent = monitor.send_code(phone=phone)

                # Check for errors
                if code_sent is True:
                    return redirect(url_for('confirm'))
                elif code_sent == 'User is authorized':
                    return redirect(url_for('index'))
                else:
                    redirect(url_for('login'))

            if request.endpoint != 'ask':
                return redirect(url_for('ask'))


@app.route('/')
def index():
    if not monitor.check_auth():
        return redirect(url_for('login'))

    # Get the channel chain list
    chains = monitor.get_chains()

    # Try to get user information
    try:
        user = monitor.client.get_me().to_dict()
    except Exception as e:
        return render_template('index.html', error=str(e))

    return render_template('index.html', chains=chains, user=user)


@app.route('/ask')
def ask():
    html = '<a href="/login">Авторизоваться</a>'
    return html


def background_task(phone):
    monitor.start_monitoring(phone=phone)


@app.route('/start_work')
def start_work():
    try:
        # Begin a new asynchronous job
        phone = session.get('phone', None)
        job = q.enqueue_call(func=background_task, args=(phone,), timeout='10000h')

        print(f'{job.get_id()} has been started with phone: {phone}')
    except Exception as e:
        return redirect(url_for('index', error=str(e)))

    # Redirect to the main page
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = PhoneForm()
    if form.validate_on_submit():
        # Get a phone number from the POST-request
        phone = form.phone.data

        # Send code and receive result. True if the code has been sent and an error string if a query caught an error
        code_sent = monitor.send_code(phone=phone)

        # Check for errors
        if code_sent is True:
            return redirect(url_for('confirm'))
        elif code_sent == 'User is authorized':
            # Save the phone into the session
            session['phone'] = phone
            return redirect(url_for('index'))
        else:
            return render_template('login.html', form=form, error=code_sent)

    # Render the login template with the PhoneForm()
    return render_template('login.html', form=form)


@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    form = ConfirmationForm()
    if form.validate_on_submit():
        code = int(form.code.data)

        # Confirm the code
        try:
            monitor.confirm(code=code)
            return redirect(url_for('index'))
        except Exception as e:
            return render_template('confirm.html', form=form, error=str(e))

    # Render the confirm template with the ConfirmationForm()
    return render_template('confirm.html', form=form)


@app.route('/add_channels', methods=['GET', 'POST'])
def add_chain():
    error = None
    form = AddChannelsForm()
    if form.validate_on_submit():
        # Get names of needed channels
        from_channel_name = form.outgoing.data
        to_channel_name = form.incoming.data

        # Try to add channel chain into the database
        result = monitor.add_chain(from_channel_name=from_channel_name, to_channel_name=to_channel_name)
        if result is True:
            return redirect(url_for('index'))
        else:
            error = result

    return render_template('add_channel.html', form=form, error=error)


@app.route('/delete/<int:chain>')
def delete(chain):

    chain_to_delete = ChannelChain.query.filter_by(id=chain).first()
    db_session = db.object_session(chain_to_delete)
    if db_session is None:
        db_session = db.session

    db_session.delete(chain_to_delete)
    db_session.commit()

    return redirect(url_for('index'))


@app.route('/clear')
def clear():
    try:
        """Clears the Flask session"""
        session['phone'] = None
        monitor.logout()

    except Exception as e:
        return redirect(url_for('login', error=str(e)))

    return redirect(url_for('login'))

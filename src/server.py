import json
import requests
import os
from flask import request
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, IntegrityError, InvalidRequestError

from config import setup_mail
from exceptions import AuthenticationException

from settings import dbg, app, db


mail = setup_mail(app)

CORS(app)

@app.route('/', methods=['GET'])
def ping():
    return "ping", 200

@app.route('/api/', methods=['GET'])
def login():
    try:
        app.logger.warning("GET /api %s" % request.args)
        email = request.args.get("email")
        e_password = request.args.get("e_password")
        username = request.args.get('username')
        account = dbg.get_account(email=email, password=e_password, username=username)
        if account:
            return account, 200
        else:
            return "Wrong Credentials", 403

    except OperationalError as oe:
        app.logger.error("OperationalError at GET /api/ %s" % oe)
        return login()

    except InvalidRequestError as oe:
        app.logger.error("InvalidRequestError at GET /api/ %s" % oe)
        app.logger.warning("run rollback()")
        db.session.rollback()
        return login()

    except Exception as exc:
        # 500 Internal Server Error
        app.logger.error("GET /api/ %s" % exc)
        app.logger.warning("run rollback()")
        db.session.rollback()
        return str(exc), 500


@app.route('/api/', methods=['PUT'])
def update_settings():
    try:
        data = json.loads(request.data)
        app.logger.warning("PUT /api/ %s" % data)

        if len(data) <= 1:
            return "nothing to update"

        username = data.get("username", "").lower()

        if not dbg.find_account(username=username):
            account = dbg.add_account(data)
            requests.post('%s/bot/login/' % os.environ['APP_BOT_GATEWAY'], request.data)
        else:
            account = dbg.update_account(data)

        dbg.update_user(data)
        dbg.update_timetable(account, data)

        return "updated Account %r" % account

    except OperationalError as oe:
        app.logger.error("OperationalError at PUT /api/ %s" % oe)
        return update_settings()

    except AuthenticationException as exc:
        app.logger.error("AuthenticationException at PUT /api/ %s" % exc)
        return str(exc), 403

    except InvalidRequestError as oe:
        app.logger.error("InvalidRequestError at PUT /api/ %s" % oe)
        app.logger.warning("run rollback()")
        db.session.rollback()
        return update_settings()

    except Exception as exc:
        # 500 Internal Server Error
        app.logger.error("PUT /api/ %s" % exc)
        app.logger.warning("run rollback()")
        db.session.rollback()
        return str(exc), 500


@app.route('/api/register/', methods=['PUT'])
def register():
    try:
        data = json.loads(request.data)
        app.logger.warning("PUT /api/register/ %s" % data)

        if len(data) <= 1:
            return "nothing to update"

        account = dbg.get_account(email=data.get("email"), password=data.get("password"),
                                  username=data.get("username", "").lower())
        if account:
            return account, 201

        user = dbg.register_user(data)

        return "created %r" % user, 200

    except OperationalError as oe:
        app.logger.error("OperationalError at PUT /api/register/ %s" % oe)
        return register()

    except InvalidRequestError as oe:
        app.logger.error("InvalidRequestError at PUT /api/register/ %s" % oe)
        app.logger.warning("run rollback()")
        db.session.rollback()
        return register()

    except IntegrityError as exc:
        app.logger.error("PUT /api/register/ %s" % exc)
        return "Wrong Credentials", 403

    except Exception as exc:
        # 500 Internal Server Error
        app.logger.error("PUT /api/register/ %s" % exc)
        app.logger.warning("run rollback()")
        db.session.rollback()
        return str(exc), 500


@app.route('/api/bot/activity/<user>/<pw>', methods=['POST', 'GET'])
def bot_activity(user, pw):
    try:
        if request.method == 'POST':
            app.logger.warning("POST /api/%s/%s %s: %s" % (user, pw, request.data))
            return dbg.add_bot_activity(request.data)

        elif request.method == 'GET':
            app.logger.warning("GET /api/%s/%s" % (user, pw))
            return dbg.get_bot_activity()

        return 404

    except OperationalError as oe:
        app.logger.error("OperationalError at GET/POST /api/%s/%s %s" % (user, pw, oe))
        return bot_activity(user, pw)


    except InvalidRequestError as oe:
        app.logger.error("InvalidRequestError at GET/POST /api/%s/%s %s" % (user, pw, oe))
        app.logger.warning("run rollback()")
        db.session.rollback()
        return bot_activity(user, pw)

    except Exception as exc:
        # 500 Internal Server Error
        app.logger.error("POST /api/%s/%s %s" % (user, pw, exc))
        app.logger.warning("run rollback()")
        db.session.rollback()
        return str(exc), 500


@app.route('/api/bot/login/', methods=['POST'])
def try_login():
    data = json.loads(request.data)
    app.logger.warning("POST /bot/login: %s" % data)
    try:
        return requests.post('%s/bot/login/' % os.environ['APP_BOT_GATEWAY'], request.data)
    except Exception as exc:
        app.logger.error("POST /bot/login Exception: %s" % (exc))
        return str(exc), 500


@app.route('/api/bot/stop/<account>', methods=['GET'])
def stop(account):
    app.logger.warning("GET /bot/stop/%s" % account)
    try:
        return requests.get('%s/bot/stop/%s' % (os.environ['APP_BOT_GATEWAY'], account))
    except Exception as exc:
        app.logger.error("GET /bot/stop/%s Exception: %s" % (account, exc))
        return str(exc), 500


@app.route('/api/bot/start/<account>', methods=['GET'])
def start(account):
    app.logger.warning("GET /bot/start/%s" % account)
    try:
        return requests.get('%s/bot/start/%s' % (os.environ['APP_BOT_GATEWAY'], account))
    except Exception as exc:
        app.logger.error("GET /bot/start/%s Exception: %s" % (account, exc))
        return str(exc), 500


@app.route('/api/mail/', methods=['POST'])
def mail():
    data = json.loads(request.data)
    app.logger.warning("POST /mail: %s" % data)
    try:
        return requests.post('%s/mail/' % os.environ['APP_MAIL_GATEWAY'], request.data)
    except Exception as exc:
        app.logger.error("POST /bot/login Exception: %s" % (exc))
        return str(exc), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000)

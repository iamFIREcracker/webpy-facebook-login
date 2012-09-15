import json
import os
import time
import urllib
import urlparse

import web
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from web.contrib.template import render_jinja

from models import engine
from models import User


FACEBOOK_APP_ID = "000000000000000"

FACEBOOK_APP_SECRET = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


urls = (
    '/', 'MainHandler',
    '/login', 'LoginHandler',
    '/logout', 'LogoutHandler',
    '/periods', 'PeriodsHandler',
)


def load_sqla(handler):
    web.ctx.orm = scoped_session(sessionmaker(bind=engine))
    try:
        return handler()
    except web.HTTPError:
       web.ctx.orm.commit()
       raise
    except:
        web.ctx.orm.rollback()
        raise
    finally:
        web.ctx.orm.commit()


application = web.application(urls, globals())
application.add_processor(load_sqla)
working_dir = os.path.dirname(__file__)
render = render_jinja(os.path.join(working_dir, '.'), encoding='utf-8')


def path_url():
    return web.ctx.home + web.ctx.fullpath


class BaseHandler():
    def current_user(self):
        """Returns the logged in Facebook user or None."""

        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = web.cookies().get('fb_user')
            if user_id:
                self._current_user = web.ctx.orm.query(User).filter_by(id=user_id).first()

        return self._current_user


class LoginHandler(BaseHandler):
    def GET(self):
        if self.current_user():
            web.seeother('/')
            return

        data = web.input(code=None)
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=path_url())
        if data.code is None:
            web.seeother(
                    'http://www.facebook.com/dialog/oauth?' +
                    urllib.urlencode(args))
            return

        args['code'] = data.code
        args['client_secret'] = FACEBOOK_APP_SECRET
        response = urlparse.parse_qs(
                urllib.urlopen(
                    "https://graph.facebook.com/oauth/access_token?" +
                        urllib.urlencode(args)).read())
        access_token = response["access_token"][-1]
        profile = json.load(
                urllib.urlopen(
                    "https://graph.facebook.com/me?" +
                    urllib.urlencode(dict(access_token=access_token))))

        user = User(id=str(profile["id"]), name=profile["name"],
                access_token=access_token, profile_url=profile["link"])
        user = web.ctx.orm.merge(user) # Merge flying and persistence object
        web.ctx.orm.add(user)

        web.setcookie(
                'fb_user', str(profile['id']), expires=time.time() + 7 * 86400)
        return web.seeother('/')


class LogoutHandler():
    def GET(self):
        web.setcookie('fb_user', '', expires=time.time() - 86400)
        web.seeother('/')


class MainHandler(BaseHandler):
    def GET(self):
        return render.index(user=self.current_user())


if __name__ == '__main__':
    application.run()

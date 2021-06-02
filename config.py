import os

class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "suG8$L1uJQQykAuUkjZaYo5t&cspLg!5#WEQ6NgXd*xV#pE9#6V%gmndvCBGF0DBOEXh9Kd49DiWnDl5uq!6*jR%vcIvGPuzjZa"
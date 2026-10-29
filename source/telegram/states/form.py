from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class FormSG(StatesGroup):
    name = State()
    age = State()


class CaptchaSG(StatesGroup):
    """Старое CaptchaState: ждём пять цифр в ответ на сообщение."""

    waiting_captcha = State()


class SurveySG(StatesGroup):
    """Опрос (старый survey.py): голосование по кнопкам sv:*."""

    waiting_vote = State()

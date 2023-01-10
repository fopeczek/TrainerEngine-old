from random import randint
import numpy as np
# import SQL_manager as sql
from .SQL_manager import Record_template

default_percent_answer = 50


# Scoring
def score_number(record:Record_template) -> bool:
    return record.answer == record.correct_answer


def logit_function(x: float) -> float:
    return np.log(x / (1 - x))


def score_continuous(answer: float, correct_answer: float) -> float:
    return np.abs(logit_function(correct_answer) - logit_function(answer / 0.999 + 0.0005))


def score_in_percents(answer: int, correct_answer: int, threshold) -> float:
    score = score_continuous(answer / 100, correct_answer / 100)
    return 1 - min(max(score - 0.1, 0) / threshold, 1.)


def score_percent(record: Record_template, threshold):
    if score_in_percents(record.answer, record.correct_answer, threshold) > 0:
        return True
    else:
        return False


# Question making
def make_question(loaded_config):
    if loaded_config.percent:
        question, correct_answer = make_percent_question()
        answer = default_percent_answer
    else:

        question, correct_answer = make_number_question((loaded_config.min1, loaded_config.max1),
                                                        (loaded_config.min2, loaded_config.max2),
                                                        loaded_config.do_neg)
        answer = ""
    out = Record_template(question, answer, correct_answer)
    return out


def make_number_question(first_range: tuple[int, int], second_range: tuple[int, int], do_neg) -> tuple[
    str, int]:
    num1 = randint(first_range[0], first_range[1])
    num2 = randint(second_range[0], second_range[1])
    is_neg = 0
    if do_neg:
        is_neg = randint(0, 1)
    if is_neg == 1:
        num2 = -num2  # negate num
    if num2 > 0:
        question = f"{num1}+{num2}"
    else:
        question = f"{num1}{num2}"  # no need to add - cuz the num is already with minus
    return question, num1 + num2


def make_percent_question() -> str:
    percent = randint(0, 100)
    return f"{percent}%"


def inverse_logit_function(x: float) -> float:
    return 1 / (1 + np.exp(-x))


def make_percent_question() -> tuple[str, float]:
    percent = int(inverse_logit_function(np.random.normal(0, 2)) * 100)
    return f"{percent}%", percent

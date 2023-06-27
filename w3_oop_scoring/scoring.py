import datetime
import hashlib
import json
import logging


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        datetime.datetime.strftime(birthday, "%Y-%m-%d") or ""
    ]
    key = "score:" + hashlib.md5(("".join(key_parts)).encode()).hexdigest()

    # try get from cache, fallback to heavy calculation in case of cache miss
    try:
        score = store.cache_get(key) or 0
        if isinstance(score, bytes):
            score = score.decode("UTF-8")
    except AttributeError:
        score = 0

    if score:
        logging.debug(f"get score from storage: {score}")
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    store.cache_set(key, score)
    return score


def get_interests(store, cid):
    r = store.get(f"inter:{cid}")
    return json.loads(r) if r else [f"can not get information on the key {cid} from storage"]


# def get_interests(store, cid):
#     interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
#     return random.sample(interests, 2)

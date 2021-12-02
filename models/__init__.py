import os
import json
from pytz import utc
from datetime import datetime
import time
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, aliased, load_only
from sqlalchemy import func
from collections import defaultdict, namedtuple

from .base import *
from .extra import *

def int_time():
    return int(time.time())

def retry(n):
    def _wrapper(f):
        def __wrapper(*args, **kwargs):
            for _ in range(n):
                try:
                    return f(*args, **kwargs)
                except OperationalError as e:
                    continue
        return __wrapper
    return _wrapper

class TranslationSQL(object):
    def __init__(self, override_url=None):
        self.really_connected = 0
        self.session_nest = []
        self.connect_url = override_url

        self.availability_cache = {}
        self.caches_disabled = bool(os.getenv("TLE_DISABLE_CACHES"))
        if self.caches_disabled:
            print("TranslationSQL: no caching")

    def __enter__(self):
        if not self.really_connected:
            conn_s = self.connect_url or os.getenv("DATABASE_CONNECT")
            self.engine = create_engine(conn_s, echo=False,
                #connect_args={"ssl": {"dummy": "yes"}})
		connect_args={'sslmode':'require'})

            try:
                Base.metadata.create_all(self.engine)
            except (TypeError, ProgrammingError):
                self.engine = create_engine(conn_s, echo=False)
                Base.metadata.create_all(self.engine)

            self.Session = sessionmaker(self.engine)
            self.really_connected = 1

        self.session_nest.append(self.Session())
        return self.session_nest[-1]

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value:
            self.session_nest[-1].rollback()
        self.session_nest[-1].close()
        self.session_nest.pop()

    @retry(5)
    def all(self):
        with self as s:
            transient = aliased(TranslationEntry)
            result = s.query(TranslationEntry).filter(
                s.query(func.count(transient.id))
                .filter(transient.submit_utc >= TranslationEntry.submit_utc)
                .filter(transient.key == TranslationEntry.key)
                .order_by(transient.id.desc())
                .correlate(TranslationEntry)
                .as_scalar() == 1).all()
        return result

    @retry(5)
    def delete_all_entries(self):
        with self as s:
            s.query(TranslationEntry).delete()
            s.query(TranslationCache).delete()

    @retry(5)
    def all_for_key(self, key):
        with self as s:
            result = s.query(TranslationEntry).filter(TranslationEntry.key == key).order_by(TranslationEntry.submit_utc).all()
        return result

    @retry(5)
    def translate(self, done, *key):
        with self as s:
            result = s.query(TranslationCache).filter(TranslationCache.key.in_(key)).limit(len(key)).all()
        done(result)

    @retry(5)
    def set_translation(self, key, eng, sender, force_time=None):
        with self as s:
            s.add(TranslationEntry(key=key, english=eng,
                                   submitter=sender, submit_utc=force_time or int_time()))
            try:
                thing_to_update = s.query(TranslationCache).filter(TranslationCache.key == key).one()
            except NoResultFound:
                thing_to_update = TranslationCache(key=key, english=eng)
            thing_to_update.english = eng
            s.add(thing_to_update)
            s.commit()

    @retry(5)
    def push_history(self, dt, payload):
        with self as s:
            s.add(HistoryEntry(time=dt, payload=payload))
            s.commit()
        self.history_cache = []

    @retry(5)
    def update_caches(self):
        with self as s:
            transient = aliased(TranslationEntry)
            result = s.query(TranslationEntry).filter(
                s.query(func.count(transient.id))
                .filter(transient.submit_utc >= TranslationEntry.submit_utc)
                .filter(transient.key == TranslationEntry.key)
                .order_by(transient.id.desc())
                .correlate(TranslationEntry)
                .as_scalar() == 1).all()
            s.query(TranslationCache).delete()
            cache_ents = [TranslationCache(key=x.key, english=x.english)
                for x in result if x.key != x.english]
            s.add_all(cache_ents)
            s.commit()

    def gen_presence(self, gacha_list):
        # 3, 1 is the regular gacha
        # 3, 3 is the 60-gem daily paid gacha
        # 2, x is the choose-a-ssr ticket gacha
        gacha_list = list(filter(lambda x: x.type == 3 and x.subtype == 1, gacha_list))
        gacha_map = {x.id: x for x in gacha_list}

        def earliest_gacha(gl):
            return min(gl, key=lambda gacha: gacha.start_date if gacha else utc.localize(datetime.max))
        def latest_gacha(gl):
            return max(gl, key=lambda gacha: gacha.end_date if gacha else utc.localize(datetime.min))
        def fromidlist(idl):
            return [gacha_map.get(id) for id in idl]

        gacha_list.sort(key=lambda x: x.start_date)
        prev = gacha_list[0]

        # the db operation is wrapped so we can retry if needed

        self.seed_initial(prev, delete=1)
        print("Primary seeding completed")

        for gacha in gacha_list[1:]:
            if (gacha.start_date - prev.end_date).seconds < 10:
                print(gacha, "is a continuation of", prev)
                self.extend_gacha(prev, gacha)
            else:
                self.seed_initial(gacha)
            prev = gacha

        self.availability_cache = {}
        return

    @retry(5)
    def add_reward_tracking_entries(self, iterator):
        with self as s:
            for ent in iterator:
                s.merge(GachaRewardEntry(gacha_id=ent[0], step_num=ent[1], reward_id=ent[2], recommend_order=ent[3], limited_flag=ent[4]))
            s.commit()

    @retry(5)
    def seed_initial(self, prev, delete=0):
        with self as s:
            if delete:
                s.query(GachaPresenceEntry).delete()

            for card, in s.query(GachaRewardEntry.reward_id).filter(GachaRewardEntry.gacha_id == prev.id):
                s.add(GachaPresenceEntry(card_id=card, gacha_id_first=prev.id, gacha_id_last=prev.id,
                    avail_start=prev.start_date.timestamp(), avail_end=prev.end_date.timestamp()))
                print("Seed", prev.id, "having id", card)
            s.commit()

    @retry(5)
    def extend_gacha(self, prev, new):
        print(prev.id, "->", new.id, "!!")
        with self as s:
            extant_ids = s.query(GachaPresenceEntry.card_id).filter(GachaPresenceEntry.gacha_id_last == prev.id).all()
            # sqlalchemy returns 1-tuples so get the ids out before turning it into a set
            extant_ids = set(x[0] for x in extant_ids)

            ng_ids = s.query(GachaRewardEntry.reward_id).filter(GachaRewardEntry.gacha_id == new.id).all()
            ng_ids = set(x[0] for x in ng_ids)

            # cards in both prev and new gachas
            update_ids = extant_ids & ng_ids
            print(update_ids)

            s.query(GachaPresenceEntry).filter(GachaPresenceEntry.card_id.in_(update_ids), GachaPresenceEntry.gacha_id_last == prev.id).update(
                {GachaPresenceEntry.gacha_id_last: new.id,
                 GachaPresenceEntry.avail_end: new.end_date.timestamp()},
            synchronize_session=False)

            # appearances get a new record
            new_ids = ng_ids - extant_ids
            for id in new_ids:
                s.add(GachaPresenceEntry(card_id=id, gacha_id_first=new.id, gacha_id_last=new.id,
                    avail_start=new.start_date.timestamp(), avail_end=new.end_date.timestamp()))
            print(new_ids)
            s.commit()

    def gacha_availability(self, cards, gacha_list):
        if self.caches_disabled:
            return self._gacha_availability(cards, gacha_list)

        ret = {}
        need_fetch = []
        for k in cards:
            pre = self.availability_cache.get(k)
            if pre is None:
                need_fetch.append(k)
            else:
                ret[k] = pre

        if need_fetch:
            fetch = self._gacha_availability(need_fetch, gacha_list)
            ret.update(fetch)
            self.availability_cache.update(fetch)
        return ret

    @retry(5)
    def _gacha_availability(self, cards, gacha_list):
        print("trace _gacha_availability", cards)
        gacha_map = {x.id: x for x in gacha_list}

        ga = defaultdict(lambda: [])
        for k in cards:
            ga[k] # force the empty list to be created and cached

        with self as s:
            ents = s.query(GachaLookupEntry).filter(GachaLookupEntry.card_id.in_(cards)).all()

        def getgacha(gid):
            if gid in gacha_map:
                return gacha_map[gid]
            else:
                return unknown_gacha_t("??? (unknown gacha ID: {0})".format(gid))

        for e in ents:
            recent = getgacha(e.last_gacha_id)
            name = recent.name

            # FIXME do this better
            if name == "プラチナオーディションガシャ":
                name = None

            # We now display the last gacha the card was featured in, according
            # to history. This means that we may show a past date, even though the card itself
            # is still green.
            ga[e.card_id].append(Availability(
                Availability._TYPE_GACHA,
                name,
                recent.start_date,
                recent.end_date, [],
                e.is_limited))

            # For limited cards, display the most recent and the first one it appeared in.
            if e.first_gacha_id != e.last_gacha_id and e.is_limited:
                first = getgacha(e.first_gacha_id)
                name_first = first.name
                if name_first == "プラチナオーディションガシャ":
                    name_first = None
                ga[e.card_id].append(Availability(
                    Availability._TYPE_GACHA,
                    name_first,
                    first.start_date,
                    first.end_date, [],
                    e.is_limited))
        return ga

    @retry(5)
    def get_history(self, nent, page=0):
        with self as s:
            rows = s.query(HistoryEventEntry).order_by(HistoryEventEntry.start_time.desc())

            if nent:
                rows = rows.limit(nent).offset(page * nent)

            return list(rows.all())

    @retry(5)
    def lookup_event_cards(self, cards):
        with self as s:
            ents = s.query(EventLookupEntry).filter(EventLookupEntry.card_id.in_(cards)).all()

        # {card: {event: [type, type]}}
        ret = defaultdict(lambda: defaultdict(lambda: []))
        enum_acquisition_to_str = {1: "progression", 2: "ranking", 3: "gacha"}
        for e in ents:
            w = enum_acquisition_to_str.get(e.acquisition_type)
            # Only use the generic case as a last resort
            if w is not None or not ret[e.card_id][e.event_id]:
                ret[e.card_id][e.event_id].append(w)

        return ret

    @retry(5)
    def lookup_event_rewards(self, eids):
        with self as s:
            eids_only = {x.id for x in eids}
            ents = s.query(EventLookupEntry).filter(EventLookupEntry.event_id.in_(eids_only)).all()

        buckets = defaultdict(lambda: [])
        for ent in ents:
            if ent.card_id not in buckets[ent.event_id]:
                buckets[ent.event_id].append(ent.card_id)

        return [buckets[eid.id] for eid in eids]

class TranslationEngine(TranslationSQL):
    def __init__(self, data_source, override_url=None):
        super().__init__(override_url)
        self.dsrc = data_source
        self.cache_id = -1
        self.k2r = {}

    def kill_caches(self, dv):
        self.k2r = {x.kanji: x.conventional for _, x in self.dsrc.data.names.items()}
        self.availability_cache = {}
        self.cache_id = dv

    def get_history(self, nent, page=0):
        return super().get_history(nent, page)

    def gacha_availability(self, cards, gacha_list):
        if self.cache_id != self.dsrc.data.version:
            self.kill_caches(self.dsrc.data.version)

        return super().gacha_availability(cards, gacha_list)

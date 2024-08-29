import tornado.web
import tornado.template
import tornado.escape
from dispatch import *
import os
import json
import starlight
import time
import pytz
import itertools
import enums
import table
import hashlib
import traceback
from models import extra
from collections import defaultdict
from datetime import datetime, timedelta

import webutil

class ErrorUtilsMixin(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)

        tb = None
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            tb = "".join(traceback.format_exception(*kwargs["exc_info"]))

        self.render("error.html", 
            code=status_code,
            message=kwargs.get("app_reason") or self._reason,
            traceback=tb,
            **self.settings)
        self.finish()

@route(r"/([0-9]+-[0-9]+-[0-9]+)?")
class Home(HandlerSyncedWithMaster, ErrorUtilsMixin):
    async def head(self, pretend_date):
        return self.get(pretend_date)

    async def get(self, pretend_date):
        actually_now = pytz.utc.localize(datetime.utcnow())

        if pretend_date:
            now = pytz.utc.localize(datetime.strptime(pretend_date, "%Y-%m-%d"))
        else:
            now = actually_now

        if now.day == 29 and now.month == 2:
            now += timedelta(days=1)

        # Show only cu/co/pa chara birthdays. Chihiro is a minefield and causes
        # problems
        birthdays = list(filter(lambda char: 0 < char.type < 4,
                         starlight.data.potential_birthdays(now)))
        now_utime = now.timestamp()

        recent_history = [evt for evt in self.settings["tle"].get_history(10) if evt.start_time <= now_utime]
        
        # cache priming has a high overhead so prime all icons at once
        preprime_set = set()
        for h in recent_history:
            preprime_set.update(h.card_list())
        starlight.data.cards(preprime_set)
        
        # Now split the events into current/past.
        current_events = [event for event in recent_history 
            if now_utime >= event.start_time and now_utime < event.end_time]
        # Always put events first like the old box list.
        current_events.sort(key=lambda event: -1 if event.type() == extra.HISTORY_TYPE_EVENT else 1)
    
        rates = {}
        for event in current_events:
            recent_history.remove(event)

            if event.type() == extra.HISTORY_TYPE_GACHA:
                rate = await starlight.data.live_gacha_rates(event.referred_id())
                if not rate:
                    continue

                try:
                    rates[rate["gacha"]] = rate["rates"]
                except KeyError:
                    continue

        self.render("main.html", history=recent_history,
            current_history=current_events,
            live_gacha_rates=rates,
            birthdays=birthdays, **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route("/suggest")
class SuggestNames(HandlerSyncedWithMaster):
    def get(self):
        names = {value.conventional.lower(): [value.kanji, key] for key, value in starlight.data.names.items()}#conventional value.conventional
        names.update({str(key): [value.kanji, key] for key, value in starlight.data.names.items()})#chara_id
        
        # additional keyword set
        names.update({str(value.kana_spaced): [value.kanji, key] for key, value in starlight.data.names.items()})#kana_spaced
        names.update({str(value.kanji): [value.kanji, key] for key, value in starlight.data.names.items()})#kanji
        names.update({str(value.translated): [value.translated + " *" , key] for key, value in starlight.data.names.items()})#translated
        names.update({str(value.translated_cht): [value.translated_cht + " *", key] for key, value in starlight.data.names.items()})#translated_cht
		
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Expires", "0")
        self.write(names)

@route(r"/_evt")
class EventD(HandlerSyncedWithMaster):
    def get(self):
        self.set_header("Content-Type", "text/plain; charset=utf-8")

        now = pytz.utc.localize(datetime.utcnow())
        if now.day == 29 and now.month == 2:
            now += timedelta(days=1)

        events = starlight.data.events(now)

        if events:
            evedt = events[0].end_date.astimezone(pytz.timezone("Asia/Tokyo"))
            self.set_header("Content-Type", "text/plain; charset=utf-8")
            self.write("{0}".format(evedt.strftime("%B %d, %Y %H:%M")))
        else:
            self.write("None")

@route(r"/char/([0-9]+)(/table)?")
class Character(HandlerSyncedWithMaster, ErrorUtilsMixin):
    def get(self, chara_id, use_table):
        chara_id = int(chara_id)
        achar = starlight.data.chara(chara_id)

        card_ids = starlight.data.cards_belonging_to_char(chara_id)
        chains = [starlight.data.chain(id) for id in card_ids]
        unique = []
        for c in chains:
            if c not in unique:
                unique.append(c)

        acard = [starlight.data.cards(ch) for ch in unique]
        eventset = {x.id: x for x in starlight.data.event_ids()}

        availability = defaultdict(lambda: [])
        av_dict_from_tle = self.settings["tle"].lookup_event_cards(card_ids)
        for cid, events in av_dict_from_tle.items():
            for eid in events:
                x = eventset[eid]
                avs = starlight.Availability(starlight.Availability._TYPE_EVENT, x.name, x.start_date, x.end_date)
                availability[cid].append(avs)

        ga_av = self.settings["tle"].gacha_availability(card_ids, starlight.data.gacha_ids())
        for k in ga_av:
            availability[k].extend(ga_av[k])

        # This is so the initial (N or R) card appears first.
        acard.sort(key=lambda x: (0 if x[0].rarity < 5 else 1, x[0].id))

        if achar:
            self.set_header("Content-Type", "text/html")
            self.render("chara.html",
                chara=achar,
                chara_id=chara_id,
                cards=acard,
                use_table=use_table,
                availability=availability,
                now=pytz.utc.localize(datetime.utcnow()),
                **self.settings)
            self.settings["analytics"].analyze_request(
                self.request, self.__class__.__name__, {"chara": achar.conventional})
        else:
            return self.send_error(404, app_reason="No such character.")


@route(r"/card/([0-9\,]+)(/table)?")
class Card(HandlerSyncedWithMaster, ErrorUtilsMixin):
    def get(self, card_idlist, use_table):
        card_ids = [int(x) for x in card_idlist.strip(",").split(",")]

        chains = [starlight.data.chain(id) for id in card_ids]
        unique = []
        for c in chains:
            if c not in unique:
                unique.append(c)

        acard = [starlight.data.cards(ch) for ch in unique if ch]

        eventset = {x.id: x for x in starlight.data.event_ids()}

        availability = defaultdict(lambda: [])
        av_dict_from_tle = self.settings["tle"].lookup_event_cards(card_ids)
        for cid, events in av_dict_from_tle.items():
            for eid in events:
                x = eventset[eid]
                avs = starlight.Availability(starlight.Availability._TYPE_EVENT, x.name, x.start_date, x.end_date)
                availability[cid].append(avs)

        ga_av = self.settings["tle"].gacha_availability(card_ids, starlight.data.gacha_ids())
        for k in ga_av:
            availability[k].extend(ga_av[k])

        if acard:
            if len(acard) == 1:
                just_one_card = acard[0][0]
            else:
                just_one_card = None
            self.set_header("Content-Type", "text/html")
            self.render("card.html", cards=acard, use_table=use_table,
                just_one_card=just_one_card, availability=availability,
                now=pytz.utc.localize(datetime.utcnow()), **self.settings)
            self.settings["analytics"].analyze_request(
                self.request, self.__class__.__name__, {"card_id": card_idlist})
        else:
            return self.send_error(404, app_reason="No such card.")

# all the table handlers go here

# Try to use ShortlinkTable.rendertable instead of directly rendering
# a table template whenever possible, so we can make enhancements to
# it apply globally to all tables.

@route(r"/t/([A-Za-z]+)/([^/]+)")
class ShortlinkTable(HandlerSyncedWithMaster, ErrorUtilsMixin):
    # This shouldn't take too long.
    # The full chain is pre-emptively loaded when any member is requested
    def flip_chain(self, card):
        return starlight.data.card(starlight.data.chain(card.series_id)[-1])

    def rendertable(self, dataset, cards,
                    allow_shortlink=1, table_name="自定义列表",
                    template="generictable.html", **extra):
        if isinstance(dataset, str):
            filters, categories = table.select_categories(dataset)
        else:
            filters, categories = dataset

        should_switch_chain_head = self.get_argument("plus", "NO") == "YES"
        if should_switch_chain_head:
            cards = list(map(self.flip_chain, cards))

        extra.update(self.settings)

        self.render(template,
                    filters=filters,
                    categories=categories,
                    cards=cards,
                    original_dataset=dataset,
                    show_shortlink=allow_shortlink,
                    table_name=table_name,
                    is_displaying_awake_forms=should_switch_chain_head,
                    **extra)

    def get(self, dataset, spec):
        try:
            idlist = webutil.decode_cardlist(spec)
        except ValueError:
            return self.send_error(400, app_reason="The card list could not be parsed.")

        card_list = [*filter(bool, starlight.data.cards(idlist))]
        if not card_list:
            return self.send_error(404, app_reason="Not found.")

        self.rendertable(dataset.upper(), card_list)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/skill_table")
class SkillTable(ShortlinkTable):
    def compute_etag(self):
        hasher = hashlib.sha1(b"SkillTable version ")
        hasher.update(self.settings["instance_random"])
        hasher.update(str(starlight.data.version).encode("utf8"))
        hasher.update("; plus={0}".format(
            "yes" if self.get_argument("plus", "NO") == "YES" else "no").encode("utf8"))
        return "\"{0}\"".format(hasher.hexdigest())

    def get(self):
        self.set_etag_header()
        if self.check_etag_header():
            self.set_status(304)
            return

        self.set_header("Cache-Control", "must-revalidate")
        ds = filter(lambda C: C.skill is not None, starlight.data.cards(starlight.data.all_chain_ids()))
        self.rendertable("CASDE", ds,
            allow_shortlink=0,
            table_name="Cards by skill")
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/lead_skill_table")
class LeadSkillTable(ShortlinkTable):
    def compute_etag(self):
        hasher = hashlib.sha1(b"LeadSkillTable version ")
        hasher.update(self.settings["instance_random"])
        hasher.update(str(starlight.data.version).encode("utf8"))
        hasher.update("; plus={0}".format(
            "yes" if self.get_argument("plus", "NO") == "YES" else "no").encode("utf8"))
        return "\"{0}\"".format(hasher.hexdigest())

    def get(self):
        self.set_etag_header()
        if self.check_etag_header():
            self.set_status(304)
            return

        self.set_header("Cache-Control", "must-revalidate")
        ds = filter(lambda C: C.lead_skill is not None, starlight.data.cards(starlight.data.all_chain_ids()))
        self.rendertable("CAKL", ds,
            allow_shortlink=0,
            table_name="Cards by lead skill")
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/table/([A-Za-z]+)/([0-9\,]+)")
class CompareCard(ShortlinkTable):
    def get(self, dataset, card_idlist):
        card_ids = [int(x) for x in card_idlist.strip(",").split(",")]

        chains = [starlight.data.chain(id) for id in card_ids]
        unique = []
        for c in chains:
            if c is not None and c[0] not in unique:
                unique.append(c[0])

        acard = starlight.data.cards(unique)

        if acard:
            self.rendertable(dataset.upper(), acard, table_name="自定义列表")
            self.settings["analytics"].analyze_request(
                self.request, self.__class__.__name__, {"card_id": card_idlist})
        else:
            return self.send_error(404, app_reason="No cards in the given list were found.")

@route(r"/gacha(?:/([0-9]+))?")
class GachaTable(ShortlinkTable):
    def awakened_id(self, cid):
        return starlight.data.chain(cid)[-1]

    async def get(self, maybe_gachaid):
        now = pytz.utc.localize(datetime.utcnow())

        if maybe_gachaid:
            maybe_gachaid = int(maybe_gachaid)
            gachas = starlight.data.gacha_ids()

            for gcid in gachas:
                if gcid.id == maybe_gachaid:
                    selected_gacha = gcid
                    break
            else:
                selected_gacha = None
        else:
            gachas = starlight.data.gachas(now)

            if gachas:
                selected_gacha = gachas[0]
            else:
                selected_gacha = None

        if selected_gacha is None:
            return self.send_error(404, app_reason="Not found. If there's no gacha happening right now, you'll have to specify an ID.")

        is_current = (now >= selected_gacha.start_date) and (now <= selected_gacha.end_date)

        if not is_current:
            return self.send_error(404, app_reason="Gacha rates are only available for current gachas. Sorry about that.")
        
        want_awakened = self.get_argument("plus", "NO") == "YES"
        live_info = await starlight.data.live_gacha_rates(selected_gacha.id)

        availability_list = starlight.data.available_cards(selected_gacha)
        availability_list.sort(key=lambda x: x.sort_order)

        want_id_list = [gr.card_id for gr in availability_list]
        if want_awakened:
            limited_flags = {self.awakened_id(gr.card_id): gr.is_limited for gr in availability_list}
        else:
            limited_flags = {gr.card_id: gr.is_limited for gr in availability_list}

        if live_info:
            want_id_list.extend(cid for cid in live_info["indiv"] if cid not in limited_flags)

        card_list = starlight.data.cards(want_id_list)

        filters, categories = table.select_categories("CASDE")

        lim_cat = table.CustomBool()
        lim_cat.header_text = "限？"
        lim_cat.values = limited_flags
        lim_cat.yes_text = "是"
        lim_cat.no_text = "否"
        categories.insert(0, lim_cat)

        if live_info:
            if want_awakened:
                indiv_rates = {self.awakened_id(k): v for k, v in live_info["indiv"].items()}
            else:
                indiv_rates = live_info["indiv"]

            odds_cat = table.CustomNumber(indiv_rates, header_text="几率", format="{0:.3f}%")
            categories.insert(1, odds_cat)

            live_rates = live_info["rates"]
        else:
            live_rates = None

        self.rendertable( (filters, categories),
            cards=card_list,
            allow_shortlink=0,
            table_name="扭蛋: {0}".format(selected_gacha.name),
            template="ext_gacha_table.html",
            gacha=selected_gacha,
            rates=live_rates)

class MiniTable(ShortlinkTable, ErrorUtilsMixin):
    def rendertable(self, dataset, cards, table_name="Custom Table",
                    template="minitable.html", **extra):
        extra.update(self.settings)

        self.render(template,
                    categories=dataset,
                    cards=cards,
                    table_name=table_name,
                    **extra)

@route(r"/motif_internal/([1-9][0-9]*)")
class MotifInternalTable(MiniTable):
    def get(self, type):
        t = int(type)
        try:
            dataset = starlight.data.fetch_motif_data(t)
        except ValueError:
            return self.send_error(404, app_reason="This table doesn't currently exist.")

        css_class = self.get_argument("appeal", "vocal")
        if css_class not in {"vocal", "visual", "dance"}:
            css_class = "vocal"

        motif_cats = [table.IndexedCustomNumber(0, "Appeal value", dclass=css_class),
            table.IndexedCustomNumber(1, "Score bonus", format="+{0}%"),
            table.IndexedCustomNumber(2, "Score bonus (Grand Live)", format="+{0}%")]

        self.rendertable(motif_cats, dataset, table_name="Motif skill bonus table")
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/sparkle_internal/([1-9][0-9]*)")
class SparkleInternalTable(MiniTable):
    def get(self, type):
        t = int(type)
        try:
            dataset = starlight.data.fetch_sparkle_data(t)
        except ValueError:
            return self.send_error(404, app_reason="This table doesn't currently exist.")

        motif_cats = [table.IndexedCustomNumber(0, "Life value", dclass="life"),
            table.IndexedCustomNumber(1, "Combo bonus", format="+{0}%"),
            table.IndexedCustomNumber(2, "Combo bonus (Grand Live)", format="+{0}%")]

        self.rendertable(motif_cats, dataset, table_name="Life Sparkle skill bonus table")
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/sprite_go/([0-9]+).png")
class SpriteRedirect(tornado.web.RequestHandler):
    """ Javascript trampoline to locate transparents' URLs. """

    def get(self, card_id):
        card_id = int(card_id)
        assoc_card = starlight.data.card(card_id)

        assoc_char = assoc_card.chara_id
        assoc_pose = assoc_card.pose
        self.redirect("{0}/chara2/{1}/{2}.png".format(self.settings["image_host"],
                                                     assoc_char, assoc_pose))
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__,
            {"card_id": "({0}) {1} <{2}>".format(assoc_card.title, assoc_card.chara.conventional, card_id)})


@route(r"/sprite_go_ex/([0-9]+)")
class SpriteViewerEX(ErrorUtilsMixin):
    def get(self, chara_id):
        # hack for footer text compat
        self.did_trigger_update = False

        achar = starlight.data.chara(int(chara_id))
        if achar:
            svxdata = starlight.data.svx_data(achar.chara_id)
            self.render("spriteviewer.html",
                load="{0}/chara2/{1}".format(self.settings["image_host"], int(chara_id)),
                known_poses=svxdata,
                chara=achar,
                **self.settings)

        return self.send_error(404, app_reason="Not found.")


@route(r"/history")
@route(r"/history/([0-9]+)")
class History(HandlerSyncedWithMaster, ErrorUtilsMixin):
    """ Display all history entries. """
    def get(self, page=None):
        page = max(int(page or 1), 1)
        all_history = self.settings["tle"].get_history(nent=50, page=page - 1)

        preprime_set = set()
        for h in all_history:
            preprime_set.update(h.card_list())
        starlight.data.cards(preprime_set)

        self.render("history.html", history=all_history, page=page, **self.settings)
        self.settings["analytics"].analyze_request(self.request, self.__class__.__name__)

@route(r"/tl_cacheall")
@dev_mode_only
class DebugTLCacheUpdate(tornado.web.RequestHandler):
    def get(self):
        self.settings["tle"].update_caches()
        self.write("ok.")

@route(r"/ga_genpresencecache")
@dev_mode_only
class DebugGachaPresenceUpdate(tornado.web.RequestHandler):
    def get(self):
        cl = self.settings["tle"].gen_presence(starlight.data.gacha_ids())
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.write("ok")

@route(r"/tl_debug")
@dev_mode_only
class DebugViewTLs(tornado.web.RequestHandler):
    def get(self):
        #chara_id = int(chara_id)
        gen = list((x.key, x.english, x.submitter, time.strftime("%c", time.gmtime(x.submit_utc)))
            for x in filter(lambda x: x.key != x.english, self.settings["tle"].all()))
        fields = ("key", "english", "sender", "ts")

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=gen,
                    fields=fields, **self.settings)

@route(r"/tl_debug/(.+)")
@dev_mode_only
class DebugViewTLExtreme(tornado.web.RequestHandler):
    def get(self, key):
        #chara_id = int(chara_id)
        gen = list((x.key, x.english, x.submitter, time.strftime("%c", time.gmtime(x.submit_utc)))
            for x in self.settings["tle"].all_for_key(key))
        fields = ("key", "english", "sender", "ts")

        self.set_header("Content-Type", "text/html")
        self.render("debug_view_database.html", data=gen,
                    fields=fields, **self.settings)

@route(r"/clear_remote_cache")
@dev_mode_only
class DebugKillCache(tornado.web.RequestHandler):
    def get(self):
        self.settings["tle"].kill_caches(0)
        starlight.data = starlight.DataCache(starlight.data.version)

        self.write("ok.")

@route(r"/sync_event_lookup")
@dev_mode_only
class DebugSyncEventLookup(tornado.web.RequestHandler):
    def get(self):
        self.settings["tle"].sync_event_lookup_table()
        self.write("ok.")

@route(r"/test_gacha_rate")
@dev_mode_only
class DebugAPIGachaRate(tornado.web.RequestHandler):
    def get(self):
        def done(a, b):
            print(b)
            print(a)

        starlight.apiclient.gacha_rates(30180, done)

@route(r"/ping")
class Ping(tornado.web.RequestHandler):
    def head(self):
        return

    def get(self):
        self.write("{} {} {} {} {}".format(
            starlight.data.version,
            starlight.last_version_check,
            len(starlight.data.card_cache),
            len(starlight.data.char_cache),
            "It's working"
        ))

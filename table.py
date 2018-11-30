from collections import namedtuple
import webutil
import enums
import starlight
from tornado.escape import xhtml_escape

E = xhtml_escape

# TODO: for this entire file, extract all english strings and put them in starlight.en,
# or maybe use tornado's localization module?

option_t = namedtuple("option_t", ("name", "kill_class"))
filter_t = namedtuple("filter_t", ("name", "options", "gen_object_class"))

card_attribute = filter_t("偶像属性", (
    option_t("Cute",      "Cute_kc"),
    option_t("Cool",      "Cool_kc"),
    option_t("Passion",   "Passion_kc")),
lambda card: enums.attribute(card.attribute) + "_kc")

rarity = filter_t("卡牌稀有度", (
    option_t("SSR", "ssr_kc"),
    option_t("SR",  "sr_kc"),
    option_t("R",   "r_kc"),
    option_t("N",   "n_kc")),
lambda card: enums.floor_rarity(card.rarity) + "_kc")

skill_type = filter_t("特技类型", (
    option_t("强判",       "s_pl"),
    option_t("不断连",     "s_cprot"),
    option_t("C分",        "s_combobonus"),
    option_t("P分",        "s_scorebonus"),
    option_t("奶妈",       "s_heal"),
    option_t("血盾",       "s_life"),
    option_t("过载",       "s_overload"),
    option_t("全才",       "s_allround"),
    option_t("专注",       "s_perfelegant"),
    option_t("技能增强",   "s_sb"),
    option_t("集中",       "s_focus")),
    option_t("生命闪耀",   "s_cbonus_based_life"),
    option_t("返场",       "s_mimic"),
    option_t("三色协同",   "s_synergy")),
lambda card: enums.skill_class(card.skill.skill_type) if card.skill else None)

high_stat = filter_t("偏高数值", (
    option_t("Vocal", "m_vo_kc"),
    option_t("Visual", "m_vi_kc"),
    option_t("Dance", "m_da_kc"),
    option_t("均衡", "m_ba_kc")),
lambda card: enums.stat_dot(card.best_stat) + "_kc")

ls_target_type = filter_t("对象属性", (
    option_t("所有", "ca_all"),
    option_t("Cute", "ca_cute"),
    option_t("Passion", "ca_passion"),
    option_t("Cool", "ca_cool")),
lambda card: enums.lskill_effective_target(card.lead_skill.target_attribute) if card.lead_skill else None)

ls_target_stat = filter_t("对象数值", (
    option_t("Vocal", "ce_vocal"),
    option_t("Visual", "ce_visual"),
    option_t("Dance", "ce_dance"),
    option_t("所有", "ce_anyappeal"),

    option_t("<spacer>", ""),

    option_t("生命", "ce_life"),
    option_t("特技概率", "ce_skill")),
lambda card: enums.lskill_effective_param(card.lead_skill.target_param) if card.lead_skill else None)

# skill_table: CHSDE
# lead_skill_table: CHKL


class Datum(object):
    pass

class CardProfile(Datum):
    applicable_filters = [card_attribute, rarity, high_stat]
    uid = "C"

    def make_headers(self):
        return (
            """<th></th><th class="sort_key" data-sort-key="STCardNumberDatum">卡牌</th>"""
        )

    def make_values(self, a_card):
        return (
            """<td class="{attr_class}"> <a href="/char/{card.chara_id}#c_{card.id}_head">{icon_id}</a> </td>"""
            """<td class="{attr_class}"> <a href="/char/{card.chara_id}#c_{card.id}_head">{tle_translate}</a><br> <small>{tle_title}</small> </td>"""
        ).format(
            card=a_card,
            tle_translate=a_card.name_only,#starlight.data.translate_name(a_card.name_only)
            tle_title=webutil.tlable(a_card.title) if a_card.title_flag else "",
            icon_id=webutil.icon(a_card.id),
            attr_class=E(enums.attribute(a_card.attribute))
        )

class SkillType(Datum):
    applicable_filters = [skill_type]
    uid = "S"

    def make_headers(self):
        return (
            """<th></th>"""
        )

    def make_values(self, a_card):
        if a_card.skill:
            return (
                """<td> <div class="icon {0}"></div> </td>"""
            ).format(E(enums.skill_class(a_card.skill.skill_type)))
        else:
            return """<td></td>"""

class SkillName(Datum):
    applicable_filters = [skill_type]
    uid = "D"

    def make_headers(self):
        return (
            """<th>特技</th>"""
        )

    def make_values(self, a_card):
        if a_card.skill:
            return (
                """<td> {0} </td>"""
            ).format(webutil.tlable(a_card.skill.skill_name))
        else:
            return """<td></td>"""

class SkillEffect(Datum):
    applicable_filters = [skill_type]
    uid = "E"

    def make_headers(self):
        return (
            """<th>效果 (排序："""
            """<span class="sort_key" data-sort-key="STSkillTimeDatum">时间间隔</span>, """
            """<span class="sort_key" data-sort-key="STSkillProcChanceDatum">% 几率</span>, """
            """<span class="sort_key" data-sort-key="STSkillDurationDatum">持续时间</span>, """
            """<span class="sort_key" data-sort-key="STSkillEffectiveValueDatum">效果数值</span>"""
            """)</th>"""
        )

    def make_values(self, a_card):
        fmt = """<td class="skill_effect" data-m-proc="{1}" data-m-dur="{2}" data-tw="{3}" data-ef="{4}"> <small>{0}</small> </td>"""
        if a_card.skill:
            return fmt.format(
                starlight.en.describe_skill_html(a_card.skill),
                a_card.skill.max_chance,
                a_card.skill.max_duration,
                a_card.skill.condition,
                a_card.skill.value,
            )
        else:
            return fmt.format(starlight.en.describe_skill_html(a_card.skill), 0, 0, 0, 0)

class LSkillName(Datum):
    applicable_filters = [ls_target_stat, ls_target_type]
    uid = "K"

    def make_headers(self):
        return (
            """<th>领队技能</th>"""
        )

    def make_values(self, a_card):
        if a_card.skill:
            return (
                """<td> {0} </td>"""
            ).format(webutil.tlable(a_card.lead_skill.name))
        else:
            return """<td></td>"""

class LSkillEffect(Datum):
    applicable_filters = [ls_target_stat, ls_target_type]
    uid = "L"

    def make_headers(self):
        return (
            """<th>效果 (排序：<span class="sort_key" data-sort-key="STLeadSkillUpDatum">% up</span>)</th>"""
        )

    def make_values(self, a_card):
        return (
            """<td class="lead_skill_effect" data-pup="{1}"> <small>{0}</small> </td>"""
        ).format(
            starlight.en.describe_lead_skill_html(a_card.lead_skill),
            a_card.lead_skill.up_value if a_card.lead_skill else 0
        )

class HighStat(Datum):
    applicable_filters = [high_stat]
    uid = "H"

    def make_headers(self):
        return (
            """<th></th>"""
        )

    def make_values(self, a_card):
        return (
            """<td> <div class="icon {0}"></div> </td>"""
        ).format(E(enums.stat_dot(a_card.best_stat)))

class AppealsHigh(Datum):
    applicable_filters = []
    uid = "A"

    def make_headers(self):
        return (
            """<th class="sort_key" data-sort-key="STVocalStatDatum">Vo</th>"""
            """<th class="sort_key" data-sort-key="STVisualStatDatum">Vi</th>"""
            """<th class="sort_key" data-sort-key="STDanceStatDatum">Da</th>"""
        )

    def make_values(self, a_card):
        return (
            """<td class="vocal"> {vocal_max} </td>"""
            """<td class="visual"> {visual_max} </td>"""
            """<td class="dance"> {dance_max} </td>"""
        ).format(
            vocal_max=a_card.vocal_max + a_card.bonus_vocal,
            visual_max=a_card.visual_max + a_card.bonus_visual,
            dance_max=a_card.dance_max + a_card.bonus_dance
        )

class AppealsLow(Datum):
    applicable_filters = []
    uid = "B"

    make_headers = AppealsHigh.make_headers

    def make_values(self, a_card):
        return (
            """<td class="vocal"> {a_card.vocal_min} </td>"""
            """<td class="visual"> {a_card.visual_min} </td>"""
            """<td class="dance"> {a_card.dance_min} </td>"""
        ).format(a_card=a_card)

class CustomBool(Datum):
    applicable_filters = []
    # can't be selected via url because only A-Za-z is allowed
    uid = "?"

    yes_text = "True"
    no_text = "False"
    header_text = ""

    def make_headers(self):
        return (
            """<th>{0}</th>"""
        ).format(E(self.header_text))

    def make_values(self, a_card):
        if self.values.get(a_card.id):
            return """<td class="cb_true"> {0} </td>""".format(E(self.yes_text))
        else:
            return """<td class="cb_false"> {0} </td>""".format(E(self.no_text))

class CustomNumber(Datum):
    applicable_filters = []
    # can't be selected via url because only A-Za-z is allowed
    uid = "#"

    format = "{0}"
    header_text = ""

    def __init__(self, values, header_text="", format=None):
        self.header_text = header_text
        self.values = values

        if format is not None:
            self.format = "<td>" + format + "</td>"
        else:
            self.format = "<td>{0}</td>"

    def make_headers(self):
        return (
            """<th>{0}</th>"""
        ).format(E(self.header_text))

    def make_values(self, a_card):
        return self.format.format(self.values[a_card.id])

uid_to_cls = {V.uid: V for V in Datum.__subclasses__()}

###

# html injection is easier here, please be careful

def select_categories(s):
    cats = []
    for uid in s:
        cls = uid_to_cls.get(uid)
        if cls is None:
            continue
        cats.append(cls())

    fils = []

    for c in cats:
        fils.extend(c.applicable_filters)

    fils = sorted(set(fils))
    return fils, cats

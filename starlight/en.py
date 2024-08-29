import re
from html import escape

NO_STRING_FMT = "<语音 ID {0}:{1}:{2} 没有预设文本，但是你仍然可提交它的翻译。>"

def westernized_name(chara):
    """Our conventionals are ordered Last First, but project-imas uses First Last."""
    if " " in chara.kanji_spaced:
        # "The majority of Japanese people have one surname and one given name with no middle name,"
        # in case that proves false, here's an implementation that reverses
        # "Last First Middle" -> "First Middle Last".

        # names = chara.conventional.split(" ")
        # return "{0} {1}".format(" ".join(names[1:]), names[0]).strip()
        return " ".join(reversed(chara.conventional.split(" ")))
    else:
        return chara.conventional

def availability_date_range(a, now):
    if a.start.year == a.end.year:
        return "{0}{1} ~ {2}".format(
            a.start.strftime("%Y年"),
            a.start.strftime("%m月%d日"),
            a.end.strftime("%m月%d日") if a.end < now else "至今",
        )
    else:
        return "{0} ~ {1}".format(
            a.start.strftime("%Y年%m月%d日"),
            a.end.strftime("%Y年%m月%d日") if a.end < now else "至今",
        )

def gap_date_range(a):
    delta = (a.end - a.start)
    return "{0} ~ {1} (共 {2} 日)".format(
        a.start.strftime("%m月%d日"),
        a.end.strftime("%m月%d日"),
        round(delta.days + (delta.seconds / 86400))
    )

# skill describer


SKILL_DESCRIPTIONS = {
    1: """使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成""",
    2: """使所有PERFECT/GREAT音符获得 <span class="let">{0}</span>% 的分数加成""",
    3: """使所有PERFECT/GREAT/NICE音符获得 <span class="let">{0}</span>% 的分数加成""", #provisional
    4: """获得额外的 <span class="let">{0}</span>% 的COMBO加成""",
    5: """使所有GREAT音符改判为PERFECT""",
    6: """使所有GREAT/NICE音符改判为PERFECT""",
    7: """使所有GREAT/NICE/BAD音符改判为PERFECT""",
    8: """所有音符改判为PERFECT""", #provisional
    9: """使NICE音符不会中断COMBO""",
    10: """使BAD/NICE音符不会中断COMBO""", #provisional
    11: """使你的COMBO不会中断""", #provisional
    12: """使你的生命不会减少""",
    13: """使所有音符恢复你 <span class="let">{0}</span> 点生命""", #provisional
    14: """消耗 <span class="let">{1}</span> 生命，PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并且NICE/BAD音符不会中断COMBO""",
    15: """使所有PERFECT音符获得 <span class="let">{0}</span> % 的分数加成，且使PERFECT判定区间的时间范围缩小""", #provisional
    16: """重复发动上一个其他偶像发动过的技能""",
    17: """使所有PERFECT音符恢复你 <span class="let">{0}</span> 点生命""",
    18: """使所有PERFECT/GREAT音符恢复你 <span class="let">{0}</span> 点生命""", #provisional
    19: """使所有PERFECT/GREAT/NICE音符恢复你 <span class="let">{0}</span> 点生命""", #provisional
    20: """增强当前发动技能的效果""",
    21: """当仅有Cute偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    22: """当仅有Cool偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    23: """当仅有Passion偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    24: """获得额外的 <span class="let">{0}</span>% 的COMBO加成，并使所有PERFECT音符恢复你 <span class="let">{2}</span> 点生命""",
    25: """获得额外的<a href="/sparkle_internal/{0}">基于你当前生命值的COMBO加成</a>""",
    26: """当Cute、Cool和Passion偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成/恢复你 <span class="let">{3}</span> 点生命，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    27: """使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    28: """使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，长按音符获得 <span class="let">{2}</span>% 的分数加成""",
    29: """使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，滑块音符获得 <span class="let">{2}</span>% 的分数加成""",
    30: """使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，滑动音符获得 <span class="let">{2}</span>% 的分数加成""",
    31: """获得额外的 <span class="let">{0}</span>% 的COMBO加成，并使所有GREAT/NICE音符改判为PERFECT""",
    32: """增强Cute偶像的分数/COMBO加成技能的效果""",
    33: """增强Cool偶像的分数/COMBO加成技能的效果""",
    34: """增强Passion偶像的分数/COMBO加成技能的效果""",
    35: """使所有PERFECT音符获得<a href="/motif_internal/{0}?appeal=vocal">基于队伍Vocal表现值的分数加成</a>""",
    36: """使所有PERFECT音符获得<a href="/motif_internal/{0}?appeal=dance">基于队伍Dance表现值的分数加成</a>""",
    37: """使所有PERFECT音符获得<a href="/motif_internal/{0}?appeal=visual">基于队伍Visual表现值的分数加成</a>""",
    38: """全3种属性偶像存在于队伍时，增强当前发动分数加成、COMBO加成、生命恢复技能的效果""",
    39: """使COMBO加成减少 <span class="let">{0}</span>%，但同时获得增强 <span class="let">{2}</span>% 的【LIVE中发动过的最高的分数加成效果】""",
    40: """获得【LIVE中发动过的最高的分数加成/COMBO加成效果】""",
    41: """发动队伍内所有偶像的特技效果（类型重复取最高值）""",
    42: """使获得的分数减少<span class="let">{0}</span>%，但同时获得增强 <span class="let">{2}</span>% 的【LIVE中发动过的最高的COMBO加成效果】""",
    43: """to increase the combo bonus by <span class="let">{0}</span>%, and Perfect notes will restore <span class="let">{2}</span> life""",
    44: """that <span class="let">{1}</span> life will be consumed to increase the combo bonus by <span class="let">{2}</span>%, and Perfect note scores by <span class="let">{1}</span>%""",
    # Dominant variants
    45: """to boost the score bonus of Cute idols' active skills, and the combo bonus of Cool idols' active skills""",
    46: """to boost the score bonus of Cute idols' active skills, and the combo bonus of Passion idols' active skills""",
    47: """to boost the score bonus of Cool idols' active skills, and the combo bonus of Cute idols' active skills""",
    48: """to boost the score bonus of Cool idols' active skills, and the combo bonus of Passion idols' active skills""",
    49: """to boost the score bonus of Passion idols' active skills, and the combo bonus of Cute idols' active skills""",
    50: """to boost the score bonus of Passion idols' active skills, and the combo bonus of Cool idols' active skills""",
    51: """At the start of a live, sets life to <span class="let">200</span>% of its maximum and reduces all incoming damage by <span class="let">50</span>%."""
}

SKILL_CAVEATS = {
    15: "The timing window for Perfect notes will be smaller during this time.",
    21: "All idols on your team must be Cute types.",
    22: "All idols on your team must be Cool types.",
    23: "All idols on your team must be Passion types.",
    26: "Only when all three types of idols are on the team.",
    38: "Only when all three types of idols are on the team.",
    41: "Bonuses are subject to the conditions of each skill.",
    43: "Your combo will only continue on Perfect notes during this time.",
    44: "Only when playing an all-type song with all three types of idols on the team.",
    45: "Only when playing a Cool-type song with only Cute and Cool-type idols on the team.",
    46: "Only when playing a Passion-type song with only Cute and Passion-type idols on the team.",
    47: "Only when playing a Cute-type song with only Cool and Cute-type idols on the team.",
    48: "Only when playing a Passion-type song with only Cool and Passion-type idols on the team.",
    49: "Only when playing a Cute-type song with only Passion and Cute-type idols on the team.",
    50: "Only when playing a Cool-type song with only Passion and Cool-type idols on the team.",
    51: "Cannot be re-activated by the effect of Encore or Cinderella Magic."
}

SKILL_TRIGGER_DUAL_TYPE = {
    12: ("Cute", "Cool"),
    13: ("Cute", "Passion"),
    21: ("Cool", "Cute"),
    23: ("Cool", "Passion"),
    31: ("Passion", "Cute"),
    32: ("Passion", "Cool"),
}

SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1 = [1, 2, 3, 4, 14, 15, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 39, 42, 43, 44]
SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2 = [21, 22, 23, 26, 27, 28, 29, 30, 44]

# Whether the skill's description uses the value in a negative context
# (e.g. ...reduces by x%...)
SKILL_TYPES_WITH_NEGATIVE_EFF_VAL1 = [39, 42]
SKILL_TYPES_WITH_NEGATIVE_EFF_VAL2 = []

SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL1 = [20]
SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL2 = [39, 42]

SKILL_TYPES_WITH_GLOBAL_EFFECT = [51]

REMOVE_HTML = re.compile(r"</?(span|a)[^>]*>")

def describe_skill(skill):
    return REMOVE_HTML.sub("", describe_skill_html(skill))

def describe_lead_skill(lskill):
    return REMOVE_HTML.sub("", describe_lead_skill_html(lskill))

def skill_caveat_from_trigger_type(skill):
    if skill.skill_trigger_type == 6:
        pair = SKILL_TRIGGER_DUAL_TYPE.get(skill.skill_trigger_value, ("?", "?"))
        return "Only when team consists of just {0} and {1} idols.".format(*pair)

    return None

def skill_fallback_html(skill):
    return """{0} <span class="caveat">(Translated effects are not yet available for this skill.)</span>""".format(escape(skill.explain))

def describe_skill_html(skill):
    if skill is None:
        return "无效果"

    effect_fmt = SKILL_DESCRIPTIONS.get(skill.skill_type)
    if effect_fmt is None:
        return skill_fallback_html(skill)

    fire_interval = skill.condition
    effect_val = skill.value
    # TODO symbols
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1:
        effect_val -= 100
    elif skill.skill_type in SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL1:
        effect_val = (effect_val // 10) - 100

    if skill.skill_type in SKILL_TYPES_WITH_NEGATIVE_EFF_VAL1:
        effect_val = -effect_val

    value_2 = skill.value_2
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2:
        value_2 -= 100
    elif skill.skill_type in SKILL_TYPES_WITH_THOUSANDTHS_EFF_VAL2:
        value_2 = (value_2 // 10) - 100

    if skill.skill_type in SKILL_TYPES_WITH_NEGATIVE_EFF_VAL2:
        value_2 = -value_2

    value_3 = skill.value_3

    effect_clause = effect_fmt.format(effect_val, skill.skill_trigger_value, value_2, value_3)
    
    caveat_fmt = SKILL_CAVEATS.get(skill.skill_type)
    if caveat_fmt:
        caveat_clause = """<span class="caveat">（{0}）</span>""".format(caveat_fmt)
    else:
        caveat_clause = ""

    if skill.skill_type in SKILL_TYPES_WITH_GLOBAL_EFFECT:
        return " ".join((effect_clause, caveat_clause))

    interval_clause = """每 <span class="let">{0}</span> 秒，""".format(
        fire_interval)
    probability_clause = """有 <span class="var">{0}</span>% 的几率""".format(
        skill.chance())
    length_clause = """，持续 <span class="var">{0}</span> 秒。""".format(
        skill.dur())
    
    return "".join((interval_clause, probability_clause, effect_clause, length_clause, caveat_clause))


LEADER_SKILL_TARGET = {
    1: "所有Cute",
    2: "所有Cool",
    3: "所有Passion",
    4: "所有",

    11: "Cute属性",
    12: "Cool属性",
    13: "Passion属性",
    14: "所有属性",
}

LEADER_SKILL_PARAM = {
    1: "Vocal表现值",
    2: "Visual表现值",
    3: "Dance表现值",
    4: "所有表现值",
    5: "生命",
    6: "特技发动几率",
    # FIXME: only grammatically works when used in world level desc
    # FIXME: find variants for other stats
    13: "自身的Dance表现值"
}

def lead_skill_fallback_html(skill):
    return """{0} <span class="caveat">(暂无该技能的效果翻译。)</span>""".format(escape(skill.explain))
 
def build_lead_skill_predicate(skill):
    need_list = []
    need_sum = 0
    if skill.need_cute:
        need_list.append("Cute")
        need_sum += skill.need_cute
    if skill.need_cool:
        need_list.append("Cool")
        need_sum += skill.need_cool
    if skill.need_passion:
        need_list.append("Passion")
        need_sum += skill.need_passion

    if len(need_list) == 0:
        need_str = None
    elif len(need_list) == 1:
        need_str = need_list[0]
    elif len(need_list) == 2:
        need_str = "{0} 与 {1}".format(*need_list)
    else:
        need_str = "、".join(need_list[:-1])
        need_str = "{0}和{1}".format(need_str, need_list[-1])

    if len(need_list) < 3 and need_sum >= 5:
        need_str = "只有 " + need_str

    if skill.need_skill_variation > 1 and need_list:
        return """当队伍拥有至少 {1} 种不同的特技种类，且{0}属性的偶像存在于队伍时，""".format(need_str, skill.need_skill_variation)
    elif skill.need_skill_variation > 1:
        return """当队伍拥有至少 {0} 种不同的特技种类时，""".format(skill.need_skill_variation)
    elif need_list:
        return """当{0}属性的偶像存在于队伍时，""".format(need_str)
    else:
        return None

def describe_lead_skill_html(skill):
    if skill is None:
        return "无"

    if skill.up_type == 1 and skill.type == 20:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        effect_clause = """提升{1}偶像的{0} <span class="let">{2}</span>%""".format(
            target_param, target_attr, skill.up_value)
    elif skill.up_type == 1 and skill.type == 30:
        if skill.up_value == 12:
            # Riina
            effect_clause = "完成LIVE时，有几率掉落星光碎片（スター​ピース）。掉落率随星阶等级（スターランク）提升"
        else:
            effect_clause = "完成LIVE时，有几率获得额外奖励。掉落率随星阶等级（スターランク）提升"
    elif skill.up_type == 1 and skill.type == 40:
        effect_clause = "完成LIVE时，使获得粉丝数提高 <span class=\"let\">{0}</span>%".format(
            skill.up_value)
    elif skill.type == 50:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")

        effect_clause = """提升{1}偶像的{0} <span class="let">{2}</span>%，{4}偶像的{3} <span class="let">{5}</span>%""".format(
            target_param, target_attr, skill.up_value, target_param_2, target_attr_2, skill.up_value_2)
    elif skill.type == 60:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")

        if target_param_2 != target_param:
            effect_clause = """提升{1}偶像的{0} <span class="let">{2}</span>%（及进行{5}曲目的LIVE时提高 {3} <span class="let">{4}</span>%）""".format(
                target_param, target_attr, skill.up_value, target_param_2, skill.up_value_2, target_attr_2)
        else:
            effect_clause = """提升{1}偶像的{0} <span class="let">{2}</span>%（进行{4}曲目的LIVE时则为<span class="let">{3}</span>%）""".format(
                target_param, target_attr, skill.up_value, skill.up_value_2, target_attr_2)
    elif skill.type == 70:
        target_param = LEADER_SKILL_PARAM.get(skill.param_limit, "<unknown>")

        effect_clause = """在LIVE期间允许所有生效的特技效果叠加，但除 {0} 之外的所有表现值降低 100%""".format(
                target_param)
    elif skill.type == 80:
        effect_clause = """完成LIVE时，使获得的经验值/金钱/友情pt提高  <span class="let">{0}</span>%（Guest有效）""".format(
            skill.up_value)
    elif skill.type == 90:
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")
        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")
        effect_clause = """提高此卡{0} <span class="let">{1}</span>%。当面具打开时提高{3}成员的{2} <span class="let">{4}</span>%（需装备此卡服装，此卡为Guest时无效）""".format(
            target_param, skill.up_value, target_param_2, target_attr_2, skill.up_value_2)
    elif skill.type == 100:
        effect_clause = """发动包含Guest在内的队伍内所有偶像的领队技能（类型重复取最高值）"""
    elif skill.type == 110:
        song_attr = LEADER_SKILL_TARGET.get(skill.target_attribute_2 + 10, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")
        effect_clause = """提高所有卡牌的 {0} <span class="let">{1}</span>% 以及所有卡牌的 {2} <span class="let">{3}</span>% (当进行 {4} 类型的LIVE时)""".format(
            target_param, skill.up_value, target_param_2, skill.up_value_2, song_attr)
    elif skill.type == 120:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        target_attr_2 = LEADER_SKILL_TARGET.get(skill.target_attribute_2, "<unknown>")
        target_param_2 = LEADER_SKILL_PARAM.get(skill.target_param_2, "<unknown>")

        type_bonus_target = LEADER_SKILL_TARGET.get(skill.target_attribute + 10, "<unknown>")
        song_attr = LEADER_SKILL_TARGET.get(skill.target_attribute_2 + 10, "<unknown>")
        effect_clause = """Raise {2} of {3} cards by <span class="let">{4}%</span>, and {5} of {6} cards by <span class="let">{7}</span>%. {0} cards will also receive the type bonus from {1} songs""".format(
            type_bonus_target, song_attr, target_param, target_attr, skill.up_value, target_param_2, target_attr_2, skill.up_value_2)
    else:
        return lead_skill_fallback_html(skill)

    predicate_clause = build_lead_skill_predicate(skill)
    if predicate_clause:
        built = "".join((predicate_clause, effect_clause))
    else:
        built = effect_clause
    return built + "。"

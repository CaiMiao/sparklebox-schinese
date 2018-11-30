import csvloader
import functools
import os
import re

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
            a.start.strftime("%b%d日"),
            a.end.strftime("%b%d日") if a.end < now else "至今",
        )
    else:
        return "{0} ~ {1}".format(
            a.start.strftime("%Y年%b%d日"),
            a.end.strftime("%Y年%b%d日") if a.end < now else "至今",
        )

def gap_date_range(a):
    delta = (a.end - a.start)
    return "{0} ~ {1} (共 {2} 日)".format(
        a.start.strftime("%b%d日"),
        a.end.strftime("%b%d日"),
        round(delta.days + (delta.seconds / 86400))
    )

# skill describer


SKILL_DESCRIPTIONS = {
<<<<<<< HEAD
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
    20: """当前发动技能将被增强""",
    21: """当仅有Cute偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    22: """当仅有Cool偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    23: """当仅有Passion偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
    24: """获得额外的 <span class="let">{0}</span>% 的COMBO加成，并使所有PERFECT音符恢复你 <span class="let">{2}</span> 点生命""",
    25: """依据当前越多的生命值获得越多的额外COMBO加成""",
    26: """当Cute、Cool和Passion偶像存在于队伍时，使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成/恢复你 <span class="let">{3}</span> 点生命，并获得额外的 <span class="let">{2}</span>% 的COMBO加成""",
=======
    1: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus""",
    2: """that Great/Perfect notes will receive a <span class="let">{0}</span>% score bonus""",
    3: """that Nice/Great/Perfect notes will receive a <span class="let">{0}</span>% score bonus""", #provisional
    4: """that you will gain an extra <span class="let">{0}</span>% combo bonus""",
    5: """that Great notes will become Perfect notes""",
    6: """that Nice/Great notes will become Perfect notes""",
    7: """that Bad/Nice/Great notes will become Perfect notes""",
    8: """that all notes will become Perfect notes""", #provisional
    9: """that Nice notes will not break combo""",
    10: """that Bad/Nice notes will not break combo""", #provisional
    11: """that your combo will not be broken""", #provisional
    12: """that you will not lose health""",
    13: """that all notes will restore <span class="let">{0}</span> health""", #provisional
    14: """that <span class="let">{1}</span> life will be consumed, then: Perfect notes receive a <span class="let">{0}</span>% score bonus, and Nice/Bad notes will not break combo""",
    15: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, but become harder to hit""", #provisional
    16: """to activate the previous skill again""",
    17: """that Perfect notes will restore <span class="let">{0}</span> health""",
    18: """that Great/Perfect notes will restore <span class="let">{0}</span> health""", #provisional
    19: """that Nice/Great/Perfect notes will restore <span class="let">{0}</span> health""", #provisional
    20: """that currently active skills will be boosted""",
    21: """that with only Cute idols on the team, Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    22: """that with only Cool idols on the team, Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    23: """that with only Passion idols on the team, Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
    24: """that you will gain an extra <span class="let">{0}</span>% combo bonus, and Perfect notes will restore <span class="let">{2}</span> health""",
    25: """that you will gain an extra combo bonus based on your current health""",
    26: """that with all three types of idols on the team, you will gain an extra <span class="let">{2}</span>% combo bonus, and Perfect notes will receive a <span class="let">{0}</span>% score bonus plus restore <span class="let">{3}</span> HP,""",
    27: """that Perfect notes will receive a <span class="let">{0}</span>% score bonus, and you will gain an extra <span class="let">{2}</span>% combo bonus""",
>>>>>>> 40078afdabfaa4f3058879444f1bae06085d5690
}

SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1 = [1, 2, 3, 4, 14, 15, 21, 22, 23, 24, 26, 27]
SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2 = [21, 22, 23, 26, 27]

REMOVE_HTML = re.compile(r"</?span[^>]*>")

def describe_skill(skill):
    return REMOVE_HTML.sub("", describe_skill_html(skill))

def describe_lead_skill(lskill):
    return REMOVE_HTML.sub("", describe_lead_skill_html(lskill))

def describe_skill_html(skill):
    if skill is None:
        return "无效果"

    fire_interval = skill.condition
    effect_val = skill.value
    # TODO symbols
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL1:
        effect_val -= 100
    elif skill.skill_type in [20]:
        effect_val = (effect_val//10) - 100

    value_2 = skill.value_2
    if skill.skill_type in SKILL_TYPES_WITH_PERCENTAGE_EFF_VAL2:
        value_2 -= 100
    value_3 = skill.value_3

    effect_clause = SKILL_DESCRIPTIONS.get(
        skill.skill_type, "").format(effect_val, skill.skill_trigger_value, value_2, value_3)
    interval_clause = """每 <span class="let">{0}</span> 秒，""".format(
        fire_interval)
    probability_clause = """有 <span class="var">{0}</span>% 的几率""".format(
        skill.chance())
    length_clause = """，持续 <span class="var">{0}</span> 秒。""".format(
        skill.dur())

    return "".join((interval_clause, probability_clause, effect_clause, length_clause))


LEADER_SKILL_TARGET = {
    1: "所有Cute",
    2: "所有Cool",
    3: "所有Passion",
    4: "所有",
}

LEADER_SKILL_PARAM = {
    1: "Vocal表现值",
    2: "Visual表现值",
    3: "Dance表现值",
    4: "所有表现值",
    5: "生命",
    6: "特技发动几率",
}

def build_lead_skill_predicate(skill):
    need_list = []
    if skill.need_cute:
        need_list.append("Cute")
    if skill.need_cool:
        need_list.append("Cool")
    if skill.need_passion:
        need_list.append("Passion")

    if not need_list:
        return None

    if len(need_list) == 1:
        need_str = need_list[0]
    else:
        need_str = "、".join(need_list[:-1])
        need_str = "{0}和{1}".format(need_str, need_list[-1])

    # FIXME: consider values of need_x in leader_skill_t
    #   Rei_Fan49 - Today at 5:36 PM
    #   princess and focus only works for single color
    #   it requires 5 or 6 per color
    #   which implies monocolor team or no activation
    #   cinfest team requires 1 each color (according to internal data)
    if len(need_list) < 3:
        need_str = "只有" + need_str

    predicate_clause = """当{0}属性的偶像存在于队伍时，""".format(need_str)
    return predicate_clause

def describe_lead_skill_html(skill):
    if skill is None:
        return "无"

    if skill.up_type == 1 and skill.type == 20:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        effect_clause = """提升{1}偶像的{0} <span class="let">{2}</span>%。""".format(
            target_param, target_attr, skill.up_value)

        predicate_clause = build_lead_skill_predicate(skill)
        if predicate_clause:
            built = "".join((predicate_clause, effect_clause))
        else:
            built = effect_clause
        return built
    elif skill.up_type == 1 and skill.type == 30:
        effect_clause = "完成LIVE时，额外获得特别奖励"

        predicate_clause = build_lead_skill_predicate(skill)
        if predicate_clause:
            built = "".join((predicate_clause, effect_clause))
        else:
            built = effect_clause + "。"
        return built
    elif skill.up_type == 1 and skill.type == 40:
        effect_clause = "完成LIVE时，使获得粉丝数提高 <span class=\"let\">{0}</span>%".format(
            skill.up_value)

        predicate_clause = build_lead_skill_predicate(skill)
        if predicate_clause:
            built = " ".join((effect_clause, predicate_clause))
        else:
            built = effect_clause + "。"
        return built
    else:
        return """此队长技能的内部描述格式未定义，请汇报此BUG。(up_type: {0}, type: {1})""".format(
            skill.up_type, skill.type
        )

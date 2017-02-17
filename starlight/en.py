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
    15: """使所有PERFECT音符获得 <span class="let">{0}</span>% 的分数加成，并且只有PERFECT才能继续COMBO""", #provisional
    16: """会发生有趣的事情""", #provisional
    17: """使所有PERFECT音符恢复你 <span class="let">{0}</span> 点生命""",
    18: """使所有PERFECT/GREAT音符恢复你 <span class="let">{0}</span> 点生命""", #provisional
    19: """使所有PERFECT/GREAT/NICE音符恢复你 <span class="let">{0}</span> 点生命""", #provisional
    24: """获得额外的 <span class="let">{0}</span>% 的COMBO加成，并使所有PERFECT音符恢复你 <span class="let">{2}</span> 点生命""",
}

REMOVE_HTML = re.compile(r"</?span[^>]*>")

def describe_skill(skill):
    return REMOVE_HTML.sub("", describe_skill_html(skill))

def describe_lead_skill(lskill):
    return REMOVE_HTML.sub("", describe_lead_skill_html(lskill))

def describe_skill_html(skill):
    if skill is None:
        return "No effect"

    fire_interval = skill.condition
    effect_val = skill.value
    # TODO symbols
    if skill.skill_type in [1, 2, 3, 4, 14, 24]:
        effect_val -= 100

    effect_clause = SKILL_DESCRIPTIONS.get(
        skill.skill_type, "").format(effect_val, skill.skill_trigger_value, skill.value_2)
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

def describe_lead_skill_html(skill):
    if skill is None:
        return "无"

    if skill.up_type == 1 and skill.type == 20:
        target_attr = LEADER_SKILL_TARGET.get(skill.target_attribute, "<unknown>")
        target_param = LEADER_SKILL_PARAM.get(skill.target_param, "<unknown>")

        effect_clause = """提升{1}偶像的{0} <span class="let">{2}</span>%。""".format(
            target_param, target_attr, skill.up_value)

        need_list = []
        if skill.need_cute:
            need_list.append("Cute")
        if skill.need_cool:
            need_list.append("Cool")
        if skill.need_passion:
            need_list.append("Passion")

        if need_list:
            need_str = "、".join(need_list[:-1])
            need_str = "{0}和{1}".format(need_str, need_list[-1])
            predicate_clause = """当{0}属性的偶像存在于队伍时，""".format(need_str)
            built = "".join((predicate_clause, effect_clause))
        else:
            built = effect_clause
        return built
    else:
        return """此队长技能的内部描述格式未定义，请将此汇报为BUG。(up_type: {0}, type: {1})""".format(
            skill.up_type, skill.type
        )

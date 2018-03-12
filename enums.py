import models

def enum(kv):
    i = iter(kv)
    dic = dict(zip(i, i))
    rev = {v: k for k, v in dic.items()}

    def f(key):
        return dic.get(key, "<missing string: {0}>".format(key))
    def _reverse_enum(val):
        return rev[val]
    f.value_for_description = _reverse_enum
    return f

rarity = enum([
    1, "Normal",
    2, "Normal+",
    3, "Rare",
    4, "Rare+",
    5, "SR",
    6, "SR+",
    7, "SSR",
    8, "SSR+",
])

attribute = enum([
    1, "Cute",
    2, "Cool",
    3, "Passion",
    4, "Office",
])

skill_type = enum([
    1, "PERFECT分数加成",
    2, "分数加成",
    3, "分数加成",

    4, "COMBO加成",

    5, "初级强判",
    6, "中级强判",
    7, "高级强判",
    8, "无条件强判",

    9, "COMBO保护",
    10, "高级COMBO保护",
    11, "无条件COMBO保护",

    12, "锁血",
    13, "无条件补血",
    14, "过载",

    15, "专注",
    16, "返场",

    17, "恢复生命",
    18, "恢复生命",
    19, "恢复生命",

    20, "技能增强",

    21, "Cute集中",
    22, "Cool集中",
    23, "Passion集中",

    24, "全才",
    25, "生命闪耀",
    26, "三色协同"
])

skill_probability = enum([
    2, "小概率",
    3, "中概率",
    4, "高概率",
])

skill_length_type = enum([
    1, "一瞬间",
    2, "较短时间",
    3, "短时间",
    4, "稍长时间",
    5, "较长时间",
])

lskill_target = enum([
    1, "所有Cute",
    2, "所有Cool",
    3, "所有Passion",
    4, "所有",
])

lskill_effective_target = enum([
    1, "ca_cute",
    2, "ca_cool",
    3, "ca_passion",
    4, "ca_all",
])

lskill_param = enum([
    1, "Vocal表现值",
    2, "Visual表现值",
    3, "Dance表现值",
    4, "全表现值",
    5, "生命",
    6, "技能发动概率",
])

lskill_effective_param = enum([
    1, "ce_vocal",
    2, "ce_visual",
    3, "ce_dance",
    4, "ce_anyappeal",
    5, "ce_life",
    6, "ce_skill",
])

api_char_type = enum([
    1, "cute",
    2, "cool",
    3, "passion",
    4, "office"
])

lskill_target_attr = enum([
    1, "cute",
    2, "cool",
    3, "passion",
    4, "all",
])

lskill_target_param = enum([
    1, "vocal",
    2, "visual",
    3, "dance",
    4, "all",
    5, "life",
    6, "skill_probability",
])

skill_class = enum([
    1, "s_scorebonus",
    2, "s_scorebonus",
    3, "s_scorebonus",

    4, "s_combobonus",

    5, "s_pl",
    6, "s_pl",
    7, "s_pl",
    8, "s_pl",

    9, "s_cprot",
    10, "s_cprot",
    11, "s_cprot",

    12, "s_life",
    13, "s_heal",
    14, "s_overload",

    15, "s_perfelegant",
    16, "s_mimic",

    17, "s_heal",
    18, "s_heal",
    19, "s_heal",

    20, "s_sb",

    21, "s_focus",
    22, "s_focus",
    23, "s_focus",

    24, "s_allround",
    25, "s_cbonus_based_life",
    26, "s_synergy"
])

stat_dot = enum([
    1, "m_vi",
    2, "m_da",
    3, "m_vo",
    4, "m_ba",
    5, "m_ba",
    6, "m_ba",
    7, "m_ba",
])

stat_en = enum([
    1, "这张卡数值最高的是Visual",
    2, "这张卡数值最高的是Dance",
    3, "这张卡数值最高的是Vocal",
    4, "这张卡数值较为均衡",
    5, "这张卡数值较为均衡（Visual较高）",
    6, "这张卡数值较为均衡（Dance较高）",
    7, "这张卡数值较为均衡（Vocal较高）"
])

floor_rarity = enum([
    1, "n",
    2, "n",
    3, "r",
    4, "r",
    5, "sr",
    6, "sr",
    7, "ssr",
    8, "ssr",
])

he_event_class = enum([
    models.EVENT_TYPE_TOKEN, "hev_token",
    models.EVENT_TYPE_CARAVAN, "hev_caravan",
    models.EVENT_TYPE_GROOVE, "hev_groove",
    models.EVENT_TYPE_PARTY, "hev_party",
    models.EVENT_TYPE_TOUR, "hev_tour",
])

# TODO need enum defs for
# constellation
# blood_type
# hand
# personality
# home_town

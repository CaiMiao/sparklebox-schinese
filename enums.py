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
    26, "三色协同",
    27, "协调",
    28, "PERFECT分数加成",
    29, "PERFECT分数加成",
    30, "PERFECT分数加成",
    31, "调音",

    32, "Cute合奏",
    33, "Cool合奏",
    34, "Passion合奏",

    35, "Vocal片断",
    36, "Dance片断",
    37, "Visual片断",

    38, "三色和音",
    39, "轮替 <Alt.>",
    40, "副歌 <Refr.>",
    
    41, "灰姑娘魔法",
    42, "呼应 <Mut.>",
    43, "Overdrive",
    44, "Tricolor Spike",

    45, "Dominant Harmony",
    46, "Dominant Harmony",
    47, "Dominant Harmony",
    48, "Dominant Harmony",
    49, "Dominant Harmony",
    50, "Dominant Harmony",

    51, "灰姑娘礼物",
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
    1, "scoreup",
    2, "scoreup",
    3, "scoreup",

    4, "cboost",

    5, "plock",
    6, "plock",
    7, "plock",
    8, "plock",

    9, "cguard",
    10, "cguard",
    11, "cguard",

    12, "hguard",
    13, "heal",
    14, "overload",

    15, "concentrate",
    16, "encore",

    17, "heal",
    18, "heal",
    19, "heal",

    20, "skillboost",

    21, "focus",
    22, "focus",
    23, "focus",

    24, "allround",
    25, "sparkle",
    26, "synergy",
    27, "focus_flat",
    28, "psb_hold",
    29, "psb_flick",
    30, "psb_slide",
    31, "tuning",

    32, "skillboost",
    33, "skillboost",
    34, "skillboost",
    35, "motif",
    36, "motif",
    37, "motif",

    38, "symphony",
    39, "alternate",
    40, "refrain",
    
    41, "magic",
    
    42, "mutual",
    43, "overdrive",
    44, "spike",

    45, "dominant",
    46, "dominant",
    47, "dominant",
    48, "dominant",
    49, "dominant",
    50, "dominant",

    51, "present",
])

stat_dot = enum([
    1, "visual",
    2, "dance",
    3, "vocal",
    4, "balance",
    5, "balance",
    6, "balance",
    7, "balance",
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

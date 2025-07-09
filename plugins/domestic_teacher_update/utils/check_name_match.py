import pandas as pd
import itertools
import unicodedata
from pypinyin import pinyin, Style
from itertools import product
import re


#移除字符串中的重音符号
def remove_accents(input_str):
    normalized_str = unicodedata.normalize('NFD', input_str)
    return ''.join(c for c in normalized_str if unicodedata.category(c) != 'Mn')

#拼音分割函数
def segment_pinyin(pinyin_text):
    # 完整的拼音音节列表，不含声调
    pinyin_syllables = [
        'ai', 'an', 'ang', 'ao',
        'ba', 'bai', 'ban', 'bang', 'bao', 'bei', 'ben', 'beng', 'bi', 'bian', 'biao',
        'bie', 'bin', 'bing', 'bo', 'bu',
        'ca', 'cai', 'can', 'cang', 'cao', 'ce', 'cen', 'ceng', 'cha', 'chai',
        'chan', 'chang', 'chao', 'che', 'chen', 'cheng', 'chi', 'chong', 'chou',
        'chu', 'chuai', 'chuan', 'chuang', 'chui', 'chun', 'chuo',
        'ci', 'cong', 'cou', 'cu', 'cuan', 'cui', 'cun', 'cuo',
        'da', 'dai', 'dan', 'dang', 'dao', 'de', 'dei', 'den', 'deng', 'di', 'dian',
        'diao', 'die', 'ding', 'diu', 'dong', 'dou', 'du', 'duan', 'dui', 'dun', 'duo',
        'en', 'er',
        'fa', 'fan', 'fang', 'fei', 'fen', 'feng', 'fo', 'fou', 'fu',
        'ga', 'gai', 'gan', 'gang', 'gao', 'ge', 'gei', 'gen', 'geng', 'gong', 'gou', 'gu',
        'gua', 'guai', 'guan', 'guang', 'gui', 'gun', 'guo',
        'ha', 'hai', 'han', 'hang', 'hao', 'he', 'hei', 'hen', 'heng', 'hong', 'hou', 'hu',
        'hua', 'huai', 'huan', 'huang', 'hui', 'hun', 'huo',
        'ji', 'jia', 'jian', 'jiang', 'jiao', 'jie', 'jin', 'jing', 'jiong', 'jiu', 'ju',
        'juan', 'jue', 'jun',
        'ka', 'kai', 'kan', 'kang', 'kao', 'ke', 'ken', 'keng', 'kong', 'kou', 'ku',
        'kua', 'kuai', 'kuan', 'kuang', 'kui', 'kun', 'kuo',
        'la', 'lai', 'lan', 'lang', 'lao', 'le', 'lei', 'leng', 'li', 'lia', 'lian',
        'liang', 'liao', 'lie', 'lin', 'ling', 'liu', 'long', 'lou', 'lu', 'lv',
        'luan', 'lue', 'lun', 'luo',
        'ma', 'mai', 'man', 'mang', 'mao', 'me', 'mei', 'men', 'meng', 'mi', 'mian',
        'miao', 'mie', 'min', 'ming', 'miu', 'mo', 'mou', 'mu',
        'na', 'nai', 'nan', 'nang', 'nao', 'ne', 'nei', 'nen', 'neng', 'ni', 'nian',
        'niang', 'niao', 'nie', 'nin', 'ning', 'niu', 'nong', 'nou', 'nu', 'nv',
        'nuan', 'nue', 'nuo',
        'ou',
        'pa', 'pai', 'pan', 'pang', 'pao', 'pei', 'pen', 'peng', 'pi', 'pian', 'piao',
        'pie', 'pin', 'ping', 'po', 'pu',
        'qi', 'qia', 'qian', 'qiang', 'qiao', 'qie', 'qin', 'qing', 'qiong', 'qiu', 'qu',
        'quan', 'que', 'qun',
        'ran', 'rang', 'rao', 're', 'ren', 'reng', 'ri', 'rong', 'rou', 'ru',
        'rua', 'ruan', 'rui', 'run', 'ruo',
        'sa', 'sai', 'san', 'sang', 'sao', 'se', 'sen', 'seng', 'sha', 'shai',
        'shan', 'shang', 'shao', 'she', 'shen', 'sheng', 'shi', 'shou', 'shu',
        'shua', 'shuai', 'shuan', 'shuang', 'shui', 'shun', 'shuo',
        'si', 'song', 'sou', 'su', 'suan', 'sui', 'sun', 'suo',
        'ta', 'tai', 'tan', 'tang', 'tao', 'te', 'teng', 'ti', 'tian', 'tiao',
        'tie', 'ting', 'tong', 'tou', 'tu', 'tuan', 'tui', 'tun', 'tuo',
        'wa', 'wai', 'wan', 'wang', 'wei', 'wen', 'weng', 'wo', 'wu',
        'xi', 'xia', 'xian', 'xiang', 'xiao', 'xie', 'xin', 'xing', 'xiong', 'xiu', 'xu',
        'xuan', 'xue', 'xun',
        'ya', 'yan', 'yang', 'yao', 'ye', 'yi', 'yin', 'ying', 'yo', 'yong', 'you',
        'yu', 'yuan', 'yue', 'yun',
        'za', 'zai', 'zan', 'zang', 'zao', 'ze', 'zei', 'zen', 'zeng', 'zha', 'zhai',
        'zhan', 'zhang', 'zhao', 'zhe', 'zhen', 'zheng', 'zhi', 'zhong', 'zhou',
        'zhu', 'zhua', 'zhuai', 'zhuan', 'zhuang', 'zhui', 'zhun', 'zhuo',
        'zi', 'zong', 'zou', 'zu', 'zuan', 'zui', 'zun', 'zuo'
    ]

    # 按音节长度从长到短排序
    pinyin_syllables.sort(key=lambda x: -len(x))

    def max_forward_matching(pinyin_string):
        pinyin_string = pinyin_string.lower()
        index = 0
        segments = []
        while index < len(pinyin_string):
            matched = False
            for syllable in pinyin_syllables:
                length = len(syllable)
                if pinyin_string[index:index + length] == syllable:
                    segments.append(syllable)
                    index += length
                    matched = True
                    break
            if not matched:
                return []
                # # 处理点号与前面字母组合的情况
                # if index > 0 and pinyin_string[index] == '.' and segments:
                #     segments[-1] += '.'
                #     index += 1
                # else:
                #     # 未匹配到音节，可能是拼写错误或特殊情况，这里可以选择跳过或处理
                #     # 当前示例中，跳过一个字符
                #     segments.append(pinyin_string[index])
                #     index += 1
        return segments

    pinyin_text = pinyin_text.replace('-', '').replace(' ', '').replace(',', '')
    syllables = max_forward_matching(pinyin_text)

    return syllables

#枚举所有可能的姓氏
def split_surname(name_parts):
    name_variants = []
    n = len(name_parts)
    # 2. 枚举姓氏：前缀或后缀连续的 1 ~ n-1 个单词作为姓氏
    for i in range(1, n):  # i 表示姓氏的单词数量
        # 前缀作为姓氏
        prefix_surname = " ".join(name_parts[:i])  # 从头开始取 i 个单词作为姓氏
        first_name = " ".join(name_parts[i:])  # 剩余部分为名字
        if first_name:
            name_variants.append(f"[{prefix_surname}] {first_name}")  # 添加结果

        # 后缀作为姓氏
        suffix_surname = " ".join(name_parts[-i:])  # 从末尾开始取 i 个单词作为姓氏
        first_name = " ".join(name_parts[:-i])  # 剩余部分为名字
        if first_name:
            name_variants.append(f"[{suffix_surname}] {first_name}")  # 添加结果

    return sorted(set(name_variants))  # 去重并排序
#按照[]取出姓名, []中是姓, 其他部分是名
def split_by_brackets(input_string):
    # 使用正则表达式匹配方括号及其内容
    match = re.match(r"\[(.*?)]\s*(.*)", input_string)
    if match:
        surname = match.group(1).strip()  # 方括号内的内容（姓氏）
        remaining = match.group(2).strip()  # 方括号后的内容（名字）
        return surname, remaining
    return None, input_string  # 如果没有匹配到方括号，返回原字符串作为剩余部分
#对名字部分做处理，将可以拼接的部分拼接到一起
def merge_adjacent_words(variant):
    new_variants = []
    words = variant.split(" ")  # 将字符串按空格分隔为单词列表
    n = len(words)
    if n < 2:
        return words

    # 遍历每种拼接长度（从 2 到 n 个单词拼接）
    for merge_length in range(2, n + 1):  # 修正为 n+1，包含 n 个单词拼接的情况
        # 遍历所有可能的拼接起始位置
        for i in range(n - merge_length + 1):
            # 拼接从第 i 个开始的 merge_length 个单词
            merged_words = words[:i] + ["".join(words[i:i + merge_length])] + words[i + merge_length:]
            new_variants.append(" ".join(merged_words))  # 拼接为字符串

    # 加入原始形式
    new_variants.append(variant)

    return sorted(set(new_variants))  # 去重并排序
#对名字做缩写处理，缩写带点
def add_abbreviations_point(name_variants):
    new_variants = set(name_variants)  # 初始化结果集合，保留输入的原始值

    for variant in name_variants:
        words = variant.split(" ")  # 将字符串按空格分隔为单词列表
        n = len(words)

        # 保留原始输入形式
        new_variants.add(variant)

        if n == 1:  # 如果只有一个单词
            new_variants.add(words[0][0] + ".")  # 直接缩写为首字母加点
        else:
            # 遍历单词全写的组合情况（包括所有单词缩写）
            for r in range(0, n + 1):  # r 表示全写单词的数量（包括全缩写 r=0）
                for full_indices in itertools.combinations(range(n), r):  # 选择 r 个单词全写
                    abbreviated_variant = [
                        word if j in full_indices else word[0] + "." for j, word in enumerate(words)
                    ]
                    new_variants.add(" ".join(abbreviated_variant))

            # 处理相邻多个缩写连在一起的变体
            for r in range(2, n + 1):  # 至少两个单词的组合
                for start_index in range(n - r + 1):  # 起始位置
                    # 检查组合中的单词是否都能缩写
                    if all(len(words[start_index + i]) > 1 for i in range(r)):  # 确保长度 > 1 的单词
                        abbreviated_variant = [
                            words[start_index + i][0] + "." for i in range(r)
                        ]  # 缩写相邻的 r 个单词
                        merged_abbreviation = "".join(abbreviated_variant)  # 合并缩写单词
                        # 构建新的变体
                        new_variant = (
                            " ".join(words[:start_index]) +  # 前部分
                            (" " + merged_abbreviation if merged_abbreviation else "") +  # 连在一起的缩写
                            " " + " ".join(words[start_index + r:])  # 后部分
                        ).strip()  # 去掉多余空格
                        new_variants.add(new_variant)

    return new_variants
#对名字做缩写处理，缩写不带点
def add_abbreviations_no_point(name_variants):
    processed_variants = set(name_variants)  # 初始化结果集合，保留输入的原始值

    for variant in name_variants:
        if "." in variant:
            # 去掉所有的点但保留空格
            variant_without_dots = " ".join([part.replace(".", "") for part in variant.split(" ")])
            processed_variants.add(variant_without_dots)
    return processed_variants
#对名字做缩写处理，缩写部分带点
def add_abbreviations_part_point(name_variants):
    new_variants = set(name_variants)  # 初始化结果集合，保留输入的原始值

    for variant in name_variants:
        if "." not in variant:
            continue  # 跳过不包含点的变体

        words = variant.split(" ")  # 按空格分隔为单词列表

        # 处理单词中点部分去除的变体
        for i, word in enumerate(words):
            if "." in word:
                dot_positions = [pos for pos, char in enumerate(word) if char == "."]
                total_dots = len(dot_positions)

                # 去掉 1 到 total_dots-1 个点
                for r in range(1, total_dots):  # 去掉的点数量
                    for remove_indices in itertools.combinations(dot_positions, r):  # 点的组合
                        trimmed_word = list(word)
                        for index in remove_indices:
                            trimmed_word[index] = ""  # 去掉指定位置的点
                        partially_trimmed = "".join(trimmed_word)
                        new_variant = " ".join(words[:i] + [partially_trimmed] + words[i + 1:])
                        new_variants.add(new_variant)

        # 完全去掉点的变体
        for r in range(1, len(words) + 1):  # 遍历从 1 到 len(words) 的缩写组合
            for dotted_indices in itertools.combinations(range(len(words)), r):  # 选择保留点的单词索引
                new_variant = [
                    word if i in dotted_indices else word.replace(".", "")
                    for i, word in enumerate(words)
                ]
                processed_variant = " ".join(new_variant)
                new_variants.add(processed_variant)

    return new_variants
#给名字加上连字符，暂时只处理两个单词和多个单词的情况
def add_variants_with_hyphen(name_variants):
    new_variants = set(name_variants)  # 初始化结果集合，保留输入的原始值

    for variant in name_variants:
        words = variant.split(" ")  # 按空格分隔为单词列表

        # 两个单词的情况
        if len(words) == 2:
            first, second = words
            new_variants.add(f"{first}-{second}")  # 将空格替换为连字符
            new_variants.add(f"{first} -{second}")  # 在第二个单词前加连字符

        # 多个单词的情况
        elif len(words) > 2:
            for i in range(len(words) - 1):  # 遍历每个空格位置
                merged_with_hyphen = words[:i] + [words[i] + "-" + words[i + 1]] + words[i + 2:]
                new_variants.add(" ".join(merged_with_hyphen))  # 插入连字符的形式

    return sorted(new_variants)  # 去重并排序
#处理姓氏和名字的组合
def generate_name_combinations(name_dict, is_chinese):
    name_variants = set()  # 用于存放组合结果

    for surname, names in name_dict.items():  # 遍历姓氏和名字列表
        for name in names:  # 遍历每个名字
            # 四种组合方式
            name_variants.add(f"{surname}, {name}")  # 姓，名
            name_variants.add(f"{surname} {name}")  # 姓 名
            name_variants.add(f"{name}, {surname}")  # 名，姓
            name_variants.add(f"{name} {surname}")  # 名 姓
            # 中国人加上以下情况
            if is_chinese:
                name_variants.add(f"{name}{surname}")  # 名姓
                name_variants.add(f"{surname}{name}")  # 姓名

    return name_variants

#对输入的姓名处理生成变体
def generate_name_variants_by_one(full_name):
    name_variants = []
    # 1. 按照空格、连字符或逗号分隔，分割姓名单词
    final_name_parts = []
    # 去掉姓名中的',', '-'
    processed_name = full_name.replace(',', ' ').replace('-', ' ')
    # 按空格进行划分
    name_parts = re.split(r'\s+', processed_name.strip())
    is_chinese = False
    # print(name_parts)
    # 1.1 如果长度小于等于2，则需要处理拼音的情况  比如 li shudong, Hiroyuki Kusuhara -> ['h', 'i', 'r', 'o', 'yu', 'k', 'i', 'ku', 'su', 'ha', 'r', 'a']
    #     处理拼音后的结果：1.长度等于2 直接手动枚举结果 2.长度等于3 使用拼音处理后的结果进行后续处理 3. 如果长度大于3或者等于1，直接使用原始的name_parts进行处理
    pinyin_segment_res = segment_pinyin(processed_name)
    if len(pinyin_segment_res) == 2:
        first_name = pinyin_segment_res[0]
        last_name = pinyin_segment_res[1]
        name_variants.extend([
            f"{first_name} {last_name}",
            f"{last_name} {first_name}",
            f"{first_name}{last_name}", # 中国人加上
            f"{last_name}{first_name}", # 中国人加上
            f"{first_name}, {last_name}",
            f"{last_name}, {first_name}",
            f"{first_name} {last_name[0]}",
            f"{last_name} {first_name[0]}",
            f"{first_name} {last_name[0]}.",
            f"{last_name} {first_name[0]}.",
            f"{first_name}, {last_name[0]}",
            f"{last_name}, {first_name[0]}",
            f"{first_name}, {last_name[0]}.",
            f"{last_name}, {first_name[0]}.",
            f"{first_name[0]} {last_name}",
            f"{last_name[0]} {first_name}",
            f"{first_name[0]}. {last_name}",
            f"{last_name[0]}. {first_name}",
            f"{first_name[0]}, {last_name}",
            f"{last_name[0]}, {first_name}",
            f"{first_name[0]}., {last_name}",
            f"{last_name[0]}., {first_name}",
        ])
        return name_variants
    elif len(pinyin_segment_res) > 0 and len(pinyin_segment_res) <= 5:  # 处理出现复姓的情况
        final_name_parts = pinyin_segment_res
        is_chinese = True
    else:
        final_name_parts = name_parts

    # 2. 按照姓氏进行分隔 枚举姓氏
    split_res = split_surname(final_name_parts)

    # 3. 对名字进行拼接处理
    name_dict = {}
    for tmp_name in split_res:
        surname, name = split_by_brackets(tmp_name)
        res = merge_adjacent_words(name)
        name_dict[surname] = res

    #4. 对姓进行处理
    #4.1 在姓氏间添加连字符的情况 4.2 对姓氏进行拼接的情况，不考虑部分拼接
    for key in list(name_dict.keys()):  # 遍历所有姓氏
        parts = re.split(r'\s+', key.strip())  # 按空格分割姓氏

        #4.2 对姓氏进行拼接的情况，不考虑部分拼接
        if len(parts) > 1:  # 如果姓氏包含多个单词
            # 新增拼接的姓氏变体
            concatenated_surname = "".join(parts)  # 将所有单词直接拼接
            if concatenated_surname not in name_dict:  # 避免覆盖已有键
                name_dict[concatenated_surname] = name_dict[key]

        #4.1 在姓氏间添加连字符的情况
        # 处理两个单词的情况
        if len(parts) == 2:
            new_name = parts[0] + '-' + parts[1]
            name_dict[new_name] = name_dict[key]

        # 处理多个单词的情况
        elif len(parts) > 2:
            for i in range(len(parts) - 1):  # 遍历每个空格位置
                merged_with_hyphen = parts[:i] + [parts[i] + '-' + parts[i + 1]] + parts[i + 2:]
                new_name = " ".join(merged_with_hyphen)
                name_dict[new_name] = name_dict[key]

    #4.3 存在姓氏前缀时，省略部分前缀名的情况（少见）
    #TODO


    #5. 对名进行缩写处理
    #5.1 先对名字做带点的缩写
    for key, value in list(name_dict.items()):
        name_dict[key] = add_abbreviations_point(value)
    #5.2 再处理不带点的缩写情况
    for key, value in list(name_dict.items()):
        name_dict[key] = add_abbreviations_no_point(value)
    #5.3 最后处理部分带点的缩写情况
    for key, value in list(name_dict.items()):
        name_dict[key] = add_abbreviations_part_point(value)
    #
    #6. 名字加上连字符
    for key, value in list(name_dict.items()):
        name_dict[key] = add_variants_with_hyphen(value)
    #
    # #7. 姓与名进行组合
    name_variants = generate_name_combinations(name_dict, is_chinese)
    if full_name.lower() not in name_variants:
        name_variants.add(full_name.lower())

    return name_variants

def generate_name_variants(ori_full_name):
    full_name = ori_full_name.strip()
    # 1. 去掉姓名中的重音符号, ',', '-'
    full_name = remove_accents(full_name)
    processed_name = full_name.replace(',', ' ').replace('-', ' ')
    # 2. 按空格进行划分
    name_parts = re.split(r'\s+', processed_name.strip())

    final_res = {ori_full_name.lower(), full_name.lower()}  # 使用集合存储所有变体，避免重复

    # 3. 判断是否存在 'Jr.' 或 'Jr' 并生成对应变体
    if 'Jr.' in name_parts or 'Jr' in name_parts:
        # 移除 'Jr.' 或 'Jr'
        filtered_name_parts = [part for part in name_parts if part not in {'Jr.', 'Jr'}]
        new_name = " ".join(filtered_name_parts)
        # print('new_name:', new_name)
        final_res.add(new_name.lower())
        final_res.update(generate_name_variants_by_one(new_name))

    # print('full_name:', full_name)
    # 4. 生成包含 'Jr.' 或 'Jr' 的原始姓名变体
    final_res.update(generate_name_variants_by_one(full_name))

    # 5. 姓名统一转换成小写
    final_res = {name.lower() for name in final_res}
    # print("姓---名")
    # for k, v in name_dict.items():
    #     print(k, "---", v)
    # print(name_variants, len(name_variants))

    return final_res

# 测试
# full_name = "Little, L." #"Jorge Humberto Rodriguez Quintero" "Celeste González de Bustamante" "Monica Olvera de la Cruz" "Robert J. Jackson, Jr." "Little, Jr., Arthur L."
# variants = generate_name_variants(full_name)
#
#
# print(variants)
# for item in variants:
#     if full_name.lower() == item:
#         print(True)
# print(len(variants))



# 定义复姓列表
compound_surnames = ['欧阳', '司马', '上官', '诸葛', '夏侯', '东方', '皇甫', '尉迟', '澹台', '令狐', '宇文', '长孙', '慕容', '司徒', '司空', '端木', '百里', '东郭', '呼延', '西门']


# 名字转换只做一遍
def chinese_name_to_pinyin(chinese_name):
    # 维吾尔族
    if '·' in chinese_name:
        out = []
        parts = chinese_name.split('·')
        for p in parts:
            cn_name = ''.join(p)
            pinyin_list = pinyin(cn_name, style=Style.NORMAL, strict=False)
            pinyin_name = [word[0] for word in pinyin_list]
            out.append(''.join(pinyin_name))
        return set([' '.join(out)])

    # 检查复姓
    for surname in compound_surnames:
        if chinese_name.startswith(surname):
            chinese_name = chinese_name.replace(',', '').replace('，', '').replace(' ', '')
            surname_pinyin = ''.join([word[0] for word in pinyin(surname, style=Style.NORMAL, strict=False)])
            given_name = chinese_name[len(surname):]
            given_name_pinyin = ''.join([word[0] for word in pinyin(given_name, style=Style.NORMAL, strict=False)])
            possible_names = [
                f"{surname_pinyin}, {given_name_pinyin}",
                f"{surname_pinyin} {given_name_pinyin}",
                f"{given_name_pinyin}, {surname_pinyin}",
                f"{given_name_pinyin} {surname_pinyin}"
            ]
            return set(possible_names)

    # 提取拼音并进行格式化
    pinyin_result = pinyin(chinese_name, style=Style.NORMAL, heteronym=True)
    # print(pinyin_result)
    combinations = list(product(*pinyin_result))
    # print(combinations)
    # 过滤掉包含空格或空字符串的组合元素
    valid_combinations = []
    for comb in combinations:
        filtered_comb = [p for p in comb if p.strip() and ', ' != p and ',' != p and '，' != p and '， ' != p]  # 移除空格和空字符串
        if filtered_comb:  # 确保组合不为空
            valid_combinations.append(tuple(filtered_comb))
    

    # print(valid_combinations)
    # 多种排列方式生成
    possible_names = []
    for pinyin_name in valid_combinations:
        if len(pinyin_name) == 1:
            return set([pinyin_name[0].lower()])

        # 处理两字姓名情况
        if len(pinyin_name) == 2:
            last_name = pinyin_name[0]
            first_name = pinyin_name[1]
            possible_names += [
                f"{last_name}, {first_name}",
                f"{first_name}, {last_name}",
                f"{last_name}{first_name}",
                f"{last_name} {first_name}",
                f"{first_name} {last_name}",
                # f"{last_name}, {first_name[0]}.",
                # f"{first_name}, {last_name[0]}."
            ]
        # 处理三字姓名情况
        elif len(pinyin_name) == 3:
            first_name = pinyin_name[0]  # 第一个字为姓 wu
            last_name_1 = f"{pinyin_name[1]}-{pinyin_name[2]}"  # ya-qi
            last_name_2 = f"{pinyin_name[1]}{pinyin_name[2]}"  # yaqi
            possible_names += [
                f"{first_name}, {last_name_1}",
                f"{first_name}, {last_name_2}",
                f"{first_name}{last_name_1}",
                f"{first_name}{last_name_2}",
                f"{first_name} {last_name_1}",
                f"{first_name} {last_name_2}",
                f"{pinyin_name[0]} {pinyin_name[1]} {pinyin_name[2]}",
                f"{last_name_2} {first_name}",
                f"{last_name_2}, {first_name}",
                f"{last_name_2}{first_name}",
                f"{last_name_1}, {first_name}",
                f"{last_name_1} {first_name}",
                f"{last_name_1}{first_name}"
                # f"{first_name}, {pinyin_name[1][0]}. {pinyin_name[2][0]}.",
                # f"{first_name}, {pinyin_name[1][0]}{pinyin_name[2][0]}"
            ]

            first_name = f"{pinyin_name[0]}{pinyin_name[1]}"  # 前两个字为姓  wuya
            first_name_2 = f"{pinyin_name[0]}-{pinyin_name[1]}"  # 前两个字为姓 wu-ya
            last_name = pinyin_name[2]  # qi
            possible_names += [
                f"{first_name}, {last_name}",
                f"{first_name} {last_name}",
                f"{first_name_2}, {last_name}",
                f"{first_name_2} {last_name}"
                # f"{first_name}, {last_name[0]}.",
                # f"{first_name} {last_name[0]}.",
                # f"{first_name_2}, {last_name[0]}.",
                # f"{first_name_2} {last_name[0]}." 
            ]
        # 处理多字姓名情况（>=4个字）
        elif len(pinyin_name) >= 4:
            last_name_1 = pinyin_name[0]  # 第一个字为姓
            first_name_1 = ''.join(pinyin_name[1:])  # 其余字为名
            last_name_2 = ''.join(pinyin_name[:2])  # 前两个字为姓
            first_name_2 = ''.join(pinyin_name[2:])  # 后两个字为名
            possible_names += [
                f"{first_name_1}, {last_name_1}",
                f"{last_name_1}, {first_name_1}",
                f"{first_name_2}, {last_name_2}",
                f"{last_name_2}, {first_name_2}",
                f"{first_name_2} {last_name_2}",
                f"{last_name_2} {first_name_2}"
            ]
    # 小写
    return set(possible_names)


def contains_chinese(s):
    # 判断字符串是否包含中文，且检查类型
    if not isinstance(s, str):
        return True
    pattern = re.compile(r'[\u4e00-\u9fff]+')
    return bool(pattern.search(s))


def chinese_name_to_hanzi(input_name):
    # 检查复姓
    for surname in compound_surnames:
        if input_name.startswith(surname):
            input_name = input_name.replace(',', '').replace('，', '').replace(' ', '')
            given_name = input_name[len(surname):]
            possible_names = [
                f"{surname}, {given_name}",
                f"{surname} {given_name}",
                f"{given_name}, {surname}",
                f"{given_name} {surname}"
            ]
            return set(possible_names)
        
    input_name = re.sub(r'\s+', '', input_name).strip()
    input_name = input_name.replace(',', '').replace('，', '').replace(' ', '')
    surname = input_name[0]
    given_name = input_name[1:]
    # print(surname, given_name)
    possible_names = [
        f"{surname}, {given_name}",
        f"{surname} {given_name}",
        f"{given_name}, {surname}",
        f"{given_name} {surname}"
    ]
    return set(possible_names)

def get_chinese_name(input_name):
    if contains_chinese(input_name):
        # # 中文汉字姓名变体
        res = chinese_name_to_hanzi(input_name)
        # 中文拼音名字变体
        res.update(chinese_name_to_pinyin(input_name))
        res.add(input_name)

        return res

# if __name__ == '__main__':
#     input_name = '郭灿阳'
#     res = get_chinese_name(input_name)
#     print(res)



def contains_chinese(s):
    """判断字符串是否包含中文或非字符串类型"""
    if not isinstance(s, str):
        return True
    return bool(re.search(r'[\u4e00-\u9fff]', s))

def remove_parentheses(text):
    """移除所有中英文括号及其内容（支持混合括号）"""
    if '(' not in text and ')' not in text and '（' not in text and '）' not in text:
        return text  # 无任何括号，直接返回
    
    result = []
    skip = False  # 标记是否跳过当前字符
    
    for char in text:
        # 处理左括号（中英文）
        if char in '(（':
            skip = True
        # 处理右括号（中英文）
        elif char in ')）':
            skip = False
            continue  # 不添加右括号本身
        # 跳过括号内的字符
        if skip:
            continue
        # 添加括号外的字符
        result.append(char)
    res_str = ''.join(result)
    res_str = re.sub(r'\s+', ' ', res_str).strip()
    return res_str

def generate_name_set(name):
    """生成姓名的变体集合（处理中文/英文姓名）"""
    # 预处理：移除括号内容
    processed_name = remove_parentheses(str(name))
    
    # 根据语言类型生成变体
    if contains_chinese(processed_name):
        return set(get_chinese_name(processed_name))
    else:
        return set(generate_name_variants(processed_name))

def check_name_match(ext_name, der_name):
    if contains_chinese(ext_name) and contains_chinese(der_name):
        return None

    """检查两个姓名是否匹配（基于变体集合的交集）"""
    ext_names = generate_name_set(ext_name)
    der_names = generate_name_set(der_name)
    
    # 两个集合存在交集则判定为匹配
    return not ext_names.isdisjoint(der_names)


# print(check_name_match('楼燕','YAN LUO'))

# def check_name_match(row):
#     """检查两个姓名是否匹配（基于变体集合的交集）"""
#     ext_names = generate_name_set(row['extracted_teacher_name'])
#     der_names = generate_name_set(row['derived_teacher_name'])
    
#     # 两个集合存在交集则判定为匹配
#     return not ext_names.isdisjoint(der_names)

# df = pd.read_csv('./姓名比对数据.csv')

# # 使用apply高效处理每行数据
# tqdm.pandas(desc="Processing names")
# df['is_same'] = df.progress_apply(check_name_match, axis=1)

# # 筛选结果列并保存
# df = df[['extracted_teacher_name', 'derived_teacher_name', 'is_same']]
# print(f"匹配成功的记录数: {len(df[df['is_same'] == True])}")
# df.to_csv('./姓名比对结果.csv')
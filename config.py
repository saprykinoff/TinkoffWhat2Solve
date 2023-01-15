import os

if os.getenv('what2solve', 'release') == 'rlease':
    token = '???'
    isdebug = False
    print('Debug mode set to false')
    dir_path = "/home/ubuntu/dev/tgen_what2solve-main"
else:
    token = '????'
    isdebug = True
    print('Debug mode set to true')
    dir_path = "logs"

process_name = "what2solve"
admins = [472209097, 552514677]
paths = {
    "logs": dir_path + "/logs/",
    "user_saves": dir_path + "/user_saves/",
    "reboot_script": dir_path + "/reboot.py"
}
for path in paths.keys():
    if not os.path.exists(path):
        os.makedirs(path)

# параллель -- ссылки
table_links_dict = {
    "a20f": ["https://algocode.ru/standings_data/a_fall2020"],
    "aspb20": ["https://algocode.ru/standings_data/aspb2020"],
    "apspb20": ["https://algocode.ru/standings_data/aprimespb2020"],
    "ap20f": ["https://algocode.ru/standings_data/ap_fall2020"],
    "ap20s": ["https://algocode.ru/standings_data/ap_spring2021"],
    "b20f": ["https://algocode.ru/standings_data/b_fall2020"],
    "b20s": ["https://algocode.ru/standings_data/b_spring2020"],
    "bp20f": ["https://algocode.ru/standings_data/bp_fall2020"],
    "bp20s": ["https://algocode.ru/standings_data/bp_spring2021"],
    "c20f": ["https://algocode.ru/standings_data/c_fall2020"],
    "c20s": ["https://algocode.ru/standings_data/c_spring2021"],
    "a19f": ["https://algocode.ru/standings_data/37"],
    "a19s": ["https://algocode.ru/standings_data/70"],
    "ap19": ["https://algocode.ru/standings_data/41"],
    "b19f": ["https://algocode.ru/standings_data/45"],
    "b19s": ["https://algocode.ru/standings_data/72"],
    "bp19f": ["https://algocode.ru/standings_data/76"],
    "bp19s": ["https://algocode.ru/standings_data/73"],
    "bprzn19": ["https://algocode.ru/standings_data/46"],
    "aprnd19": ["https://algocode.ru/standings_data/59"],
    "aspb19": ["https://algocode.ru/standings_data/55"],
    "cizh19": ["https://algocode.ru/standings_data/61"],
    "cekb19": ["https://algocode.ru/standings_data/56"],
    "apekb19": ["https://algocode.ru/standings_data/57"],
    "bpekb19": ["https://algocode.ru/standings_data/60"],
    "bekb19": ["https://algocode.ru/standings_data/63"],
    "a18f": ["https://algocode.ru/standings_data/1"],
    "a18s": ["https://algocode.ru/standings_data/3"],
    "c18s": ["https://algocode.ru/standings_data/6"],
    "c19f": ["https://algocode.ru/standings_data/43"],
    "c19s": ["https://algocode.ru/standings_data/69"]}
groups = list(table_links_dict.keys())
default_param = {'groups': ['bp20s']}  # дефолтные параметры

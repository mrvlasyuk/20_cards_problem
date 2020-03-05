import glob
import random
import numpy as np
import itertools as it
from tabulate import tabulate
from subprocess import check_call

ICONS = "icons/"
QUESTION_ICON = ICONS + "empty.svg"

colors = ("red", "green", "blue")
shape = ("wave", "circle", "square")
fill = ("strips", "flood", "none")
numbers = ("1", "2", "3")

all_props = dict(colors=colors, shape=shape, fill=fill, numbers=numbers)

DECK = list(it.product(colors, shape, fill, numbers))

THIRD_GOOD_PROP = {} 
for key in all_props:
    props = all_props[key]
    for i in range(3):
        for j in range(3):
            THIRD_GOOD_PROP[(props[i], props[j])] = props[(6 - j - i) % 3]

def is_good_comb(cards):
    assert len(cards) == 3
    for q_ix in range(4):
        qualities = [c[q_ix] for c in cards]
        if len(set(qualities)) == 2:
            return False
    return True

def get_num_of_sets(cards):
    num_sets = 0
    for cards_3 in it.combinations(cards, 3):
        num_sets += is_good_comb(cards_3)
    return num_sets
            
def find_3rd_card(card_a, card_b):
    return tuple([THIRD_GOOD_PROP[(a, b)] for a, b in zip(card_a, card_b)])

def calc_not_allowed_cards(cards):
    return set(find_3rd_card(a, b) for a, b in it.permutations(cards, 2))
    
def score_cards_to_remove(cards):
    cards = set(cards)
    res = {c: len(calc_not_allowed_cards(cards - {c})) for c in cards} 
    return sorted(res.items(), key=lambda x: x[1])

def score_cards_to_add(cards):
    cards = set(cards)
    rest = set(DECK) - set(calc_not_allowed_cards(cards)) - cards
    res = {c: len(calc_not_allowed_cards(cards | {c})) for c in rest} 
    return sorted(res.items(), key=lambda x: x[1])

def select_top_and_choice(results):
    results = sorted(results, key=lambda x: x[1])
    results = [x for x in results if x[1] == results[0][1]]
    return random.choice(results)[0]


def find_20_cards():
    cards = set()

    while len(cards) < 20:
        cards = set()
        epoch = 0
        max_len = 0
        while len(cards) < 20 and epoch < 100:
            to_add = score_cards_to_add(cards)
            epoch += 1
            if to_add:
                cards.add(select_top_and_choice(to_add))
            else:
                for _ in range(2):
                    to_del = score_cards_to_remove(cards)
                    cards.remove(select_top_and_choice(to_del))
    return cards

#############  HTML generation  #############

def generate_path(card, base=ICONS):
    color, shape, fill, num = card
    color = dict(red="r", green="g", blue="p")[color]
    shape = dict(square="D", wave="S", circle="P")[shape]
    fill = dict(flood="S", none="O", strips="H")[fill]
    
    return f"{base}/{num}{fill}{color}{shape}.svg"

def get_img_tag(path):
    return f'<img src="{path}"/>'

def gen_tag_for_card(card):
    return get_img_tag(generate_path(card))


def make_html(cards):
    cards = list(cards)
    random.shuffle(cards)
    # cards = sorted(cards, key=lambda x: x[1])
    tags = np.array([gen_tag_for_card(c) for c in cards])
    tags = tags.reshape(-1, 5)
    tags[-1][-1] = get_img_tag(QUESTION_ICON)

    html = "<html><body> \n"
    html += "<div style='font-size:110px; color:white'>You have 120 mins left</div><br>"
    html += "<style> body{ background-color: #000000;}</style>\n"
    html += tabulate(tags, tablefmt="html")
    html += "</body></html>"
    return html, cards[-1]


if __name__ == "__main__":
    cards = find_20_cards()
    assert get_num_of_sets(cards) == 0
    print(tabulate(cards)) 

    html, removed_card = make_html(cards)

    with open("index.html", "w") as f:
        f.write(html)

    screenshot_name = "_".join(removed_card) + ".png"
    check_call(['"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --screenshot --window-size=1600,1800 --default-background-color=0 index.html'], shell=True)
    # check_call([f"mkdir -p pics; mv screenshot.png pics/{screenshot_name}"], shell=True)
    check_call([f"open screenshot.png"], shell=True)



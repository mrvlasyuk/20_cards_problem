import glob
import random
import numpy as np
from PIL import Image
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


##############   Nice card shuffle   ##########

def calc_neibors_indexes(x_len, y_len):
    indexes = np.array(list(it.product(range(x_len), range(y_len))))
    all_neibors = set()
    for a in indexes:
        for b in indexes:
            if abs(a - b).sum() in (1, 2):
                neibors = sorted([tuple(a), tuple(b)])
                all_neibors.add(tuple(neibors))
    return all_neibors

NEIBORS = calc_neibors_indexes(4, 5)

def shuffle_score(cards):
    def cards_dist(card_a, card_b):
        return sum([x == y for (x, y) in zip(card_a, card_b)])
    cards = np.array(cards).reshape(-1, 5, 4)
    score = sum(cards_dist(cards[ix_a], cards[ix_b]) for ix_a, ix_b in NEIBORS) 
    return score

def find_best_shuffle(cards, n_iters):
    best_shuffle = None
    best_shuffle_score = 1e9
    cards = list(cards)
    for i in range(n_iters):
        random.shuffle(cards)
        score = shuffle_score(cards)
        if score < best_shuffle_score:
            best_shuffle_score = score
            best_shuffle = list(cards)
    return best_shuffle, score

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
    html += "<div style='font-size:110px; color:white'>Prove you're not a robot</div><br><br>"
    html += "<style> body{ background-color: #010101;}</style>\n"
    html += tabulate(tags, tablefmt="html")
    html += "</body></html>"
    return html, cards[-1]


#############  Image processsing  #############

def make_color_transparent(img, rgba):
    data = np.array(img.convert('RGBA'))
    mask = True
    for ix, color in enumerate(rgba):
        mask = (data[:, :, ix] == color) & mask

    data[mask] = 0
    return Image.fromarray(data)

def make_image_from_html(in_html, out_file):
    check_call([f'"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --screenshot --window-size=1800,1800 --default-background-color=0 {in_html}'], shell=True)

    img = Image.open("screenshot.png")
    img = make_color_transparent(img, (1, 1, 1))
    img.save("screenshot.png")
    check_call([f"mkdir -p pics; mv screenshot.png pics/{screenshot_name}"], shell=True)
    check_call([f"open pics/{screenshot_name}"], shell=True)


if __name__ == "__main__":
    cards = find_20_cards()
    assert get_num_of_sets(cards) == 0
    cards, shuffle_score = find_best_shuffle(cards, 1000)
    print(f"shuffle_score = {shuffle_score}")
    print(tabulate(cards))

    html, removed_card = make_html(cards)
    with open("index.html", "w") as f:
        f.write(html)

    screenshot_name = "_".join(removed_card) + ".png"
    make_image_from_html("index.html", screenshot_name)
    



import re
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

class Checklist(object):
    def __init__(self, path):
        self.file = open(path, 'r')
        self.sport = None
        self.product = None
        self.year = None
        self.codes = {}
        self.checklists = defaultdict(dict)
        self.comc_cache = {}
        self.parse()

    def parse(self):
        insert = "base"
        code_definitions = {'X': {'name': "Base", 'color': 'black'}}
        for line in self.file.readlines():
            if not line.strip():
                continue

            # special line defining special attributes
            if line.startswith("#"):
                if line.startswith("#product: "):
                    self.product = line[10:].strip()
                elif line.startswith("#year: "):
                    self.year = int(line[7:])
                elif line.startswith("#sport: "):
                    self.sport = line[8:].strip()
                elif '=' in line:
                    code, args_ = line[1:].split("=")

                    argz = args_.strip().split(" ")
                    color = 'black' if len(argz) <= 1 else argz[1]

                    code_definitions[code.strip()] = {
                        'name': argz[0].strip(),
                        'color': color
                    }

                elif line.startswith("#insert: "):
                    insert = line[9:].strip()
                    code_definitions = {'X': {'name': insert}}
                continue

            # normal line with player and codes
            number, codes, name = line.split("|")

            for code in code_definitions.keys():
                quantity = 1
                if code not in codes:
                    quantity = 0

                set_name = code_definitions[code]['name']
                self.checklists[set_name][number.strip()] = {
                    'player_name': name.strip(),
                    'quantity': quantity,
                    'price': None
                }

    def get_card_info_from_comc(self, set):
        if set in self.comc_cache:
            return self.comc_cache[set]

        url = self.get_comc_url(set)

        print "fetching from comc..."
        doc = requests.get(url)
        print "...done"
        parsed = BeautifulSoup(doc.content, "html.parser")

        infos = parsed.find_all(class_="cardInfoWrapper")

        datas = {}
        for card in infos:
            number = card.find(class_="description").text.strip().split("#")[-1]
            datas[number] = {
                'price': card.find(class_="listprice").find('a').text,
                'player_name': card.find(class_="title").text.strip(),
            }

        self.comc_cache[set] = datas
        return datas

    def get_comc_url(self, set):
        if set not in self.checklists:
            raise Exception("Invalid Code")

        return "https://www.comc.com/Cards/{sport}/{year}/{product}_-_{set},i100".format(
            sport=self.sport,
            year=self.year,
            product=self.product,
            set=set
        )

    def get_total_size_of_set(self, set):
        return len(self.checklists[set])

    def get_want_list(self, set, with_price=False):
        return self._get_list('want', set, with_price)

    def get_have_list(self, set, with_price=False):
        return self._get_list('have', set, with_price)

    def _get_list(self, type, set, with_price=False):
        cards = {}
        for number, data in self.checklists[set].items():
            if (type == 'want' and data['quantity'] == 0) or (
            type == 'have' and data['quantity'] > 0):
                cards[number] = data

        if with_price:
            info = self.get_card_info_from_comc(set)
            for num, data in cards.items():
                data['price'] = info[num]['price'] if num in info else None

        return cards

    def average_card_price(self, set):
        info = self.get_card_info_from_comc(set)
        total_cost = 0
        total_hits = 0
        for card in info.values():
            p = card['price']
            if p:
                total_cost += float(p[1:])
                total_hits += 1
        return total_cost / total_hits


    def show_want_list(self, set, with_price=False):
        cards = self.get_want_list(set, with_price)
        return self._show('want', set, cards, with_price)

    def show_have_list(self, set, with_price=False):
        cards = self.get_have_list(set, with_price)
        return self._show('have', set, cards, with_price)

    def _show(self, type, set, cards, with_price=False):
        print "%s list for: %s %s %s" % (
            type.title(), self.year, self.product, set.replace("_", ' ')
        )

        total = self.get_total_size_of_set(set)
        total_in = len(cards)
        total_out = total - total_in
        total_price = 0
        total_on_comc = 0

        for num, card in sorted(cards.items(), key=lambda x: x[0]):
            price = card['price']
            if price:
                total_on_comc += 1
                total_price += float(price[1:])

            print "%s %s %s" % (
                num.ljust(4), (price or '').ljust(5), card['player_name']
            )

        if type == 'want':
            tag = 'are missing'
            final = "Cost to get to %.1f%% complete: $%.2f"
            after_comc = (total_out + total_on_comc) * 100 / float(total)
        else:
            tag = "have"
            final = "You can sell your entire %scollection for $%.2f"
            after_comc = ''

        print "You %s %s out of %s (%.1f%%)" % (
            tag, total_in, total, total_in * 100 / float(total)
        )

        if with_price:
            print "Total cards on Comc: %s" % total_on_comc
            print final % (after_comc, total_price)

    def show_intersections(self, set, card_numbers, with_price=False):
        total = len(card_numbers)
        wants = self.get_want_list(set, with_price)
        haves = self.get_have_list(set, with_price)

        have_count = 0
        need_count = 0
        total_have_price = 0
        haves_on_comc = 0
        total_need_price = 0
        needs_on_comc = 0

        for card in card_numbers:
            c = str(card)
            if c in wants:
                need_count += 1
                p = wants[c]['price']
                if p:
                    total_need_price += float(p[1:])
                    needs_on_comc += 1
                print "+ Need", c.ljust(3), (p or '').ljust(6), wants[c]['player_name']
            elif c in haves:
                have_count += 1
                p = haves[c]['price']
                if p:
                    total_have_price += float(p[1:])
                    haves_on_comc += 1
                print "- Have", c.ljust(3), (p or '').ljust(6), haves[c]['player_name']

        print "======"
        print "You need %d, and you have %d out of a total of %d cards." % (
            need_count, have_count, total
        )
        if with_price:
            print "Value of haves: $%.2f (%d missing), Value of needs: $%.2f (%d missing)" % (
                total_have_price, total_need_price, have_count - haves_on_comc,
                need_count - needs_on_comc
            )
        print "Dupe rate: %.2f%%," % (100 * float(have_count) / total),
        print "Fill rate: %.2f%%" % (100 * float(need_count) / total),

c = Checklist("/Users/chrispriest/BaseballCards/Panini Cooperstown/2013.txt")
#c.show_want_list("Base", True)
#c.show_intersections("Base_-_Crystal_Collection", [
#    4,7,9,11,17,22,31,34,42,43,46,50,51,52,57,61,65,70,71,76,77,80,87,90,94,97,100,
#    106, 109,118,119,120,122,123,125,127,135,137,145,150,159,199

#    4, 9, 11, 13, 14, 19, 20, 26, 28, 32, 33, 36, 41, 42, 47, 50, 54, 56, 58, 59,
#    60, 62, 65, 66, 67, 69, 70, 77, 80, 81, 82, 86, 88, 92, 98, 100, 102, 104,
#    106, 107, 113, 115, 117, 119, 121, 126, 127, 129, 130, 133, 136, 137, 138,
#    141, 142, 143, 144, 145, 148

#], with_price=True)


print c.show_want_list("Base_-_Green_Crystal_Shard", with_price=False)

#print c.average_card_price("Base_-_Crystal_Collection")
#print c.get_comc_url("X")
#print c.get_comc_url("Y")

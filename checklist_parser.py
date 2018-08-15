import re
from collections import defaultdict
from comc import Comc

class Checklist(object):
    def __init__(self, path):
        self.file = open(path, 'r')
        self.sport = None
        self.product = None
        self.year = None

        # key is set, value is list of cards and quantities, etc.
        self.checklists = defaultdict(dict)

        # cached utility for fetching data on comc.
        self.comc = Comc()
        self.parse()

    def fetch_set_data(self, set):
        if set not in self.checklists:
            raise Exception("Invalid set name")
        return self.comc.fetch_set_data(self.sport, self.year, self.product, set)

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
            info = self.fetch_set_data(set)
            for num, data in cards.items():
                data['price'] = info[num]['price'] if num in info else None

        return cards

    def average_card_price(self, set):
        info = self.fetch_set_data(set)
        total_cost = 0
        total_hits = 0
        for card in info.values():
            p = card['price']
            if p:
                total_cost += p
                total_hits += 1
        return total_cost / total_hits

    def percentage_filled(self, set, verbose=False):
        total = self.get_total_size_of_set(set)
        haves = len(self.get_have_list(set))
        if verbose: print "You have %d out of %d" % (haves, total)
        return haves / float(total)

    def percentage_missing(self, set, verbose=False):
        total = self.get_total_size_of_set(set)
        wants = len(self.get_want_list(set))
        if verbose: print "You are missing %d out of %d" % (wants, total)
        return wants / float(total)

    def wants_comc_unlisted(self, set):
        wants = self.get_want_list(set, True)
        wnloc = [x for x in wants.values() if not x['price']]

    def haves_comc_unlisted(self, set):
        haves = self.get_have_list(set, True)
        hnloc = [x for x in haves.values() if not x['price']]

    def comc_report(self, set, verbose=True):
        wants = self.get_want_list(set, True)
        haves = self.get_have_list(set, True)

        wloc = [x for x in wants.values() if x['price']]
        wnloc = [x for x in wants.values() if not x['price']]

        hloc = [x for x in haves.values() if x['price']]
        hnloc = [x for x in haves.values() if not x['price']]

        average_list_price = (
            sum(x['price'] for x in wloc + hloc) / len(wloc + hloc)
        )

        cost_to_buyout = sum(x['price'] for x in wloc)
        value_from_sellout =  sum(x['price'] * x['quantity'] for x in hloc)

        ret = {
            "wants_listed_on_comc": len(wloc),
            "wants_not_listed_on_comc": len(wnloc),
            "haves_listed_on_comc": len(hloc),
            "haves_not_listed_on_comc": len(hnloc),
            "cost_to_buyout": cost_to_buyout,
            "value_from_sellout": value_from_sellout,
            "average_list_price": average_list_price,

            "estimated_value": sum(
                x['quantity'] * average_list_price for x in hnloc
            ) + value_from_sellout,

            "estimated_cost_to_complete": (average_list_price * len(wnloc)) + cost_to_buyout
        }

        if verbose:
            print "Estimated value of your collection: $%.2f (%.1f%% unlisted)" % (
                ret['estimated_value'], 100.0 * len(hnloc) / len(hloc)
            )
            print "Estimated cost to complete: $%.2f (%.1f%% unlisted)" % (
                ret['estimated_cost_to_complete'], 100.0 * len(wnloc) / len(wloc)
            )
            print "Estimation based on: $%.2f per card." % average_list_price

        return ret

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

        # sorted by card number
        sorted_cards = sorted(cards.items(), key=lambda x: x[0])

        for num, card in sorted_cards:
            if not with_price:
                print "%s %s %s" % (
                    num.ljust(4), card['player_name']
                )
            else:
                p = ("$%.2f" % card['price']) if card['price'] else ''
                print "%s %s %s" % (
                    num.ljust(4),
                    p.ljust(5),
                    card['player_name']
                )

        total_in_set = self.get_total_size_of_set(set)

        print "You %s %d cards out of %d in the set" % (
            "need" if type == 'want' else "have",
            len(cards), total_in_set
        )
        remaining = total_in_set - len(cards)
        print "You %s %d cards (%.1f%%)" % (
             "have" if type == 'want' else "need",
            remaining, 100 * remaining / float(total_in_set)
        )

        if with_price:
            self.comc_report(set, verbose=True)


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
        print "Fill rate: %.2f%%" % (100 * float(need_count) / total)

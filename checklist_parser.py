from __future__ import print_function

import re
from collections import defaultdict
from comc import Comc
from natsort import natsorted

class Checklist(object):
    def __init__(self, path):
        self.file = open(path, 'r')
        self.sport = None
        self.product = None
        self.year = None

        self.subsets = []

        # key is set, value is list of cards and quantities, etc.
        self.checklists = self.parse()

        # cached utility for fetching data on comc.
        self.comc = Comc()

    def fetch_set_data(self, set):
        if set not in self.checklists:
            raise Exception("Invalid set name")
        return self.comc.fetch_set_data(self.sport, self.year, self.product, set)

    def parse(self):
        checklists = defaultdict(dict)
        current_subset = {}
        for line in self.file.readlines():
            if not line.strip():
                continue # skip blank lines

            # special line defining special attributes
            if line.startswith("#"):
                if line.startswith("# product: "):
                    self.product = line[10:].strip()
                elif line.startswith("# year: "):
                    self.year = int(line[7:])
                elif line.startswith("# sport: "):
                    self.sport = line[8:].strip()
                elif '=' in line:
                    code, args_ = line[1:].split("=")

                    argz = args_.strip().split(" ")
                    color = 'black' if len(argz) <= 1 else argz[1]
                    name = argz[0].strip()

                    current_subset[name] = {
                        'code': code.strip(),
                        'color': color
                    }
                    self.subsets += current_subset
                continue

            if not current_subset: # allow first base definition to be implicit
                current_subset = {'Base': {'code': "X", 'color': 'black'}}
                self.subsets += current_subset

            # normal line with player and codes
            number, codes, player_name = line.split("|")

            for set_name, data in current_subset.items():
                quantity = 1
                if data['code'] not in codes:
                    quantity = 0

                checklists[set_name][number.strip()] = {
                    'player_name': player_name.strip(),
                    'quantity': quantity,
                    'price': None # will get filled in later
                }

        return checklists



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
        if verbose: print("You have %d out of %d" % (haves, total))
        return haves / float(total)

    def percentage_missing(self, set, verbose=False):
        total = self.get_total_size_of_set(set)
        wants = len(self.get_want_list(set))
        if verbose: print("You are missing %d out of %d" % (wants, total))
        return wants / float(total)

    def wants_comc_unlisted(self, set):
        wants = self.get_want_list(set, True)
        return [x for x in wants.values() if not x['price']]

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
            if len(haves):
                unlisted = "(%.1f%% unlisted)" % (100.0 * len(hnloc) / len(hloc))
                print("Estimated value of your collection: $%.2f %s" % (
                    ret['estimated_value'], unlisted
                ))
            print("Estimated cost to complete: $%.2f (%.1f%% unlisted)" % (
                ret['estimated_cost_to_complete'], 100.0 * len(wnloc) / len(wloc)
            ))
            print("Estimation based on: $%.2f per card." % average_list_price)

        return ret

    def show_want_list(self, set, with_price=False):
        cards = self.get_want_list(set, with_price)
        return self._show('want', set, cards, with_price)

    def show_have_list(self, set, with_price=False):
        cards = self.get_have_list(set, with_price)
        return self._show('have', set, cards, with_price)

    def _show(self, type, set, cards, with_price=False):
        print("%s list for: %s %s %s" % (
            type.title(), self.year, self.product.replace("_", ' '),
            set.replace("_", ' ')
        ))

        # sorted by card number
        sorted_cards = natsorted(cards.items(), key=lambda x: x[0])

        for num, card in sorted_cards:
            if not with_price:
                print("%s %s" % (
                    num.ljust(4), card['player_name']
                ))
            else:
                p = ("$%.2f" % card['price']) if card['price'] else ''
                print("%s %s %s" % (
                    num.ljust(4),
                    p.ljust(5),
                    card['player_name']
                ))

        total_in_set = self.get_total_size_of_set(set)

        print("You %s %d cards out of %d in the set" % (
            "need" if type == 'want' else "have",
            len(cards), total_in_set
        ))
        remaining = total_in_set - len(cards)
        print("You %s %d cards (%.1f%%)" % (
             "have" if type == 'want' else "need",
            remaining, 100 * remaining / float(total_in_set)
        ))

        if with_price:
            self.comc_report(set, verbose=True)


    def show_intersections(self, set, card_numbers, with_price=False):
        total = len(card_numbers)
        needs = self.get_want_list(set, with_price)
        haves = self.get_have_list(set, with_price)

        have_count = 0
        need_count = 0
        total_have_price = 0
        haves_on_comc = 0
        total_need_price = 0
        needs_on_comc = 0

        counts = {'+ Need': 0, '- Have': 0, None: 0}
        total_price = {'+ Need': 0, '- Have': 0, None: 0}
        on_comc = {'+ Need': 0, '- Have': 0, None: 0}

        for card in card_numbers:
            c = str(card)

            if c in needs:
                tag = "+ Need"
                card = needs[c]
            elif c in haves:
                tag = "- Have"
                card = haves[c]
            else:
                print("Neither want nor need:", c)
                continue

            p = card['price']
            counts[tag] += 1

            if not p:
                on_comc[tag] += 1
            else:
                total_price[tag] += p

            print (tag, c.ljust(3),
                (("$%.2f" % p) if p else '').ljust(6),
                card['player_name']
            )

        print ("======")
        print("You need %d, and you have %d out of a total of %d cards." % (
            counts['+ Need'], counts["- Have"], total
        ))
        if with_price:
            haves_unlisted = counts['- Have'] - on_comc['- Have']
            needs_unlisted = counts["+ Need"] - on_comc['+ Need']
            avg = (total_price["- Have"] + total_price["+ Need"]) / (counts['- Have'] + counts['+ Need'])
            estimated_haves = total_price["- Have"] + (haves_unlisted) * avg
            estimated_needs = total_price["+ Need"] + (needs_unlisted) * avg
            print ("Value of haves: $%.2f (%d unlisted), Value of needs: $%.2f (%d unlisted)" % (
                estimated_haves, haves_unlisted,
                estimated_needs, needs_unlisted
            ))
            print("Total value of lot: $%.2f" % (estimated_needs + estimated_haves))
        print("Dupe rate: %.2f%%," % (100 * float(counts['- Have']) / total))
        print("Fill rate: %.2f%%" % (100 * float(counts['+ Need']) / total))

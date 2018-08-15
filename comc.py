from bs4 import BeautifulSoup
import requests

class Comc(object):

    def __init__(self):
        self.comc_cache = {}

    def fetch_set_data(self, sport, year, product, set):
        key = "{sport}/{year}/{product}_-_{set}".format(
            sport=sport,
            year=year,
            product=product,
            set=set
        )

        if key in self.comc_cache:
            return self.comc_cache[key]

        print "fetching from comc..."
        doc = requests.get("https://www.comc.com/Cards/%s,i100" % key)
        print "...done"
        parsed = BeautifulSoup(doc.content, "html.parser")

        wrappers = parsed.find_all(class_="cardInfoWrapper")

        datas = {}
        for card in wrappers:
            number = card.find(class_="description").text.strip().split("#")[-1]
            datas[number] = {
                'price': float(card.find(class_="listprice").find('a').text[1:]),
                'player_name': card.find(class_="title").text.strip(),
            }

        self.comc_cache[key] = datas
        return datas

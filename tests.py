from checklist_parser import Checklist

c = Checklist("/Users/chrispriest/BaseballCards/Panini Cooperstown/2012.txt")
#print c.show_have_list("Base_-_Crystal_Collection", False)

#c.show_intersections("Base_-_Crystal_Collection", [
#    4,7,9,11,17,22,31,34,42,43,46,50,51,52,57,61,65,70,71,76,77,80,87,90,94,97,100,
#    106, 109,118,119,120,122,123,125,127,135,137,145,150,159,166

#    4, 9, 11, 13, 14, 19, 20, 26, 28, 32, 33, 36, 41, 42, 47, 50, 54, 56, 58, 59,
#    60, 62, 65, 66, 67, 69, 70, 77, 80, 81, 82, 86, 88, 92, 98, 100, 102, 104,
#    106, 107, 113, 115, 117, 119, 121, 126, 127, 129, 130, 133, 136, 137, 138,
#    141, 142, 143, 144, 145, 148
#
#], with_price=True)

c.show_intersections("Bronze_History", [
    4,8,18,20,24,29,34,58,62,65,74,77,80,81,86,89,92,99
], with_price=True)

#c.show_want_list("Base_-_Green_Crystal_Shard", with_price=True)

#print c.percentage_missing("Base_-_Green_Crystal_Shard", verbose=True)
#print c.cost_to_buyout_comc("Base_-_Green_Crystal_Shard", verbose=True)
#print c.value_from_sellout("Base_-_Green_Crystal_Shard", verbose=True)
#print c.average_card_price("Base_-_Crystal_Collection")
#print c.get_comc_url("X")
#print c.get_comc_url("Y")

#print c.comc_report("Base_-_Green_Crystal_Shard")

#d = Checklist("/Users/chrispriest/BaseballCards/Stadium Club/2016.txt")
#d.show_want_list("Legends_Die-Cuts", with_price=True)

from recap.recap_page import RecapPage
#print("i'm in")
def fetch_one_line():
  url = "https://recaps.competitionsuite.com/7bd6b6ad-a3be-4b9f-8be6-de516f452b95.htm"
  print(url)
 # """
  recap = RecapPage(url)
  recap.fetch()
  header = recap.parse_header()

  print(header.division)
  print(header.captions)
  print(header.sub_captions)
  print(header.judges)
  print(header.table_headers)
  #"""
  #print("good by")
  return ("Hi Sam!")
#"""

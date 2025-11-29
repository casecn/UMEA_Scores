from recap.recap_page import RecapPage, TransformHeader

#print("i'm in")
def fetch_one_line():
  url = "https://recaps.competitionsuite.com/7bd6b6ad-a3be-4b9f-8be6-de516f452b95.htm"
  
  #print(url)
 # """
  recap = RecapPage(url)
  recap.fetch()
  header = recap.parse_header()

  transformer = TransformHeader()
  renamed_headers = transformer.apply(header)

  print("Division:", header.division)
  print("Captions: ", header.captions)
  print("Sub-Captions: ", header.sub_captions)
  print("Judges: ", header.judges)
  print("Raw headers:", header.table_headers)
  print("Renamed headers:", renamed_headers)
  #"""
  #print("good by")
  return ("Hi Sam!")
#"""

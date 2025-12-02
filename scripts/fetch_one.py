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
  renamed_header = transformer.update_header(header)
  header.renamed_headers = renamed_header

  #recap.parse_scores

  #parse data rows (scores)
  rows = recap.parse_scores(first_data_row=6)
  print(rows)
  #print("Division:", header.division)
  #print("Captions: ", header.captions)
  #print("Sub-Captions: ", header.sub_captions)
  #print("Judges: ", header.judges)
  print("Raw headers:", header.table_headers)

  print("Renamed Headers:", renamed_header)
  #"""
  #print("good by")
  return ("Hi Sam!")
#"""

from bs4 import BeautifulSoup
import requests
url = "https://recaps.competitionsuite.com/7bd6b6ad-a3be-4b9f-8be6-de516f452b95.htm"
division = ''
captions_list = []
sub_captions_list = []
judges_list = []
table_header_list = []

response = requests.get(url).text
soup = BeautifulSoup(response, 'html.parser')
#print(soup)
table_tag = soup.find_all('table')
#print(table_tag[1])
table_of_intrest = table_tag[1]
table_rows = table_of_intrest.find_all('tr')
#print(table_rows[3].text)
#pull info from table header.
division = table_rows[0].text
#captions_list= [header.get_text(strip=True) for header in table_rows[2]]
captions_list = [
  text
  for text in (caption.get_text(strip=True) for caption in table_rows[2])
    if text
]
sub_captions_list = [
    text
    for text in (sub_caption.get_text(strip=True) for sub_caption in table_rows[3])
      if text
]
judges_list = [
    text
    for text in (judge.get_text(strip=True) for judge in table_rows[4])
    if text
]

table_header_list = [
    text
    for text in (header.get_text(strip=True) for header in table_rows[5])
    if text
]

#print(f'# of Captions: {len(captions_list)}, # of Sub Captions: {len(sub_captions_list)}, #of Judges: {len(judges_list)}')
#print(table_header_list)

#**Update table_header_list with sub caption initials (e.g. Music Ensemble = ME => Music => ME_Music)
#***** Split the string by spaces, then take the first three characters of each word and join them into a prefix
prefix_list = []
for i in range(len(sub_captions_list)):
  text = sub_captions_list[i]

  first_chars = []
  for word in text.split():
    if word:  # Ensure the word is not empty (handles multiple spaces)
      #print(word)
      first_chars.append(word[0:3])
      prefix = ''.join(first_chars)

  prefix_list.append(prefix)
#print(prefix_list)
#print(f'Caption List: {captions_list}')
#print(f'Sub Caption List: {sub_captions_list}')
print(f'Table Headers: {table_header_list}')
#Music Caption
table_header_list[0] = f'{prefix_list[0]}_{table_header_list[0]}'
table_header_list[1] = f'{prefix_list[0]}_{table_header_list[1]}'
table_header_list[2] = f'{prefix_list[0]}_{table_header_list[2]}'

table_header_list.insert(3,f'{prefix_list[0]}_rank')

table_header_list[4] = f'{prefix_list[1]}_{table_header_list[4]}'
table_header_list[5] = f'{prefix_list[1]}_{table_header_list[5]}'
table_header_list[6] = f'{prefix_list[1]}_{table_header_list[6]}'

table_header_list.insert(7, f'{prefix_list[1]}_rank')

table_header_list[8] = f'{captions_list[0]}_{table_header_list[8]}al'
table_header_list.insert(9, f'{captions_list[0]}_rank')
# Music Effect Caption
table_header_list[10] = f'{prefix_list[2]}_{table_header_list[10]}'
table_header_list[11] = f'{prefix_list[2]}_{table_header_list[11]}'
table_header_list[12] = f'{prefix_list[2]}_{table_header_list[12]}'

table_header_list.insert(13, f'{prefix_list[2]}_rank')

table_header_list[14] = f'{prefix_list[3]}_{table_header_list[14]}'
table_header_list[15] = f'{prefix_list[3]}_{table_header_list[15]}'
table_header_list[16] = f'{prefix_list[3]}_{table_header_list[16]}'

table_header_list.insert(17, f'{prefix_list[3]}_rank')

table_header_list[18] = f'{captions_list[1]}_{table_header_list[18]}al'
table_header_list.insert(19, f'{captions_list[1]}_rank')

# Percussion Caption
table_header_list[20] = f'{prefix_list[4]}_{table_header_list[20]}'
table_header_list[21] = f'{prefix_list[4]}_{table_header_list[21]}'
table_header_list[22] = f'{prefix_list[4]}_{table_header_list[22]}'

table_header_list[23] = f'{captions_list[2]}_{table_header_list[23]}al'
table_header_list.insert(24, f'{captions_list[2]}_rank')

# Color Guard Caption
table_header_list[25] = f'{prefix_list[5]}_{table_header_list[25]}'
table_header_list[26] = f'{prefix_list[5]}_{table_header_list[26]}'
table_header_list[27] = f'{prefix_list[5]}_{table_header_list[27]}'

table_header_list[28] = f'{captions_list[3]}_{table_header_list[28]}al'
table_header_list.insert(29, f'{captions_list[3]}_rank')

# Sub Total
table_header_list.insert(30, captions_list[4])
table_header_list.insert(31, f'{captions_list[4]}_rank')

# Penalty
table_header_list[32] = f'{prefix_list[6]}_{table_header_list[32]}'
table_header_list[33] = f'{captions_list[5]}_{table_header_list[33]}al'

table_header_list.insert(len(table_header_list), 'Total')
table_header_list.insert(len(table_header_list), 'Rank')

#table_header_list[25] = f'{captions_list[5]}_{table_header_list[25]}al'
#print(f'Updated Table Header List: {table_header_list}')

#headers = [th.get_text(strip=True) for th in table_rows[3].find_all("td")]
#print(headers)
#score_table = table_rows[4].find_all('td')

#print(score_table[0].text) #School Name
#print(score_table[1].text) #School City
#print(score_table[78].text)  # School City
#print(len(score_table))


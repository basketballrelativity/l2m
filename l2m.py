from selenium import webdriver
import pandas as pd
import time

from py_ball import scoreboard

HEADERS = {'Connection': 'close',
           'Host': 'stats.nba.com',
           'Origin': 'http://stats.nba.com',
           'Upgrade-Insecure-Requests': '1',
           'Referer': 'stats.nba.com',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2)' + \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
                         'Chrome/66.0.3359.117 Safari/537.36'}

def get_game_ids(date):
	""" get_game_ids returns the NBA game IDs
	that take place on the provided date

	@param date (str): Date in MM/DD/YYYY format

	Returns:

		- game_id_list (list): List of game IDs
	"""

	scores = scoreboard.ScoreBoard(headers=HEADERS,
                               	   endpoint='scoreboardv2',
                                   league_id='00',
                               	   game_date=date,
                               	   day_offset='0')

	games = scores.data['GameHeader']
	game_id_list = [x['GAME_ID'] for x in games]

	return game_id_list


def get_l2m_reports(date):
	""" get_l2m_reports scrapes the NBA Last Two Minute
	reports on the given date for relevant data

	@param date (str): Date in MM/DD/YYYY format

	Returns:

		- l2m_date.csv file saved to the local working
			directory
	"""

	full_df = pd.DataFrame({})
	game_id_list = get_game_ids(date)
	for x in game_id_list:
		driver = webdriver.Chrome()

		url = 'https://official.nba.com/l2m/L2MReport.html?gameId=' + x
		driver.get(url)
		html = driver.page_source

		video_ind = html.find('class="videoHead">Video')
		html = html[video_ind:]
		start_lab = '"tablesaw-cell-content">'
		end_lab = '</span></td>'
		table = []
		loop = True
		time.sleep(3)
		if html.find(start_lab)!=-1:
			while loop:
				if html.find(start_lab) > html.find('</table>') or html.find(start_lab)==-1:
					loop = False
					break
				row = []
				for count in range(7):
					start_ind = html.find(start_lab)
					end_ind = html.find(end_lab)
					if count == 6:
						alt_start = '<a target="_blank" href="'
						alt_end = '">Video</a>'
						alt_start_ind = html.find(alt_start)
						alt_end_ind = html.find(alt_end)
						row.append(html[alt_start_ind + len(alt_start):alt_end_ind].replace('amp;', ''))
					else:	
						row.append(html[start_ind + len(start_lab):end_ind])
					html = html[end_ind + len(end_lab):]

				if html.find('Comment:') < html.find(start_lab) or (html.find('Comment:')!=-1 and html.find(start_lab)==-1):
					com_start = 'Comment:</td><td colspan="6">'
					com_end = '</td></tr>'
					comment_start = html.find(com_start)
					comment_end = html.find(com_end)
					html = html[comment_end + len(com_end):]
					comment_start = html.find(com_start)
					comment_end = html.find(com_end)

					row.append(html[comment_start + len(com_start):comment_end])
					html = html[comment_end + len(com_end):]
				else:
					print('!!')
					print(html.find('Comment:'))

				table.append(row)
				if html.find(start_lab) > html.find('</table>') or html.find(start_lab)==-1:
					loop = False

			test_df = pd.DataFrame(table, columns=['Period',
											      'Time',
				 							      'Call Type',
				 							      'Committing Player',
				 							      'Disadvantaged Player',
				 							      'Review Decision',
				 							      'Video',
				 							      'Comment'])
			test_df['game_id'] = [x] * len(test_df)

			full_df = pd.concat([full_df, test_df], axis=0)
		else:
			print(x)

		driver.close()

	full_df.to_csv('l2m_date.csv', index=False)


if __name__ == '__main__':
	date = '11/15/2019'
	get_l2m_reports(date)

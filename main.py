from bs4 import BeautifulSoup
import chess
import json
import multiprocessing
import os
from re import sub
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def uci2coord(uci_str: str):
	return [ord(uci_str[0]) - ord('a'), int(uci_str[1]) - 1, ord(uci_str[2]) - ord('a'), int(uci_str[3]) - 1]

def sans2coords(last_move: str, next_moves: list):
	board = chess.Board()
	last_coord = []
	for m in last_move.split('+'):
		if m:
			uci_str = board.push_san(m).uci()
			last_coord.append(uci2coord(uci_str))

	next_coords = []
	for next_move in next_moves:
		uci_str = board.parse_san(next_move).uci()
		next_coords.append(uci2coord(uci_str))

	return last_coord, next_coords


def obtain_moves(last_move: str, nb_ply: int):

	# Set up Chrome options and initialize the web driver
	chrome_options = Options()
	chrome_options.add_argument("--headless")  # Run Chrome in headless mode (no GUI)
	driver = webdriver.Chrome(options=chrome_options)

	# Define the URL to scrape
	url = f"https://www.chess.com/explorer?moveList={last_move}&ply={nb_ply}"

	# Set the PHPSESSID cookie with sys.argv
	if len(sys.argv) > 1:
		cookie = {
			'domain': '.chess.com',
			'httpOnly': True,
			'name': 'PHPSESSID',
			'path': '/',
			'sameSite': 'Lax',
			'secure': True,
			'value': sys.argv[1]}

		# Enables network tracking so we may use Network.setCookie method
		driver.execute_cdp_cmd('Network.enable', {})
		# Set the actual cookie
		driver.execute_cdp_cmd('Network.setCookie', cookie)
		# Disable network tracking
		driver.execute_cdp_cmd('Network.disable', {})

	# Open the URL in the web driver
	driver.get(url)

	# Wait for the elements to load using WebDriverWait
	wait = WebDriverWait(driver, 10)  # Adjust the timeout as needed
	suggested_moves_items = wait.until(
		EC.presence_of_all_elements_located((By.CLASS_NAME, 'suggested-moves-suggested-moves-items'))
	)

	# Create a list to store the extracted data
	next_moves = {'last coord':[], 'sans': [], 'coords': [], 'probas': []}
	total_played = 0;
	total_coef = 0;

	# Iterate through each <li> element
	for item in suggested_moves_items:
		# Parse the HTML content of the <li> element using BeautifulSoup
		soup = BeautifulSoup(item.get_attribute('outerHTML'), 'html.parser')

		# Find the specific elements within the <li> element
		san_move = soup.find('span', class_='move-san-san').get_text()

		if not san_move:
			fig_elem = soup.find('span', class_='move-san-figurine').get('class')[-1]

			if fig_elem.startswith("knight"):
				san_move = 'N'
			elif fig_elem.startswith("bishop"):
				san_move = 'B'
			elif fig_elem.startswith("rook"):
				san_move = 'R'
			elif fig_elem.startswith("queen"):
				san_move = 'Q'
			elif fig_elem.startswith("king"):
				san_move = 'K'

			san_move += soup.find('span', class_='move-san-afterfigurine').get_text()

		nb_played = sub(r"\D", "", soup.find('p', class_='suggested-moves-total-games').get_text())
		if not nb_played:
			break # Case where only played once (not interesting)
		nb_played = int(nb_played)

		percent = [int(sub(r"\D", "", span.get_text())) for span in soup.find_all('span', class_='suggested-moves-percent-label')]

		total_played += nb_played

		if (nb_played >= 0.01 * total_played): # Keep 99% of the best moves
			# Store the extracted data in a dictionary
			coef = nb_played * percent[-1 if nb_ply % 2 else 0]
			total_coef += coef
			next_moves['sans'].append(san_move)
			next_moves['probas'].append(coef)

		else:
			break

	# Close the web driver
	driver.quit()

	# print(last_move)
	# print(next_moves)

	if not next_moves['sans']:
		exit()

	next_moves['last coord'], next_moves['coords'] = sans2coords(last_move, next_moves['sans'])
	for i in range(len(next_moves['probas'])):
		next_moves['probas'][i] /= total_coef

	return last_move, next_moves


def multithread_scrapping(max_ply: int = 6):

	shared_moves = [None] * (max_ply + 1)
	max_nb_threads = multiprocessing.cpu_count()

	for ply in range(0, max_ply+1):
		print(f"Going over ply: {ply}")
		shared_moves[ply] = {}

		if os.path.isfile(f"ply{ply}.json") and os.access(f"ply{ply}.json", os.R_OK):
			with open(f"ply{ply}.json", "r") as infile:
				shared_moves[ply] = json.load(infile)

		else:
			# start n worker processes
			with multiprocessing.Pool(processes=max_nb_threads) as pool:
				# Create multiple processes to add values to the shared list

				processes = []
				if ply >= 2:
					for previous_move, previous in shared_moves[ply - 1].items():
						for move in previous["sans"]:
							process = pool.apply_async(obtain_moves, (f"{previous_move}+{move}", ply))
							processes.append(process)

				elif ply == 1:
					for previous in shared_moves[0].values():
						for move in previous["sans"]:
							process = pool.apply_async(obtain_moves, (move, 1))
							processes.append(process)

				else:
					process = pool.apply_async(obtain_moves, ("", 0))
					processes.append(process)

				# Wait for all processes to finish
				for process in processes:
					last_move, next_moves = process.get(timeout=100)
					shared_moves[ply][last_move] = next_moves

			with open(f"ply{ply}.json", "w") as outfile: 
				json.dump(shared_moves[ply], outfile)

	return shared_moves


if __name__ == '__main__':

	max_ply = 15

	if len(sys.argv) <= 1:
		max_ply = 6

	openings = multithread_scrapping(max_ply=max_ply)

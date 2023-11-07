# Chess Opening Explorer Scraper
## Overview
This Python script is designed to scrape data from chess.com's Opening Explorer and create weighted lists of potential moves for various ply levels in chess openings. The resulting data is stored in JSON files for easy access and analysis.

## Prerequisites
- Python 3.x
- Internet connection
- pip3

## Usage
#### Clone or download this repository to your local machine.

#### Install the requiered library using pip:
```{bash}
python3 -m pip install -r requirements.txt
```

#### Run the main.py script using your Python interpreter:
```{bash}
python3 main.py
```
The script will scrape data from chess.com's Opening Explorer, process the information, and generate JSON files for each ply level.

The JSON files will be named ply0.json, ply1.json, and so on, corresponding to the ply level.

## Contributing
Contributions are welcome. If you have ideas for improvements or find issues, please feel free to open an issue or submit a pull request.

## License
This project is licensed under the GNU License. See the LICENSE file for details.

## Disclaimer
This project is intended for educational and analytical purposes. Please respect chess.com's terms of service and usage policies when using this scraper.

Happy chess analysis!

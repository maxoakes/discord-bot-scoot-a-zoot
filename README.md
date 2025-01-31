# Discord Bots

## DJ-Scoot-A-Zoot / ScootNet
A Discord bot that has many modes: 
* Tools like weather, dictionary and color lookups
* Media player that plays from a preset list of media
* Quote tracking
* Custom-built RSS feed

All settings are stored in json files or a MySQL database (other than the quoting functionality, which requires a database).

## Installation and Usage

### Required dependencies:
Also see `--upgrade py-cord[voice] py-cord[speed]`

### Usage

Full usage is

```py main.py [list of character codes] [prefix command character] [true= mysql|false=json]```

Mode codes:
* `t` = tools
* `r` = RSS feeds
* `m` = media player
* `q` = quotes (requires database)

My personal start command: `py main.py trmq ! true`

## Maintenance
RSS Feeds, Radio Stations cannot be created via commands and must be created by admin by editing json files or inserting database rows. For the database, stored procedures are available for adding and editing rows:
* `insert_or_update_radio_station`
* `insert_or_update_rss_feed`

For json files, `settings/*.json.example` files are provided that show how the objects are structured

## Docker
If using Docker and MySQL database on host or elsewhere, the container must see the local network
```
sudo docker run -i -d --network host -p 8080:80 scootnet
```
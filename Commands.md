# Commands

Below are all implemented and available commands for DJ Scoot-A-Zoot.

# `quote`
1. Add a quote to the database in the same format that you would write in formal text.

`>>quote direct "<quote text>" -<author name>(, <datetime in any format>(, <location or platform> ))`

2. Add a quote to the database in a verbose, specific format.

`>>quote add --quote=<quote text without quotation> --author=<author name> --location=<location or platform> --time=<datetime in any format>`

## Examples:

`>>quote direct "This is a direct quote to add." -Scouter, 2023`

`>>quote direct "This is a different quote." -Scouter`

`>>quote add --quote=This is a verbose quote. --author=Scouter --location=Discord--time=2023`

`>>quote add --quote=This is a less detailed quote. --author=Scouter --time=2023`


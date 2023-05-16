Command: `quote`

Creates or retrieves quotes. Available with the following sub-commands in the formats:

1. `direct`: Add a quote to the database in the same style as in text

Usage:
```>>quote direct "<quote text>" -<author name>(, <datetime in any format>(, <location or platform> ))```

Example:
`>>quote direct "This is a direct quote to add." -Scouter, 2023`

2. `add`: Add a quote to the database in a verbose, specific format.

Usage:
```>>quote add --quote=<quote text without quotation> --author=<author name> --location=<location or platform> --time=<datetime in any format>```

Example: 
`>>quote add --quote=This is a verbose quote. --author=Scouter --location=Discord--time=2023`
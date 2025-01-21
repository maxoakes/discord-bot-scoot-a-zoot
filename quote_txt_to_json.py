
import json
from classes.quote import Quote
from state import Utility


def main():
    quote_sets: list[list[dict]] = []
    with open("quotes.txt", "r", encoding='utf-8') as read_file:
        this_set: list[dict] = [] 
        for line in read_file:
            if Utility.is_null_or_whitespace(line):
                quote_sets.append(this_set.copy())
                this_set.clear()
            else:
                quote = Quote.parse_from_raw(line.encode("utf-16").decode("utf-16"))
                if quote != None:
                    this_set.append(quote.as_dict())

    with open("quotes.json", "w+") as write_file:
        json.dump(quote_sets, write_file, indent=4)

if __name__ == "__main__":
    main()

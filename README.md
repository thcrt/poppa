# POPPA

> [!CAUTION]
> This tool is entirely for my own use. It parses a completely unstandardised spreadsheet layout
> that my grandad uses to record his genealogical research, so unless he's your grandad too, this
> isn't going to do much for you. I've made it open-source largely in order to back up my work, and
> maybe on the off-chance that someone finds the code helpful as an example of the general task it
> performs.

POPPA is a parser that reads an ODS (LibreOffice spreadsheet) file in a _very particular format_ and
uses it to generate a CSV of genealogical data that can be imported into 
[Gramps](https://gramps-project.org/).

### Usage 

```
poppa [OPTIONS] FILE OUT
```

#### Arguments

- `FILE` The spreadsheet to be parsed.
- `OUT` Where to output the generated CSV.

#### Options

- `places-file PATH` A TOML file detailing valid place names. An example is given at
  [`src/poppa/places.toml`](/src/poppa/places.toml).

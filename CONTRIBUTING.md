# Contributing
The actual definitions for the XML data is inside [data/](data/), not inside the [schemas/](schemas/) folder. The dataset is passed through [a script](chores/format_schemas.py) to generate the [schemas/](schemas/) files. Another [script](chores/generate_output.py) is used to generate the content of the [out/](out/) folder. The [settings.json](out/settings.json) file can be used by users to automatically load the proper schema validations based on patterns marked inside the dataset files.

A schema for the dataset files validation is provided inside [.schemas/](.schemas/data_schema.json) to indicate whenever you did a mistake in your syntax of the dataset. Use it to reduce the risks of doing back and forths in pull requests.

## Structure
The dataset is structured the following way:
```bash
.github/                      # GitHub related files
└── workflows/
    └── format-output.yml       # GitHub action to format the out files
.schemas/
└── data_schema.json            # validation schema of files in data/
chores/                       # chores to run when updating the dataset
├── format_schemas.py           # generates the XSD files from data/
├── generate_output.py          # generates the out/data.json file
├── make_settings.py            # generates the out/settings.json file
└── requirements.txt            # Python dependencies for the chores
data/                         # the dataset in yaml format
└── *.yaml
out/                          # output files generated from the dataset
├── schemas/                    # holds XSD files for XML validation
│   └── *.xsd
├── data.json                   # holds every data/*.yaml file in a single JSON file, some information are formatted first (e.g. references to other descriptions)
└── settings.json               # VSCode settings file
schemas/                      # deprecated folder, kept for backward compatibility
└── *.xsd
scripts/                      # dev scripts
└── ...
Makefile                      # helper to run some of the chores locally
```

## Contact
You can find the creator of this dataset (SimKDT) in the [PZ Modding Community](https://pzwiki.net/wiki/PZ_Modding_Community).
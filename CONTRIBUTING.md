# Contributing
The actual definitions for the XML data is inside [data/](data/), not inside the [schemas/](schemas/) folder. The dataset is passed through [a script](chores/format_schemas.py) to generate the [schemas/](schemas/) files. Another [script](chores/generate_output.py) is used to generate the content of the [out/](out/) folder. The [settings.json](out/settings.json) file can be used by users to automatically load the proper schema validations based on patterns marked inside the dataset files.

A schema for the dataset files validation is provided inside [.schemas/](.schemas/data_schema.json) to indicate whenever you did a mistake in your syntax of the dataset. Use it to reduce the risks of doing back and forths in pull requests.

# License
For the license, see [LICENSE](LICENSE).
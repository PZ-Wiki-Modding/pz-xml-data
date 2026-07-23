# PZ XML Data
Provides a dataset of documentation for the XML files used in Project Zomboid. The data stored inside yaml files are used to generate the following:
- a JSON file [data.json](out/data.json) that contains the entire dataset.
- XSD schema files inside the [schemas](schemas) folder to easily link to.
- an example VSCode setting file [settings.json](out/settings.json) that already has all the necessary setup to the online accessible schema files.

## Schemas
This data is used to provide validation schemas for the XML files which can be found in [out/schemas](out/schemas) and require the [XML extension by RedHat](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-xml). You can use the [settings.json](out/settings.json) to easily load the schemas into your VSCode workspace.

## Contributing
This dataset is aimed to accept any contributions. See [CONTRIBUTING](CONTRIBUTING.md) for more information on how to contribute to this dataset.

## License
See [LICENSE](LICENSE) for more information.
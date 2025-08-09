# DiffSync CLI

DiffSync CLI is a powerful command-line tool designed for diffing and synchronizing data between various sources, with a primary focus on product and catalog data. It provides robust integrations for platforms like CCVShop and Perfion, and supports mock data sources for testing and development workflows. The CLI leverages the `rich` library for visually appealing output and is built to be easily extensible for new data sources.

---

## Features

- **Diff and Sync**: Compare and synchronize data between sources (Perfion, CCVShop, mock files).
- **Rich CLI Output**: Uses the `rich` library for colored, formatted, and readable terminal output.
- **Extensible Integrations**: Modular adapters for adding new data sources or targets.
- **Perfion Utilities**: Query Perfion for product attributes, categories, and attribute values.
- **Configurable**: Supports environment variables and `.env` files for flexible configuration.
- **Robust Logging**: Pretty logging output with configurable verbosity.

# Data analysis toolkit

This is the toolkit you can use to analyze logs from PathFAInder application.

## Development setup

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
1. Clone this repository
1. Run `uv sync` to install the dependencies
1. Run `uv run streamlit run src/app.py` to start the development server

## Files and functions

- [app.py](src/app.py): The main Streamlit application file. It constructs the user interface and handles user interactions.
- [components](src/components): Contains reusable components for the application.
- [sections](src/sections): Contains the different sections of the application, each responsible for a specific part of the analysis.
- [utils](src/utils): Contains utility functions and classes used throughout the application.

## Streamlit deployment

[Documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)

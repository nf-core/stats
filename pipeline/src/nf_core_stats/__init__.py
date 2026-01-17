from importlib.metadata import version

from cyclopts import App
from dotenv import load_dotenv

from . import citations_pipeline, github_pipeline, slack_pipeline, strict_syntax_pipeline

__version__ = version("nf_core_stats")

load_dotenv()


app = App()
app.command(github_pipeline.main, "github")
app.command(slack_pipeline.main, "slack")
app.command(citations_pipeline.main, "citations")
app.command(strict_syntax_pipeline.main, "strict-syntax")


if __name__ == "__main__":
    app()

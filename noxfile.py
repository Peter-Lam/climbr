import tempfile
from pathlib import Path

import nox

# package = None
nox.options.sessions = (
    "lint",
    "safety",
)
locations = "web_scraper", "noxfile.py", "climbr.py", "config.py", "common"


def install_with_constraints(session, *args, **kwargs):
    requirements = tempfile.NamedTemporaryFile(delete=False)
    try:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)
    finally:
        requirements.close()
        Path(requirements.name).unlink()


@nox.session
def black(session):
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session
def lint(session):
    args = session.posargs or locations

    install_with_constraints(
        session,
        "isort",
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-docstrings",
    )
    session.run("isort", "--profile", "black", *args)
    session.run("flake8", "--max-line-length", "88", "climbr.py")


@nox.session
def safety(session):
    with tempfile.NamedTemporaryFile(delete=False) as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        install_with_constraints(session, "safety")
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")
    Path(requirements.name).unlink()

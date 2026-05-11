[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Multi-process automation built on noxus-lab and the Noxus AI platform."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
classifiers = [
  "Development Status :: 3 - Alpha",
  "Private :: Do Not Upload",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
]
dependencies = [
  "noxus-sdk>=0.5.0",
  "openai>=1.40.0",
  "python-dotenv>=1.0.0",
  "pydantic>=2.7",
]

[project.optional-dependencies]
dev = [
  "ruff>=0.6.0",
  "pre-commit>=3.7.0",
  "pyright>=1.1.380",
  "pytest>=8.0",
  "pytest-cov>=5.0",
  "pytest-mock>=3.12",
]

[tool.hatch.build.targets.wheel]
packages = ["shared", "processes"]

[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
  "-q",
  "--strict-markers",
  "--strict-config",
  "--cov=shared",
  "--cov=processes",
  "--cov-report=term-missing",
  "--cov-fail-under=70",
]
testpaths = ["tests", "processes"]
markers = [
  "live: hits the live Azure OpenAI / Noxus backend (requires keys)",
]

[tool.coverage.run]
branch = true
source = ["shared", "processes"]

[tool.coverage.report]
exclude_lines = [
  "pragma: no cover",
  "raise NotImplementedError",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
]

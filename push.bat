@echo off
set GITHUB_TOKEN=
"C:\Program Files\GitHub CLI\gh.exe" repo create indian-guy-project --public --source=. --remote=origin --push

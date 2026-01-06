import os

ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
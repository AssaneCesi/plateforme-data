"""Journalisation homogène pour toutes les étapes du pipeline."""
import logging
import sys

_CONFIGURE = False


def journal(nom):
    global _CONFIGURE
    if not _CONFIGURE:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-7s %(name)s : %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stdout,
        )
        _CONFIGURE = True
    return logging.getLogger(nom)

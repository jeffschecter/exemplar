import logging

import chargen

from flask import Flask
from flask import request
from flask import Response


app = Flask(__name__)


EXPLANATORY = "\n\n" + """
==============================================================================

SPENDING BONUSES:
Every character starts with one bonus; overlapping abilities may grant you a
few extra bonuses. Each bonus may be used for one of the following. Note that
some options cost an extra raise.

    - Add a specialty to an ability rated at 3d or higher, which currently
      lacks a specialty.
    - Add a new resource, as approved by the Reeree.
    - Add a new trait without special rules, as approved by the Referee.
    - Add a new training.
    - Increase an ability from 2d to 3d, or from 3d to 4d, at the cost of
      one raise.

CALCULATING VITALITY:
Vitality is equal to your dice in Steel, plus your dice in the best of
Prowess, Speed, Stealth, and Survival. Add in any bonuses from traits.

CALCULATING GUARD VALUE:
Guard value is 1 if Prowess is 2d, or 2 if Prowess is 3d or higher. If you
have training with shields or parrying blades, you may add +1 to guard value
when properly equipped.

NOTE ON OVERLAPPING ATTRIBUTES:
Overlapping grants of character attributes are handled as follows:

    - Specialties: You may only have one specialty in each ability. If granted
      multiple specialties in an ability, choose one to keep, and lose the
      rest.
    - Training: If granted the same training multiple times, you only get it
      once. (Extra versions of the same training wouldn't help you, anyay.)
    - Traits: If granted the same trait multiple times, you only get it once.
    - Resources: You may only take the weapons and armor from one of your
      archetypes. You may only have one line of credit, one stipend or source
      of income, one reserve of wealth, and one lodging or source of room and
      board; for each of these categories, if you have multiple resources,
      choose one to keep and drop the rest.
"""


@app.route('/')
def random_character():
  text = str(chargen.Character()) + EXPLANATORY
  return Response(text, mimetype="text/plain")


@app.route('/list')
def list_archetypes():
  text = "\n".join([
    "Power Level {}".format(a.power_level).ljust(20) + a.name
    for a in chargen.Character.ARCHETYPES])
  return Response(text, mimetype="text/plain")


@app.route('/<path:archnames>')
def character(archnames):
  text = str(chargen.Character(*archnames.split(",")))  + EXPLANATORY
  return Response(text, mimetype="text/plain")


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

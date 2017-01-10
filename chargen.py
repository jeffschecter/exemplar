# -*- coding: utf-8 -*-

import random
import re
import sys


# --------------------------------------------------------------------------- #
# Utilities.                                                                  #
# --------------------------------------------------------------------------- #

def read_archetypes():
  with open("archetypes.txt", "r") as f:
    arch_txt = f.read()
  return [Archetype(s) for s in arch_txt.split("\n\n")]


def similarity(s1, s2):
  return float(len(s1 & s2)) / ((len(s1) ** 0.5) * (len(s2) ** 0.5))


def best_guess(query, opts):
  query = query.lower()
  if query in opts:
    return query
  else:
    qlet = set(query)
    scored = [(similarity(set(opt), qlet), opt) for opt in opts]
    return max(scored)[1]


def format_item(it):
  words = it.replace("\n", " ::BREAK:: ").split()
  s = "    "
  line_len = 4
  extra_indent = False
  for word in words:
    l = len(word) + 1
    if word == "::BREAK::":
      line_len = 8
      extra_indent = True
      s += "\n        "
    elif line_len + l > 80:
      line_len = 8 + (4 * extra_indent)
      s += "\n        " + ("    " * extra_indent) + word + " "
    else:
      line_len += l
      s += word + " "
  return s.rstrip()


def format_list(l):
  return "\n".join([format_item(it) for it in l])


# --------------------------------------------------------------------------- #
# Main classes.                                                               #
# --------------------------------------------------------------------------- #

class Archetype(object):
    
  def __init__(self, s):
    self.name = None
    self.is_order = False
    self.requirements = None
    self.power_level = None
    self.abilities = {}
    self.specialty = None
    self.training = []
    self.traits = []
    self.resources = []
    self.techniques = []
    self.bond = None
    
    self._current_field = "Name"
    self._in_choice = False
    self._choice_lines = []
    self._unparsed_lines = []
    self._choice_end_callback = lambda _: None
    self._parse_from_string(s)
  
  def _parse_from_string(self, s):
    lines = s.split("\n")
    while lines:
      self._parse_line(lines[0].strip())
      lines = lines[1:]
  
  def _maybe_handle_choice(self, line, maybe_new_callback):
    # Return True if the line was totally handled and
    # nothing more needs to be done.
    choice_re = re.compile(r"^(And )?[cC]hoose.*\.")
    if choice_re.match(line):
      self._choice_end_callback("\n".join(self._choice_lines))
      self._choice_lines = [line]
      self._choice_end_callback = maybe_new_callback
      self._in_choice = True
      return True
    elif not self._in_choice:
      return False
    elif self._in_choice and line:
      self._choice_lines.append(line.strip("."))
      return True

  def _assigner(self, field_name):
    def assigner(line):
      if line:
        setattr(self, field_name, line)
    return assigner
  
  def _appender(self, field_name):
    def appender(line):
      if line:
          setattr(self, field_name, getattr(self, field_name, []) + [line])
    return appender
  
  def _append_entry_or_list(self, field_name, s):
    if not s:
      return
    if not s.endswith("."):
      split_re = re.compile(r"[,;] ")
      setattr(
          self, field_name,
          getattr(self, field_name, []) + split_re.split(s))
    elif s.endswith("."):
      setattr(
          self, field_name,
          getattr(self, field_name, []) + [s.strip(".")])
      
  def _parse_line(self, line):
    field_indicators = set([
        "Abilities", "Specialty", "Training", "Traits",
        "Resources", "Techniques", "Bond Relationship"])
    for fi in field_indicators:
      if line.startswith(fi) or line.startswith(fi + " "):
        self._choice_end_callback("\n".join(self._choice_lines))
        self._current_field = fi
        self._choice_lines = []
        self._coice_end_callback = lambda x: None
        self._in_choice = False
        line = line.partition(fi + " ")[2]
    
    if self._current_field == "Name":
      self.name = line
      self._current_field = "Power Level"

    elif self._current_field == "Power Level":
      parts = line.split(" • ")
      for part in parts:
        if part == "exemplar order":
          self.is_order = True
        elif part.startswith("requires "):
          self.requirements = set([
              arch.rpartition("or ")[2].strip()
              for arch in part.partition("requires ")[2].split(", ")])
        elif part.startswith("power level"):
          self.power_level = int(part.rpartition(" ")[2])
    
    elif self._current_field == "Abilities":
      entries = line.split(", ")
      for entry in entries:
        possibly = entry.startswith("possibly")
        ability, _, raw_dice = entry.rpartition("possibly ")[2].partition(" ")
        self.abilities[ability] = ("possibly " * possibly) + raw_dice
    
    elif self._current_field == "Specialty":
      if not self._maybe_handle_choice(line, self._assigner("specialty")):
        self.specialty = line

    elif self._current_field == "Training":
      if not self._maybe_handle_choice(line, self._appender("training")):
        self._append_entry_or_list("training", line)

    elif self._current_field == "Traits":
      if not self._maybe_handle_choice(line, self._appender("traits")):
        self._append_entry_or_list("traits", line)

    elif self._current_field == "Resources":
      if line:
        self.resources.append(line)

    elif self._current_field == "Techniques":
      if not self._maybe_handle_choice(line, self._appender("techniques")):
        self._append_entry_or_list("techniques", line)

    elif self._current_field == "Bond Relationship":
      if not self._maybe_handle_choice(line, self._assigner("bond")):
        self.bond = line
      self._choice_end_callback("\n".join(self._choice_lines))

    else:
      self._unparsed_lines.append(line)


class Character(object):
    
  ARCHETYPES = read_archetypes()
  
  def __init__(self, *arch_names):
    self._determine_archetypes(arch_names)
    self._calculate_abilities()
    self.specialties = self._flatten("specialty")
    self.training = self._flatten("training")
    self.traits = self._flatten("traits")
    self.resources = self._flatten("resources")
    self.techniques = self._flatten("techniques")
    self.bonds = self._flatten("bond")
    self.power_level = sum([a.power_level for a in self.archetypes])
  
  def __str__(self):
    return "\n".join([
        "ARCHETYPES: " + ", ".join([a.name for a in self.archetypes]),
        "POWER LEVEL: {} plus raises".format(self.power_level),
        "\nABILITIES:\n    " + "\n    ".join([
            "{ab}: {rat}".format(ab=ab, rat=rat)
            for ab, rat in sorted(self.abilities.items())]),
        "\nSPECIALTIES: (max of one per Ability)\n" + format_list(
            self.specialties),
        "\nTRAINING:\n" + format_list(self.training),
        "\nTRAITS:\n" + format_list(self.traits),
        "\nRESOURCES:\n" + format_list(self.resources),
        "\nTECHNIQUES:\n" + format_list(self.techniques),
        "\nBOND RELATIONSHIPS:\n" + format_list(self.bonds)])
  
  def _determine_archetypes(self, arch_names,):
    if arch_names:
      archs_by_name = dict((a.name.lower(), a) for a in self.ARCHETYPES)
      candidate_names = archs_by_name.keys()
      normalized_names = set(
          [best_guess(name, candidate_names) for name in arch_names])
      self.archetypes = [archs_by_name[name] for name in normalized_names]
    else:
      n_arch = random.randint(2, 4)
      random.shuffle(self.ARCHETYPES)
      self.archetypes = self.ARCHETYPES[:n_arch]
  
  def _flatten(self, field):
    final = []
    for l, a in [(getattr(a, field), a) for a in self.archetypes]:
      if l is None:
        continue
      elif isinstance(l, basestring):
        final.append("({a}) {it}".format(a=a.name, it=l))
      else:
        final += ["({a}) {it}".format(a=a.name, it=it) for it in l]
    return sorted(final)

  def _calculate_abilities(self):
    ab_list = [
        "Influence", "Logistics", "Medicine", "Perception", "Prowess",
        "Speed", "Stealth", "Steel", "Survival", "Technology", "Vehicles"]
    ranks = {"possibly 3d": 0, "3d": 1, "3d or 4d": 2, "4d": 3}
    translate = {
        (): "2d",
        ("possibly 3d",): "2d, or 3d and +1 raise",
        ("3d",): "3d",
        ("3d or 4d",): "3d, or 4d and +1 raise",
        ("4d",): "4d",
        ("3d", "3d"): "3d and +1 bonus, or 4d",
        ("3d or 4d", "3d"): "3d and +1 bonus, or 4d",
        ("3d or 4d", "3d or 4d"): "3d and +1 bonus, or 4d",
        ("4d", "3d"): "4d and +1 bonus",
        ("4d", "3d or 4d"): "4d and +1 bonus",
        ("4d", "4d"): "4d and +1 bonus"}
    self.abilities = {}
    for ab in ab_list:
      grants = [
          a.abilities.get(ab)
          for a in self.archetypes
          if ab in a.abilities]
      ranked = sorted([(ranks[g], g) for g in grants])[::-1]
      top_two = tuple([r[1] for r in ranked][:2])
      if len(top_two) == 2 and top_two[1] == "possibly 3d":
        top_two = top_two[:1]
      self.abilities[ab] = translate[top_two]


# --------------------------------------------------------------------------- #
# Driver.                                                                     #
# --------------------------------------------------------------------------- #

def main(argv):
  print Character(*argv)


if __name__ == "__main__":
  main(sys.argv[1:])

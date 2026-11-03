"""Validate the raw data/ and meta/ YAML files against meta/schema.yaml.

The schema maps each file to a record. A record maps field names to specs;
a field name ending in "!" is required, and any field the record does not
name is an error. A spec is either a string or a dict:

  str, text, name, int, bool, url, date, dates, years, term, apa, any
  key:<pool>          a key of a pool (authors, venues, courses,
                      institutions, papers, positions, coursework_groups)
  enum:a,b,c          one of the listed words
  list:<spec>         a list whose items match <spec>
  record:<name>       a record defined under `records:`
  <spec>|<spec>       either form
  {map: <spec>, keys: <spec>}   a mapping with free keys
  {one_of: [<spec>, ...]}       either form
  {<field>: <spec>, ...}        an inline record

`name` is plain text (no markdown link), `text` may carry markdown.
"""
import re
import sys

import yaml

PATTERNS = {
    "date": r"^\d{4}(-\d{2}(-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?)?)?$",
    "dates": r"^\d{4}-\d{2}(-\d{2})?/(\d{4}-\d{2}(-\d{2})?|\.\.)$",
    "years": r"^\d{4}/\d{4}$",
    "term": r"^\d{4}-(spring|summer|fall)$",
    "url": r"^(https?://\S+|mailto:\S+|[A-Za-z0-9_][A-Za-z0-9_./%-]*)$",
}


class Invalid(Exception):
    pass


def _pools(data):
    def keys(file, top):
        return set(((data.get(file) or {}).get(top) or {}))
    positions = set()
    for sec in ("education", "experience", "research", "teaching"):
        positions |= {e.get("id") for e in (data.get(sec) or {}).get(sec) or []}
    return {
        "authors": keys("authors", "authors"),
        "venues": keys("venues", "venues"),
        "courses": keys("courses", "courses"),
        "institutions": keys("institutions", "institutions"),
        "papers": {p.get("id") for p in (data.get("publications") or {}).get("papers") or []},
        "positions": positions,
        "coursework_groups": set(((data.get("bio") or {}).get("coursework_groups") or {})),
    }


class Validator:
    def __init__(self, schema, pools):
        self.records = schema.get("records") or {}
        self.pools = pools

    def check(self, spec, value, where):
        if isinstance(spec, dict):
            if set(spec) == {"one_of"}:
                errors = []
                for alt in spec["one_of"]:
                    try:
                        return self.check(alt, value, where)
                    except Invalid as e:
                        errors.append(str(e))
                raise Invalid(errors[-1])
            if set(spec) == {"list"}:
                return self._list(spec["list"], value, where)
            if "map" in spec:
                if not isinstance(value, dict):
                    raise Invalid(f"{where}: expected a mapping")
                for k, v in value.items():
                    if "keys" in spec:
                        self.check(spec["keys"], k, f"{where}: key {k!r}")
                    self.check(spec["map"], v, f"{where}.{k}")
                return
            return self.record(spec, value, where)
        spec = str(spec)
        if spec.startswith("list:"):
            return self._list(spec[5:], value, where)
        alts = spec.split("|")
        errors = []
        for alt in alts:
            try:
                return self.base(alt, value, where)
            except Invalid as e:
                errors.append(str(e))
        raise Invalid(errors[0] if len(errors) == 1 else f"{where}: {value!r} matches none of {spec}")

    def _list(self, spec, value, where):
        if not isinstance(value, list):
            raise Invalid(f"{where}: expected a list")
        for i, v in enumerate(value):
            label = (v.get("id") or v.get("name")) if isinstance(v, dict) else None
            self.check(spec, v, f"{where}[{label or i}]")

    def base(self, spec, value, where):
        if spec == "any":
            return
        if spec.startswith("record:"):
            name = spec[7:]
            if name not in self.records:
                raise Invalid(f"schema: unknown record {name!r}")
            return self.record(self.records[name], value, where)
        if spec.startswith("key:"):
            pool = spec[4:]
            if not isinstance(value, str) or value not in self.pools[pool]:
                raise Invalid(f"{where}: {value!r} is not a key in {pool}")
            return
        if spec.startswith("enum:"):
            if not isinstance(value, str) or value not in spec[5:].split(","):
                raise Invalid(f"{where}: {value!r} is not one of {spec[5:]}")
            return
        if spec == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                raise Invalid(f"{where}: expected an integer")
            return
        if spec == "bool":
            if not isinstance(value, bool):
                raise Invalid(f"{where}: expected true or false")
            return
        if not isinstance(value, str):
            raise Invalid(f"{where}: expected a string, got {type(value).__name__}")
        if spec in ("str", "text"):
            return
        if spec == "name":
            if "](" in value:
                raise Invalid(f"{where}: names are plain text; put the link in a url field")
            return
        if spec == "apa":
            if ", " not in value:
                raise Invalid(f"{where}: {value!r} is not an APA name (Surname, X.)")
            return
        if spec in PATTERNS:
            if not re.match(PATTERNS[spec], value):
                raise Invalid(f"{where}: {value!r} is not a {spec}")
            return
        raise Invalid(f"schema: unknown type {spec!r}")

    def record(self, fields, value, where):
        if not isinstance(value, dict):
            raise Invalid(f"{where}: expected a mapping")
        names = {f.rstrip("!"): f.endswith("!") for f in fields}
        specs = {f.rstrip("!"): s for f, s in fields.items()}
        for k in value:
            if k not in names:
                raise Invalid(f"{where}: unknown field {k!r}")
        for k, required in names.items():
            if k not in value:
                if required:
                    raise Invalid(f"{where}: missing field {k!r}")
                continue
            self.check(specs[k], value[k], f"{where}.{k}")


def validate(data, schema_path):
    """Exit with `file: entry: field: problem` on the first violation."""
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    v = Validator(schema, _pools(data))
    for file, spec in (schema.get("files") or {}).items():
        name = file.split("/")[-1].rsplit(".", 1)[0]
        try:
            v.check(spec, data.get(name) or {}, file)
        except Invalid as e:
            sys.exit(f"Error: {e}")

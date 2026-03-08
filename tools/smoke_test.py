from engine.mapping_manager import MappingManager

m = MappingManager()
m.load_all()
print("Profiles found:", m.profile_names())
m.activate("Latin Extended")
mappings = m.active_mappings()
tests = [
    ("ae", "æ"), ("AE", "Æ"), ("n~", "ñ"),
    ("--", "\u2013"), ("->", "\u2192"), ("...", "\u2026"),
    ("(c)", "\u00a9"), ("1/2", "\u00bd"),
]
print(f"Total mappings: {len(mappings)}")
for k, v in tests:
    got = mappings.get(k, "MISSING")
    status = "OK" if got == v else "FAIL"
    print(f"  {k!r:8} -> {got!r}  {status}")

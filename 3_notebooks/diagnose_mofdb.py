# =====================================================================
# MOFX-DB DIAGNOSTIC — paste into a new Colab cell and run.
#
# candidates came back empty, which means one of three things:
#   (a) the API call itself failed,
#   (b) it returned records but none had a `database` field we recognise,
#   (c) it returned nothing for these parameters.
# This distinguishes them and prints the real values, rather than guessing.
# =====================================================================
import collections, traceback

print("=" * 66)
print("1. CAN WE REACH THE LIBRARY AT ALL?")
print("=" * 66)
try:
    from mofdb_client.main import get_all
    import mofdb_client
    print(f"  OK — mofdb_client {getattr(mofdb_client, '__version__', 'version unknown')}")
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {e}")
    print("  Fix: !pip install -q --upgrade mofdb-client   then re-run this cell")
    raise SystemExit

print()
print("=" * 66)
print("2. WHAT COMES BACK WITH NO FILTERS AT ALL?")
print("=" * 66)
# No parameters: if this is empty too, the service or the client is the problem,
# not our query. If it returns records, the parameters were the problem.
sample = []
try:
    for i, m in enumerate(get_all({})):
        sample.append(m)
        if i >= 39:
            break
    print(f"  got {len(sample)} records with an empty parameter set")
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {e}")
    traceback.print_exc(limit=2)
    sample = []

if sample:
    m = sample[0]
    print()
    print("  attributes on a record:")
    attrs = [a for a in dir(m) if not a.startswith('_')]
    print("   ", ", ".join(attrs[:24]))
    print()
    print(f"  first record: name={getattr(m, 'name', '?')!r}  id={getattr(m, 'id', '?')}")
    print(f"                database={getattr(m, 'database', 'NO SUCH ATTRIBUTE')!r}")
    print()
    dbs = collections.Counter(str(getattr(x, "database", "MISSING")) for x in sample)
    print(f"  database values across {len(sample)} records:")
    for k, v in dbs.most_common():
        print(f"    {v:4d}  {k!r}")
else:
    print("  Nothing came back even with no filters. The service is unreachable")
    print("  or the client is broken — skip to the LOCAL CIF route below.")

print()
print("=" * 66)
print("3. WHICH PARAMETER SPELLING ACTUALLY SELECTS CoRE MOF?")
print("=" * 66)
# The exact string the server expects is not documented consistently. Try the
# plausible spellings and report which one returns records.
for label, params in [
    ('{"database": "CoREMOF 2019"}',  {"database": "CoREMOF 2019"}),
    ('{"database": "CoRE-2019"}',     {"database": "CoRE-2019"}),
    ('{"database": "CoREMOF"}',       {"database": "CoREMOF"}),
    ('{"database": "CoRE MOF"}',      {"database": "CoRE MOF"}),
]:
    try:
        got = []
        for i, m in enumerate(get_all(params)):
            got.append(str(getattr(m, "database", "MISSING")))
            if i >= 14:
                break
        uniq = collections.Counter(got)
        status = "OK  " if got else "EMPTY"
        print(f"  [{status}] {label:34s} -> {len(got):3d} records {dict(uniq) if got else ''}")
    except Exception as e:
        print(f"  [ERR ] {label:34s} -> {type(e).__name__}: {str(e)[:60]}")

print()
print("=" * 66)
print("WHAT TO DO NEXT")
print("=" * 66)
print("""  * If section 2 listed database values, copy the exact string that means
    CoRE MOF and set it as TARGET_DATABASE in Step 1, then re-run Step 2.
  * If section 3 found a spelling that returns records, use that one.
  * If everything is empty or errored, the service is not usable right now.
    Use the local-CIF route: it needs no API at all.""")

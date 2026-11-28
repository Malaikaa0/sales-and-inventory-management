"""
Count the outcomes in a `cosmic-ray dump` file.

    python summarise.py <dump.jsonl> [minimum kill rate in percent]

Exit status: 0 ok, 1 a mutant was not properly tested, 2 kill rate below the minimum.
"""
import collections
import json
import sys

INFRASTRUCTURE = ('No module named', 'ModuleNotFoundError', 'ClientConnect', 'Cannot connect', 'usage: ')

total = collections.Counter()
by_module = collections.defaultdict(collections.Counter)
by_operator = collections.defaultdict(collections.Counter)
broken = []
with open(sys.argv[1], encoding='utf-8') as handle:
    for line in handle:
        item, result = json.loads(line)
        mutation = item['mutations'][0]
        if result is None:
            outcome = 'pending'
        elif result['worker_outcome'] != 'normal':
            outcome = result['worker_outcome']
        else:
            outcome = result['test_outcome']
        total[outcome] += 1
        by_module[mutation['module_path'].replace(chr(92), '/')][outcome] += 1
        if mutation['operator_name'].startswith('sqe/'):
            by_operator[mutation['operator_name']][outcome] += 1
        output = (result or {}).get('output') or ''
        if outcome in ('pending', 'exception', 'abnormal') or any(text in output for text in INFRASTRUCTURE):
            broken.append(item['job_id'])


def rate(counts):
    tested = counts['killed'] + counts['survived'] + counts['incompetent']
    killed = counts['killed'] + counts['incompetent']
    return f'{killed}/{tested} = {100 * killed / tested:.1f}%' if tested else 'none tested'


print('mutants:', sum(total.values()), dict(total))
print('kill rate:', rate(total))
for title, groups in (('module', by_module), ('custom operator', by_operator)):
    for name, counts in sorted(groups.items()):
        print(f'{title} {name}: killed {rate(counts)}, survived {counts["survived"]}')
print('infrastructure problems:', len(broken))
if broken:
    sys.exit(1)
minimum = float(sys.argv[2]) if len(sys.argv) > 2 else 0
killed = total['killed'] + total['incompetent']
tested = killed + total['survived']
if minimum and (not tested or 100 * killed / tested < minimum):
    print(f'FAILED: kill rate is below the minimum of {minimum}%')
    sys.exit(2)

"""Check the custom operators against their examples and the real target files."""
import difflib
import sys

from cosmic_ray.mutating import mutate_code
from cosmic_ray.plugins import get_operator

TARGETS = ['transactions/services.py', 'transactions/loyalty.py', 'store/models.py', 'accounts/permissions.py']
OPERATORS = ['sqe/shift-business-limit', 'sqe/break-stock-rule']

failed = 0
for name in OPERATORS:
    operator = get_operator(name)
    for example in operator.examples():
        actual = mutate_code(example.pre_mutation_code, operator(), example.occurrence)
        if actual != example.post_mutation_code:
            failed += 1
            print(f'FAIL {name}: {example.pre_mutation_code!r} -> {actual!r}, wanted {example.post_mutation_code!r}')
    print(f'{name}: {len(operator.examples())} examples checked')
    for path in TARGETS:
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
        occurrence = 0
        while True:
            mutated = mutate_code(source, operator(), occurrence)
            if mutated is None:
                break
            compile(mutated, path, 'exec')  # every mutant must be valid Python
            changed = [line for line in difflib.unified_diff(source.splitlines(), mutated.splitlines(), n=0)
                       if line[:1] in '+-' and line[:3] not in ('+++', '---')]
            print(f'  {path} #{occurrence}: ' + ' | '.join(' '.join(line.split()) for line in changed))
            occurrence += 1
sys.exit(1 if failed else 0)

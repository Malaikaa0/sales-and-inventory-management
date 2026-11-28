"""
Write the session configs used by run.sh from cosmic-ray.toml.

    python make_config.py <template> <interpreter> <output> <local output> [module ...]

The test command gets the full interpreter path (on Windows a bare "python" can
start the system interpreter). Modules, when given, replace the module list.
"""
import re
import sys

template, interpreter, output, local_output, *modules = sys.argv[1:]
with open(template, encoding='utf-8') as handle:
    text = handle.read()
text, count = re.subn(r'^test-command = "python ', f'test-command = "{interpreter} ', text, flags=re.M)
assert count == 1, 'test-command not found'
if modules:
    listed = ', '.join(f'"{module}"' for module in modules)
    text, count = re.subn(r'^module-path = \[[^\]]*\]', f'module-path = [{listed}]', text, flags=re.M)
    assert count == 1, 'module-path not found'
with open(output, 'w', encoding='utf-8') as handle:
    handle.write(text)
with open(local_output, 'w', encoding='utf-8') as handle:
    handle.write(text.replace('name = "http"', 'name = "local"'))

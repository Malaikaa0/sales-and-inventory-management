import os

import pytest


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """Creating test users is slow with the production hasher, and no test depends on it."""
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """In CI a skipped test is a failure: a test that did not run has not passed."""
    if os.environ.get('CI', '').lower() not in ('1', 'true'):
        return
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    skipped = reporter.stats.get('skipped', []) if reporter else []
    if skipped:
        reporter.write_sep('=', f'CI: {len(skipped)} skipped test(s) fail the run', red=True)
        for report in skipped:
            reporter.write_line(f'  {report.nodeid}: {report.longrepr[-1] if report.longrepr else ""}')
        session.exitstatus = pytest.ExitCode.TESTS_FAILED

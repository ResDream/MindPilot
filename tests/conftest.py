def pytest_configure(config):
    (config.rootpath / "work").mkdir(exist_ok=True)

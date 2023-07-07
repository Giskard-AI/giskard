# %%

import datetime
from pathlib import Path

import nox
import tomli
from packaging.requirements import Requirement


@nox.session(name="custom-name")
def run(session):
    project_path = Path(".")

    # Only try to pin dependencies up to 5 years
    max_age = datetime.timedelta(days=365 * 5)

    proj_conf = tomli.load(project_path.joinpath("pyproject.toml").open("rb"))
    requirements = [Requirement(d) for d in proj_conf["project"]["dependencies"]]
    tests = [Requirement(d) for d in proj_conf["tool"]["pdm"]["dev-dependencies"]["test"]]
    devs = [Requirement(d) for d in proj_conf["tool"]["pdm"]["dev-dependencies"]["dev"]]

    f = open("test.txt", "a")
    f.write("test")
    f.close()
    # %%

    from collections import defaultdict
    from packaging.version import Version
    import requests

    min_date = datetime.datetime.now() - max_age

    dep_versions = defaultdict(list)

    for req in requirements:
        info = requests.get(f"https://pypi.org/pypi/{req.name}/json").json()
        for v in info["releases"]:
            try:
                date = max(datetime.datetime.fromisoformat(c["upload_time"]) for c in info["releases"][v])
            except ValueError:
                continue
            if date > min_date:
                dep_versions[req.name].append(Version(v))

    # %%
    def try_pinning(name, version):
        try:
            session.install(f"{name}=={version}")
            session.run("pytest", "--exitfirst", "tests/", silent=True)
            return True
        except BaseException:
            print(f"Failed with {name}=={version}")
            return False

    for req in requirements:
        session.install(f"{req}")

    for req in devs:
        session.install(f"{req}")

    for req in tests:
        if req.name == "tensorflow" or req.name == "tensorflow-text":
            continue
        session.install(f"{req}")

    session.install("pytest")

    for req in requirements:
        # Bisection
        if req.name not in ["numpy", "scipy"]:
            continue

        versions = sorted(dep_versions[req.name])

        if len(versions) == 0:
            continue

        while len(versions) > 1:
            version_idx = len(versions) // 2 - 1
            version_to_test = versions[version_idx]

            success = try_pinning(req.name, version_to_test)

            if success:
                versions = versions[: version_idx + 1]
            else:
                versions = versions[version_idx + 1:]

        min_working_version = versions[0]
        # Reinstall previous
        session.install(f"{req}")
        print(f"{req.name}: Minimum working version -> {min_working_version}")
        f = open(f"{req.name}.txt", "a")
        f.write(f"{min_working_version}")
        f.close()

# %%

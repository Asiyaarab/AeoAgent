# Contributing to AEO Agent

Thanks for your interest in making **AEO Agent** better! Here's how to get
involved.

## 🧰 Development setup

```bash
git clone https://github.com/Asiyaarab/AeoAgent.git
cd AeoAgent
python -m venv .venv && source .venv/bin/activate
make install-dev
pre-commit install
```

The `make install-dev` target installs the runtime + dev dependencies (pytest,
ruff, black, mypy).

## 🏃‍♂️ Run the tests

```bash
make test
```

We aim for **≥ 80 % coverage** of the `app/` package. New code should ship
with tests. Use `make test-cov` to see what's uncovered.

## ✨ Code style

- **Formatter:** [black](https://github.com/psf/black) (line length 100)
- **Linter:** [ruff](https://github.com/astral-sh/ruff) (config in `pyproject.toml`)
- **Type hints:** encouraged, checked with `mypy --ignore-missing-imports`

Run `make format && make lint && make typecheck` before opening a PR.
The pre-commit hooks will run these on commit.

## 🧪 Adding new features

1. **Open an issue first** to discuss what you want to change. Big features
   without a prior discussion often get rejected because they don't fit the
   project's direction.
2. Fork the repo and create a feature branch: `git checkout -b feature/cool-thing`
3. Add tests alongside your code in `tests/`.
4. Keep PRs focused — one feature/fix per PR.
5. Update the README and `CHANGELOG.md` if your change is user-facing.

## 🐛 Filing bug reports

Open a [GitHub issue](https://github.com/Asiyaarab/AeoAgent/issues) with:

- A clear title
- Steps to reproduce (with the URL you analyzed, if relevant)
- Expected vs. actual behavior
- The relevant log lines from `logs/aeo_agent.log`

## 🛡️ Security issues

**Please don't open public issues for security bugs.** See [`SECURITY.md`](./SECURITY.md)
for the responsible-disclosure process.

## 📜 License

By contributing, you agree that your contributions will be licensed under
the [MIT License](./LICENSE).

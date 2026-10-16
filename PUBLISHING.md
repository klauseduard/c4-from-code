# Publishing (author's notes)

Two ways to get this to people, neither of which depends on artifact sharing.

## 1. Send the zip

`c4-from-code-plugin.zip` is the whole package. Recipients unzip it (or not) and run
`claude --plugin-dir ./c4-from-code-plugin.zip`, or copy `skills/c4-from-code/` into their
`.claude/skills/`. Nothing else needed.

## 2. Publish a public GitHub repo (installable with /plugin)

Use your personal account so the course tutors can install it regardless of org restrictions.
The repo is its own marketplace (`.claude-plugin/marketplace.json` with `"source": "."`).

```bash
# in the unpacked folder
git init
git add -A
git commit -m "feat: c4-from-code plugin v1.0.0"
git branch -M main
git remote add origin https://github.com/klauseduard/c4-from-code.git
git push -u origin main          # username: klauseduard, password: your personal access token
git tag v1.0.0 && git push --tags
```

Then recipients run:

```text
/plugin marketplace add klauseduard/c4-from-code
/plugin install c4-from-code@klaus-tools
```

If you name the repository differently, update `homepage` and `repository` in
`.claude-plugin/plugin.json` and the install commands in `README.md`.

## Before publishing

```bash
claude plugin validate .         # manifests and layout
```

Consider adding a `LICENSE` file; none is included because that is your call.

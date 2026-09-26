# Release Kit

**Seven checks that make a release easier to verify.** Release Kit is a dependency-free Python toolkit for local builds and CI. Each check is independent and uses exit code `0` for success, `1` for a failed check, or `2` for invalid input.

| Command | Use it to |
| --- | --- |
| `checksums` | Generate SHA-256 lines for release artifacts. |
| `verify` | Detect missing or changed files against a manifest. |
| `env` | Compare variable **names** in `.env.example` and `.env` without printing values. |
| `changelog` | Require a heading for the release version. |
| `links` | Find missing relative Markdown link targets. |
| `json` | Parse one or more JSON files before packaging. |
| `arb_audit.py` | Check Flutter ARB keys and simple placeholder names before localization builds. |

## Quick start

```sh
python3 release_kit.py checksums dist app.zip > dist/SHA256SUMS
python3 release_kit.py verify dist dist/SHA256SUMS
python3 release_kit.py env .env.example .env
python3 release_kit.py changelog CHANGELOG.md 1.2.0
python3 release_kit.py links README.md docs/*.md
python3 release_kit.py json package.json config/*.json
python3 arb_audit.py lib/l10n/app_en.arb lib/l10n/app_ko.arb
```

`checksums` paths are relative to the root argument. The manifest uses the common `<sha256>  <relative-path>` format. `verify` rejects paths outside that root. The Markdown checker only checks local file targets; it does not make network requests or validate fragment anchors. `arb_audit.py` is a separate script so Flutter projects can copy or run it without the other release checks. It ignores ARB metadata and reports missing keys, extra keys, and simple `{name}` placeholder drift.

## Run the tests

```sh
python3 -m unittest -v
```

The tests cover changed release artifacts, missing environment keys, changelog headings, broken local links, malformed JSON, and ARB translation drift. All checks use only the Python standard library.

## Limitations

This toolkit does not sign artifacts, verify their origin, validate environment values, parse every Markdown syntax variant, or fully parse ICU localization expressions. Use signing and project-specific checks when a release requires them.

## License

MIT; see [LICENSE](LICENSE).

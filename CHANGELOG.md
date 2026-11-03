# Changelog

## 0.1.0 (2026-11-03)


### Features

* **dsp:** add harmonic-sum and harmonic-product f0 estimators ([73bec88](https://github.com/soheil-mp/wingbeat/commit/73bec88a831f293e5738497e45a45d1014285753))
* **dsp:** add resampling to 8 kHz, DC removal and framing ([7f5eb55](https://github.com/soheil-mp/wingbeat/commit/7f5eb55c713f4e7786b7025fc71fb39a0f4c477a))
* **dsp:** add the wingbeat band-pass and a mains-hum notch comb ([179eecd](https://github.com/soheil-mp/wingbeat/commit/179eecd3a1fe362ce81b15019118feb88a6e1645))
* **dsp:** add the YIN cross-check estimator and an agreement score ([f0879cd](https://github.com/soheil-mp/wingbeat/commit/f0879cdf94d588e74c2d86fd114dd80771069963))
* **dsp:** add Welch PSD, interpolated spectral peaks and flatness ([9cd3b3f](https://github.com/soheil-mp/wingbeat/commit/9cd3b3ff7917fcd805e0fbb363644be12d77d595))
* **reference:** add the species reference table schema and validation ([6f731ea](https://github.com/soheil-mp/wingbeat/commit/6f731ea4ae835b8a9d537aa7301f18c2c836e4b2)), closes [#12](https://github.com/soheil-mp/wingbeat/issues/12)
* **reference:** populate the species table from verified full texts ([8b5b48b](https://github.com/soheil-mp/wingbeat/commit/8b5b48b74b3595ab5fe2bf5bcd5018cb28dabe1d)), closes [#13](https://github.com/soheil-mp/wingbeat/issues/13)


### Documentation

* add README, contributing guide and security policy ([8694264](https://github.com/soheil-mp/wingbeat/commit/8694264c924fe7aeb37a27b28ee0be5f4618d4c2))
* add target architecture with data-flow and delivery-guarantee tables ([3455c82](https://github.com/soheil-mp/wingbeat/commit/3455c822c48256f61c818eedaf751ed16d2c4a74))
* add the project roadmap (19 milestones, 1,032 planned hours) ([dda83ad](https://github.com/soheil-mp/wingbeat/commit/dda83addf2932d3d3081078b53846db7bf003e80))
* add working rules for coding agents ([43740f8](https://github.com/soheil-mp/wingbeat/commit/43740f8293aae5f9c33966d81902329b24bb4acc))
* **adr:** record the ten founding architecture decisions ([54b8abc](https://github.com/soheil-mp/wingbeat/commit/54b8abc3d0a5ebf85d7dfe04f4cf8965f1cf3dbe))
* align milestone references in ADRs and research notes with the roadmap ([df0ba5c](https://github.com/soheil-mp/wingbeat/commit/df0ba5cfa1f5d62d3c3ce8594c4685d7cadc6a40))
* publish a MkDocs Material site to GitHub Pages ([1e3ff4a](https://github.com/soheil-mp/wingbeat/commit/1e3ff4a1aec75de5805ef9499b48965627c9b4f6)), closes [#7](https://github.com/soheil-mp/wingbeat/issues/7)
* **readme:** describe how roadmap items become issues ([4d51a79](https://github.com/soheil-mp/wingbeat/commit/4d51a7975a140858f30e4eaccc70284eda4d4aae))
* **research:** add literature review, data-source survey and stack selection ([ef4f853](https://github.com/soheil-mp/wingbeat/commit/ef4f853b9db81726b582c6f86dd203338d491a4f))
* **roadmap:** tick repository settings and GitHub planning ([a9ff39c](https://github.com/soheil-mp/wingbeat/commit/a9ff39cec59898dcb807564469fe032c645891b9))


### Build system

* add a dev container with the pinned toolchain ([a7813c2](https://github.com/soheil-mp/wingbeat/commit/a7813c297e2eb61ff2a3372ccfbd13fdd6d67e96)), closes [#8](https://github.com/soheil-mp/wingbeat/issues/8)
* add a justfile that mirrors every CI gate ([aabfd0d](https://github.com/soheil-mp/wingbeat/commit/aabfd0df363ddcba65378c79870da20ad6e01989)), closes [#3](https://github.com/soheil-mp/wingbeat/issues/3)
* add shared Ruff, strict mypy, pytest and coverage configuration ([0b2e1b2](https://github.com/soheil-mp/wingbeat/commit/0b2e1b21623e128bc788c2d44398c7096afacc6b)), closes [#2](https://github.com/soheil-mp/wingbeat/issues/2)
* add uv workspace with six typed member packages ([559aaf5](https://github.com/soheil-mp/wingbeat/commit/559aaf5a558c3aa26ecc5e1c5607767a034671fb)), closes [#1](https://github.com/soheil-mp/wingbeat/issues/1)
* enforce a dependency licence and scope policy on uv.lock ([f2eb101](https://github.com/soheil-mp/wingbeat/commit/f2eb10184f197cdd8e994e52867d8465952034b1)), closes [#5](https://github.com/soheil-mp/wingbeat/issues/5)


### Continuous integration

* add hook, full-history secret scan and weekly link-check workflows ([d5eaf12](https://github.com/soheil-mp/wingbeat/commit/d5eaf12d80e50298cdc8eee466773667112243c6))
* add path-filtered Python pipeline and a single CI result gate ([6a37b52](https://github.com/soheil-mp/wingbeat/commit/6a37b52952b20451d2e3a5b51528c7fb5d6fa212)), closes [#4](https://github.com/soheil-mp/wingbeat/issues/4)
* automate releases with release-please ([5476437](https://github.com/soheil-mp/wingbeat/commit/54764377edd01f52b767711dd964f04c19671319)), closes [#10](https://github.com/soheil-mp/wingbeat/issues/10)

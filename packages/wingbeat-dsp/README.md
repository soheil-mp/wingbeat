# wingbeat-dsp

Classical signal-processing estimators and the species attribution rule engine for Wingbeat.

Part of the Wingbeat workspace; see the repository README and ROADMAP.md.

## Modules

Every stage has pure batch functions and a stateful streaming class that gives the same output
however the input is chunked.

| Module | What it does |
| :-- | :-- |
| `wingbeat_dsp.conditioning` | Polyphase resampling to 8 kHz, DC removal (batch mean or a streaming one-pole blocker), windowed framing with overlap (`frame`, `Framer`) |

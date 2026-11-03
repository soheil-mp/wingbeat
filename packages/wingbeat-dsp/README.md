# wingbeat-dsp

Classical signal-processing estimators and the species attribution rule engine for Wingbeat.

Part of the Wingbeat workspace; see the repository README and ROADMAP.md.

## Modules

Every stage has pure batch functions and a stateful streaming class that gives the same output
however the input is chunked.

| Module | What it does |
| :-- | :-- |
| `wingbeat_dsp.conditioning` | Polyphase resampling to 8 kHz, DC removal (batch mean or a streaming one-pole blocker), windowed framing with overlap (`frame`, `Framer`) |
| `wingbeat_dsp.filters` | Butterworth band-pass 250–2,500 Hz and a mains-hum notch comb (50 or 60 Hz, first five harmonics only so wingbeat fundamentals survive), as SOS; `StreamingFilter` keeps state between chunks |
| `wingbeat_dsp.spectral` | Welch PSD, the dominant in-band peak with parabolic interpolation (about 0.1 Hz error on clean tones), spectral flatness |

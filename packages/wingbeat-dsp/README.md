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
| `wingbeat_dsp.harmonic` | Harmonic-sum and harmonic-product *f0* estimators with an octave-error guard (both directions) and refinement from the harmonics' interpolated peaks; median error 0.03 Hz at 10 dB SNR in a 500-case stress run |
| `wingbeat_dsp.yin` | YIN time-domain *f0* on a 4× upsampled frame with its aperiodicity, and an agreement score in cents for cross-checking estimators |

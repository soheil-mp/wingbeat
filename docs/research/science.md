# The acoustics of mosquito flight: literature review

> Status: research note for roadmap milestone M1. Collected 2 November 2026.
> Every number below is quoted from the cited source; nothing is estimated by this project.

## 1. Summary and what it means for the design

| Finding | Source | Design consequence |
| :-- | :-- | :-- |
| A flying mosquito emits a tone at its wingbeat frequency plus integer harmonics; female fundamentals in a 29-species study ranged from 342 Hz to 737 Hz. | Kim et al. 2021 | A band of roughly 250–2,500 Hz holds the fundamental and the first harmonics, so an 8 kHz sample rate is enough. |
| Males beat faster than females (roughly 1.3–1.5× in the studies below). | Rajan et al. 2025; Loh et al. 2024 | Sex is a separate axis in the reference table; male and female bands are kept separately. |
| Frequency rises with air temperature: about 8–13 Hz/°C for female *Aedes aegypti*, and about 9.6 Hz/°C at 525 Hz in a general insect formula. | Villarreal et al. 2017; Saha et al. 2024 | Every detection is **temperature-normalised** to 20 °C before attribution, using live temperature (on-board sensor or weather API). |
| A 15 °C swing moves a 500 Hz tone by about 144 Hz, which is more than the 128 Hz gap between female *Culex pipiens* and *Ae. albopictus* at a fixed temperature. | Saha et al. 2024 formula; Kim et al. 2021 table | Without normalisation, species bands overlap across a single day. This is the project's central technical argument. |
| Density, time of day, gravid status and age also shift frequency by several percent. | Kim et al. 2024; Rajan et al. 2025 | Bands need explicit tolerances, and attribution must report uncertainty, not a single label. |
| In pairwise comparisons, 26 of 29 species overlapped with at least one other species. | Kim et al. 2021 | Frequency alone can't name a species. The rule engine outputs a **ranked candidate set** narrowed by regional presence (VectorNet, GBIF) and activity time. |
| Courting pairs converge: a female harmonic and a male harmonic meet, at about 1,200 Hz in *Ae. aegypti* and 1,400–1,500 Hz in *Ae. albopictus* and *Cx. quinquefasciatus*. | Cator et al. 2009; Rajan et al. 2025 | A separate **harmonic-convergence detector** reports mating activity as its own event type. |
| Eco-acoustic recorders capture intelligible human speech within about 10 m. | Cretois et al. 2022 | Raw audio never leaves the device, a speech guard runs before uplink, and only band-limited features are sent (ADR-0008). |

## 2. The signal

The wings of a flying mosquito drive a periodic pressure wave at the wingbeat frequency *f0*.
Because the wing stroke isn't a pure sinusoid, the spectrum holds a fundamental plus a series of
integer harmonics (*2·f0*, *3·f0*, …). The relative strength of those harmonics varies with
species and recording geometry.

The sound is faint and decays fast with distance. Microphone-based systems therefore listen at
short range, for example in a cup, a bed net or a trap. This project assumes the microphone sits
**inside or right next to a trap or lure chamber**. Open-air detection at metres is out of scope.

Engineering implications:

- Harmonic estimators (harmonic product or harmonic sum spectrum, plus a time-domain YIN
  cross-check; de Cheveigné & Kawahara 2002) are more robust than single-peak picking when the
  fundamental is masked by low-frequency noise.
- Mains hum (50 Hz and harmonics in Europe), wind and rain sit largely below or across the band
  and must be modelled in the simulator and rejected by the detector.

## 3. Reference frequencies

Female mean wingbeat frequencies measured with an infrared optical sensor. The females were
mated, non-blood-fed, 3–5 days old, and recorded at 23.0 ± 0.5 °C and 60 % RH (Kim et al. 2021,
Table 1). The table shows the species relevant to this project: those most often recorded in the
Netherlands on GBIF (2 November 2026), plus major global vectors.

| Species | Mean (Hz) | SD (Hz) | Valid files | In NL top-15 on GBIF |
| :-- | --: | --: | --: | :-- |
| *Aedes vexans* | 377.62 | 26.11 | 714 | yes (rank 1) |
| *Aedes japonicus* | 383.00 | 37.24 | 690 | yes (invasive) |
| *Culex pipiens* | 408.39 | 41.40 | 867 | yes (rank 3) |
| *Aedes albopictus* | 536.16 | 31.24 | 840 | yes (invasive) |
| *Aedes aegypti* | 498.08 | 34.19 | 1,161 | no |
| *Culex quinquefasciatus* | 456.23 | 30.70 | 2,738 | no |
| *Anopheles albimanus* | 460.02 | 32.44 | 3,775 | no |
| *Anopheles quadrimaculatus* | 504.52 | 121.77 | 2,241 | no |
| *Culex restuans* | 341.87 | 29.19 | 251 | no (lowest in study) |
| *Uranotaenia lowii* | 736.87 | 58.52 | 369 | no (highest in study) |

**Known gaps.** This source has no values for several common Dutch taxa: *Culiseta annulata*,
the *Anopheles maculipennis* complex (*An. messeae*, *An. daciae*), *An. claviger*,
*An. plumbeus* and *Coquillettidia richiardii*. Milestone M1 has to find primary sources for
them. Until then the reference table marks them `frequency: unknown`. Values are never guessed.

**Method differences.** Optical and acoustic measurements of the same species differ. Kim et al.
report 498.1 Hz for *Ae. aegypti* against 664.0 Hz in an earlier microphone study recorded at
32.6 °C. They name temperature and recording device as likely causes. Every row of the reference
table therefore records modality, temperature and sex.

### Sex differences

| Species | Female (Hz) | Male (Hz) | Source |
| :-- | --: | --: | :-- |
| *Ae. albopictus* | 499.28 | 704.17 | Rajan et al. 2025 |
| *Cx. quinquefasciatus* | 414.61 | 533.99 | Rajan et al. 2025 |
| *Ae. aegypti* | 479 | 721 | Loh et al. 2024 |
| *Ae. albopictus* | 512 | 769 | Loh et al. 2024 |

These studies used different conditions from Kim et al. 2021, so the absolute values aren't
comparable across tables. That is one more reason to store conditions with every reference value.

## 4. Temperature

- **Villarreal et al. 2017.** Female *Ae. aegypti* fundamental frequency is "highly dependent
  on the environmental temperature, increasing ∼8–13 Hz with each °C gain". Body size and
  tethered versus free flight didn't change the relationship.
- **Saha et al. 2024.** From more than 302,000 field observations of flying insects with a
  near-infrared sensor between 10 °C and 38 °C, the slope grows with frequency: 2.02 Hz/°C at
  50 Hz and up to 9.63 Hz/°C at 525 Hz. The paper proposes a general correction (its Eq. 3) to a
  reference temperature *T_ref* = 20 °C:

  ```text
  f_corrected = f_initial + (−3.605e−5 · f_initial² + 0.0372 · f_initial) · (T_ref − T)
  ```

  The formula is fitted across all insects in the field study, not per species. Wingbeat
  implements it as the default and lets the reference table override the slope per species
  where a species-level source exists, such as Villarreal et al. for *Ae. aegypti*.

**Worked example.** *Ae. albopictus* at 536.16 Hz and 23 °C (Kim et al. 2021) has a slope of
about 9.58 Hz/°C from the formula, so it normalises to about 507.4 Hz at 20 °C. A 500 Hz tone
has a slope of about 9.59 Hz/°C, so a swing from 15 °C to 30 °C moves it by about 144 Hz.

## 5. Other sources of variation

- **Density, time of day, gravid status (Kim et al. 2024).** In *Cx. quinquefasciatus*, single
  females flew 6.2 % and 9.5 % faster than groups of five and ten, and 9.4 % faster by day than by
  night. Gravid females of *Cx. quinquefasciatus* and *Ae. aegypti* also had higher frequencies.
- **Age (Rajan et al. 2025).** Frequency is low just after emergence and peaks at the swarming
  stage, which the authors treat as the species' fundamental frequency.

Together these mean that a reference band is a distribution with a tolerance, not a single value.
The attribution output carries a margin (distance to band edge in SDs) and an `ambiguous` flag.

## 6. Harmonic convergence

Cator et al. (2009) showed that male and female *Ae. aegypti* adjust their wingbeats in flight so
that their flight tones meet at a shared harmonic just before mating, near 1,200 Hz. Rajan et al.
(2025) report that swarming and pairing in *Ae. albopictus* and *Cx. quinquefasciatus* depend on
convergence between the male's first and the female's second harmonic, at 1,400–1,500 Hz
combined.

The detector looks for **two simultaneous harmonic series whose harmonics coincide within a
tolerance** and emits a separate `convergence` event. It is a mating-activity indicator, and the
reference table records the expected convergence band per species where a source gives one.

## 7. Prior art and where Wingbeat differs

- **HumBug / HumBugDB** (Kiskin et al. 2021): 20 hours of labelled mosquito audio and 15 hours of
  background from 8 experiments and 36 species, recorded mainly with phones. It is released for
  machine-learning research.
- **Abuzz** (Mukundarajan et al. 2017): phones as acoustic sensors. It uses time and place
  metadata to tell overlapping species apart, the same idea behind Wingbeat's regional
  candidate filtering.
- **Optical sensors** (Kim et al. 2021; Saha et al. 2024): infrared sensors that record wingbeats
  at scale.
- **AudioMoth** (Hill et al. 2018; Lapp et al. 2023): a low-cost open acoustic logger, and one of
  the device types Wingbeat imports from.

Published work focuses on recognition accuracy. Wingbeat focuses on the system around it:
deterministic and explainable estimators, live temperature normalisation, regional candidate
filtering from open biodiversity data, privacy by design, and a streaming data platform with data
contracts, quality gates and reproducible operations. A GitHub search on 2 November 2026 turned up
wingbeat projects that were learned classifiers or hardware sketches. None was a
streaming platform. This is not an exhaustive survey.

## 8. Privacy

Cretois et al. (2022) found that speech in eco-acoustic recordings stays intelligible, and
detectable, up to about 10 m in playback tests, and that speech counts track human activity. An
acoustic sensor near a home is therefore a privacy risk by default. Wingbeat's response is in
`docs/adr/0008-privacy-by-design-audio.md`: on-device processing, no raw-audio uplink, a
deterministic speech guard, and features restricted to the mosquito band.

## 9. Context: why the Netherlands and Europe care

- The Dutch food and consumer product safety authority (NVWA) monitors invasive *Aedes* at
  high-risk import sites. A government letter to parliament of 4 December 2025 forwarded advisory
  reports from RIVM, the NVWA and the association of municipalities (VNG). The NVWA again
  handled many *Ae. albopictus* introductions in the 2025 season, and the species may become
  established at some Dutch locations within two to five years.
- The first locally acquired West Nile virus infections in the Netherlands were reported in
  2020 (Vlaskamp et al. 2020); *Culex pipiens* is the main vector there.

Wingbeat uses only environmental and biodiversity data. It never ingests human case data.

## References

- Cator LJ, Arthur BJ, Harrington LC, Hoy RR (2009). Harmonic convergence in the love songs of
  the dengue vector mosquito. *Science* 323:1077–1079. doi:10.1126/science.1166541
- Cretois B, Rosten CM, Sethi SS (2022). Voice activity detection in eco-acoustic data enables
  privacy protection and is a proxy for human disturbance. *Methods in Ecology and Evolution*
  13:2865–2874. doi:10.1111/2041-210X.14005
- de Cheveigné A, Kawahara H (2002). YIN, a fundamental frequency estimator for speech and music.
  *J. Acoust. Soc. Am.* 111:1917–1930. doi:10.1121/1.1458024
- Hill AP, Prince P, Piña Covarrubias E, Doncaster CP, Snaddon JL, Rogers A (2018). AudioMoth:
  evaluation of a smart open acoustic device for monitoring biodiversity and the environment.
  *Methods in Ecology and Evolution* 9:1199–1211. doi:10.1111/2041-210X.12955
- Kim D, DeBriere TJ, Cherukumalli S, White GS, Burkett-Cadena ND (2021). Infrared light sensors
  permit rapid recording of wingbeat frequency and bioacoustic species identification of
  mosquitoes. *Scientific Reports* 11:10042. doi:10.1038/s41598-021-89644-z
- Kim D, DeBriere TJ, Burkett-Cadena ND (2024). Effect of physiological and environmental factors
  on mosquito wingbeat frequency. *Journal of Vector Ecology* 49:R70–R77.
  doi:10.52707/1081-1710-49.2.R70
- Kiskin I, Sinka M, Cobb AD, et al. (2021). HumBugDB: a large-scale acoustic mosquito dataset.
  NeurIPS Datasets and Benchmarks Track. arXiv:2110.07607; data doi:10.5281/zenodo.4904800
- Lapp S, Stahlman N, Kitzes J (2023). A quantitative evaluation of the performance of the
  low-cost AudioMoth acoustic recording unit. *Sensors* 23:5254. doi:10.3390/s23115254
- Loh YM, Xu YYJ, Lee TT, Ohashi TS, Zhang YD, Eberl DF, Su MP, Kamikouchi A (2024). Differences
  in male *Aedes aegypti* and *Aedes albopictus* hearing systems facilitate recognition of
  conspecific female flight tones. *iScience* 27:110264. doi:10.1016/j.isci.2024.110264
- Mukundarajan H, Hol FJH, Castillo EA, Newby C, Prakash M (2017). Using mobile phones as
  acoustic sensors for high-throughput mosquito surveillance. *eLife* 6:e27854.
  doi:10.7554/eLife.27854
- Rajan P, Goswami D, Vanlalhmuaka, Datta S, Rabha B, Kamboj DV (2025). Acoustic behaviour and
  flight tone frequency changes in adult *Aedes albopictus* and *Culex quinquefasciatus*
  mosquitoes. *Scientific Reports*. doi:10.1038/s41598-025-89608-7
- Saha T, Genoud AP, Park JH, Thomas BP (2024). Temperature dependency of insect's wingbeat
  frequencies: an empirical approach to temperature correction. *Insects* 15:342.
  doi:10.3390/insects15050342
- Villarreal SM, Winokur O, Harrington L (2017). The impact of temperature and body size on
  fundamental flight tone variation in the mosquito vector *Aedes aegypti*. *Journal of Medical
  Entomology* 54:1116–1121. doi:10.1093/jme/tjx079
- Vlaskamp DR, Thijsen SF, Reimerink J, et al. (2020). First autochthonous human West Nile virus
  infections in the Netherlands, July to August 2020. *Eurosurveillance* 25(46):2001904.
  doi:10.2807/1560-7917.ES.2020.25.46.2001904
- Dutch government letter to parliament on the Asian tiger mosquito, 4 December 2025, with
  advisory reports from RIVM, NVWA and VNG.
  <https://api.eerstekamer.nl/9370000/1/j4nvi0xeni9vr2l_j9vvkfvj6b325az/vmt5gz3yq6ya/f=/vmt4gyt6xuxv.pdf>

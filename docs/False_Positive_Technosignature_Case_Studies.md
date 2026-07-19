# False-Positive Technosignature Case Studies

## Purpose and Scope

Technosignature searches look for observable evidence of technology beyond Earth. The difficult part is rarely finding an unusual signal; it is determining whether that signal can be explained by terrestrial interference, an instrument, data processing, statistics, or an unfamiliar natural phenomenon.

This document summarizes several well-known candidate events and the practical lessons they offer for designing a technosignature detection pipeline. The word *false positive* is used broadly here for candidates that attracted artificial-origin speculation but did not become confirmed technosignatures. Some have persuasive conventional explanations, while others remain unexplained or unconfirmed. An unexplained event is not evidence of an extraterrestrial origin.

## Candidate Overview

| Candidate | First reported or observed | Why it attracted attention | Present interpretation | Pipeline lesson |
|---|---:|---|---|---|
| **Tabby's Star (KIC 8462852)** | 2015 | Deep, irregular, aperiodic dimming unlike an ordinary planetary transit | Dust-related natural explanations are favored; no evidence of engineering | Compare anomalies against wavelength-dependent and time-dependent astrophysical models |
| **BLC1** | 2019 | Narrowband, drifting radio signal observed toward Proxima Centauri and initially isolated to on-target scans | Terrestrial radio-frequency interference, likely involving related electronic products | A convincing drift curve and on/off behavior do not eliminate subtle RFI |
| **Wow! Signal** | 1977 | Strong, narrowband, approximately 72-second event near the neutral-hydrogen line | Unexplained and never independently confirmed; not established as artificial | One-off events must remain unconfirmed regardless of how striking they appear |
| **HD 164595 signal** | 2015; public attention in 2016 | Reported radio excess in the direction of a Sun-like star | Not repeated; terrestrial interference or a non-technological transient is more plausible | Require prompt follow-up, raw-data review, and independent confirmation |
| **Ross 128 burst** | 2017 | Unusual radio emission apparently associated with a nearby red dwarf | Consistent with geostationary-satellite interference combined with possible stellar activity | Cross-check sky position, observing geometry, satellites, and known stellar behavior |

## 1. Tabby's Star (KIC 8462852)

### Why It Looked Unusual

Kepler observations of KIC 8462852 showed behavior that did not resemble a normal transiting planet:

- Brightness decreases reached roughly 20 percent in the deepest events.
- The dips were irregular and did not follow a simple orbital period.
- Some events had complex or asymmetric profiles.
- Early discussion emphasized the apparent lack of the strong infrared excess expected from some simple dust scenarios.

These characteristics prompted a wide range of hypotheses. A large artificial structure or swarm was discussed as a speculative possibility, not as the leading conclusion.

### Why It Is Not a Confirmed Technosignature

Follow-up observations produced evidence more compatible with obscuring material than opaque engineered structures:

- Dimming depth varies with wavelength, indicating that smaller particles preferentially block some colors.
- Dust can produce irregular, evolving, and non-periodic occultations.
- Radio and optical searches did not produce a corroborating technosignature.
- No observation requires an engineered explanation.

### Engineering Lessons

- Preserve multi-band photometry; a single broad-band anomaly discards powerful discrimination information.
- Fit several astrophysical nuisance models before assigning an anomaly score.
- Distinguish *unusual relative to a simple model* from *inconsistent with natural models*.
- Treat the absence of one expected feature, such as obvious infrared excess, as a constraint rather than proof of artificiality.
- Require corroboration in a different observable before escalating an artificial-origin hypothesis.

## 2. BLC1 (Breakthrough Listen Candidate 1)

### Why It Looked Unusual

BLC1 was detected in 2019 in Breakthrough Listen observations toward Proxima Centauri at approximately 982 MHz. It passed several early filters associated with a potential narrowband radio technosignature:

- It was narrow in frequency.
- Its frequency drifted over time.
- It persisted across multiple observations spanning several hours.
- It appeared in on-target observations and was not initially obvious in nearby off-target scans.
- Its sky direction was scientifically compelling because Proxima Centauri is the nearest stellar system to the Sun.

### How It Was Rejected

Detailed forensic analysis found other signals in the observing data that were related to BLC1. Their frequency relationships and shared characteristics supported an origin in terrestrial electronics rather than Proxima Centauri. The apparent candidate was consistent with a complex radio-frequency interference process, including electronic mixing or intermodulation products.

BLC1 matters because it resembled the output expected from several standard detection filters. Its rejection required analysis of the wider frequency-time environment, not merely the candidate cutout.

### Engineering Lessons

- Search for harmonically and algebraically related frequencies across the full receiver band.
- Test whether candidate drift appears in a family of signals, not only in one track.
- Retain sufficient raw or near-raw data to reconstruct the interference environment.
- Model local oscillators, clocks, mixers, digitizers, and observatory electronics.
- Do not treat an on-target/off-target test as infallible; intermittent or direction-dependent RFI can imitate source localization.
- Keep a complete audit trail showing which filters a candidate passed and why later evidence overruled them.

## 3. The Wow! Signal

### Why It Looked Unusual

The Wow! Signal was recorded in 1977 by Ohio State University's Big Ear radio telescope. Its enduring interest comes from a compact set of striking properties:

- It was strong relative to the surrounding background.
- It was narrowband.
- It occurred near the neutral-hydrogen spectral line around 1420 MHz.
- Its approximately 72-second duration was compatible with a fixed celestial source passing through the telescope beam.

### Why Its Status Remains Unconfirmed

The signal was not detected again despite follow-up efforts. The available observation therefore cannot establish repeatability, persistent sky localization, or independent confirmation. Natural and terrestrial explanations have been proposed, but no single explanation has achieved decisive confirmation.

The correct classification is therefore *unexplained, non-repeating, and unconfirmed*—not a verified false alarm with a known cause, and not evidence of extraterrestrial intelligence.

### Engineering Lessons

- Preserve an explicit `unexplained_unconfirmed` state rather than forcing every event into `natural`, `RFI`, or `technological` categories.
- Trigger rapid follow-up while an event's observing geometry can still be reproduced.
- Record pointing, beam shape, polarization, calibration, local hardware state, and environmental telemetry.
- Demand recurrence or independent observation before promoting a one-off signal.
- Prevent scientific interest or historical fame from being converted into a higher posterior probability without new evidence.

## 4. HD 164595

### Why It Attracted Attention

A radio event observed in 2015 in the direction of the Sun-like star HD 164595 received substantial public attention in 2016. Its association with a nearby stellar target encouraged speculation about a powerful transmitter.

### Why It Was Not Persuasive

The event lacked the evidentiary structure needed for a credible technosignature claim:

- It was a single reported event.
- It was not independently reproduced.
- Its spectral characteristics were not uniquely indicative of an engineered narrowband signal.
- Terrestrial interference or another transient explanation remained plausible.

### Engineering Lessons

- Do not equate *observed while pointed toward a star* with *originated at that star*.
- Separate target-interest scores from signal-quality and provenance scores.
- Automatically package high-priority events for independent follow-up.
- Penalize candidates for missing raw data, calibration context, or control observations.
- Keep public-interest considerations outside the scientific ranking function.

## 5. The Ross 128 Burst

### Why It Looked Unusual

In 2017, unusual radio emission was reported during observations of Ross 128, a nearby red dwarf. The initial signal did not immediately match the expected appearance of ordinary stellar activity, making both astrophysical and interference explanations worth investigating.

### How Conventional Explanations Emerged

Follow-up work favored a combination of ordinary stellar behavior and terrestrial interference, particularly emissions associated with geostationary satellites. The case illustrates how an observation aimed at a nearby star can intersect human-made transmitters in ways that are not obvious from the target name alone.

### Engineering Lessons

- Query satellite ephemerides using the observatory location, pointing, beam sidelobes, and exact observation time.
- Include frequency-allocation and transmitter databases, while recognizing that databases are incomplete.
- Compare the candidate against known flare and burst morphology for the stellar class.
- Use simultaneous control beams or nearby pointings whenever the instrument permits.
- Treat sidelobe pickup as a localization problem, not only a frequency-mask problem.

## Common Failure Modes

### 1. Terrestrial Radio-Frequency Interference

Human transmitters and electronics dominate the false-positive environment in radio SETI. Sources include:

- Communication satellites and navigation constellations
- Aircraft, radar, and microwave links
- Mobile, broadcast, and telemetry systems
- Observatory computers, network equipment, clocks, and oscillators
- Receiver harmonics, mixing products, and intermodulation
- Intermittent or moving transmitters that evade simple on/off tests

RFI may be narrowband, drifting, intermittent, or apparently localized. No single one of those features is sufficient proof of a celestial origin.

### 2. Instrumental and Processing Artifacts

Anomalies can arise anywhere between the detector and the final candidate table:

- Detector saturation, bad pixels, or unstable gain
- Digitizer artifacts and quantization effects
- Filter edges and channelization artifacts
- Calibration errors or time-standard mistakes
- Baseline subtraction and detrending failures
- Software defects, duplicated data, and metadata mismatches
- Machine-learning domain shift or preprocessing inconsistency

Instrument state and pipeline provenance should be treated as scientific data.

### 3. Incomplete Astrophysical Models

Nature produces rare signals that may initially appear artificial. Relevant phenomena include:

- Dust occultations and stellar variability
- Stellar flares and coherent stellar radio bursts
- Pulsars and rotating radio transients
- Fast radio bursts
- Astrophysical masers
- Plasma propagation, scintillation, and lensing
- Rare alignments or previously under-sampled source classes

The appropriate comparison is not with the most familiar natural phenomenon but with the full plausible natural model space.

### 4. Statistical Outliers and Multiple Testing

Large surveys generate extreme events even when every measurement is drawn from non-technological processes. Billions of time-frequency samples or light-curve points make apparently extraordinary outliers inevitable.

Pipelines should therefore:

- Track the total search volume and number of effective trials.
- Calibrate scores on realistic noise and interference distributions.
- Estimate false-discovery rates, not only per-candidate significance.
- Test the complete pipeline with signal injection and recovery.
- Reserve untouched data for final validation.
- Correct for repeated tuning on the same candidate set.

### 5. Lack of Repeatability or Independent Confirmation

A one-off event may be worth preserving and following up, but it cannot support a strong claim by itself. Confirmation can include:

- Reappearance at the same sky position
- Behavior consistent with a celestial reference frame
- Detection in multiple beams or baselines with the expected geometry
- Independent observation by another telescope
- Repetition across epochs or observing systems
- Consistent polarization, dispersion, drift, or modulation properties

Non-repetition does not prove that an event was terrestrial, but it sharply limits the conclusions that can be drawn.

### 6. Selection Bias and Narrative Contamination

Scientifically attractive targets can make ambiguous events seem more persuasive. A signal near a nearby habitable-zone planet or a star already known for unusual behavior will receive more attention, but target interest is not evidence about signal provenance.

The detection system should keep separate:

- Signal-level evidence
- Instrument and interference evidence
- Astrophysical context
- Target priority
- Follow-up feasibility
- Public or historical interest

## Recommended Verification Pipeline

The pipeline should be designed around progressive rejection and evidence preservation. A high anomaly score should initiate verification, not produce a technosignature label.

```text
Raw observations
      |
      v
Data integrity, calibration, and instrument-health checks
      |
      v
Candidate detection and calibrated anomaly scoring
      |
      v
Known RFI bands, transmitter catalogs, and satellite ephemerides
      |
      v
Full-band search for harmonics, sidebands, and mixing products
      |
      v
On/off target, multi-beam, and sidelobe consistency tests
      |
      v
Celestial-frame drift, polarization, and propagation tests
      |
      v
Astrophysical model comparison
      |
      v
Repeat search across archival and new observing epochs
      |
      v
Independent telescope confirmation
      |
      v
Human review of evidence package and reproducibility record
      |
      v
Candidate status: rejected, unresolved, or confirmed for escalation
```

## Engineering Recommendations

### Candidate Data Model

Store evidence and state transitions rather than a single opaque score. Useful fields include:

- Stable candidate identifier and immutable observation identifiers
- Observatory, instrument, beam, target, sky coordinates, and timestamps
- Frequency, bandwidth, drift rate, duration, signal-to-noise ratio, and polarization
- Calibration version, software version, model version, and configuration hash
- On-target and off-target detections and non-detections
- Harmonic, sideband, intermodulation, and neighboring-frequency relationships
- Satellite and known-transmitter coincidences
- Instrument-health and environmental telemetry
- Astrophysical model likelihoods or goodness-of-fit measures
- Repeat-search results and independent-observatory results
- Injection/recovery efficiency for the relevant signal class
- Reviewer decisions, rationales, and links to reproducible evidence

### Candidate States

Avoid a binary alien/not-alien flag. A safer state machine is:

- `detected`: produced by an automated search
- `needs_validation`: basic integrity checks not yet complete
- `likely_artifact`: instrument or processing evidence dominates
- `likely_rfi`: terrestrial interference evidence dominates
- `likely_astrophysical`: natural-source evidence dominates
- `unexplained_unconfirmed`: no adequate explanation, but insufficient confirmation
- `follow_up_requested`: observation package prepared for additional measurements
- `independently_confirmed`: reproduced by a genuinely independent system
- `escalated_candidate`: passed predefined scientific and governance gates
- `retracted`: later evidence invalidated an earlier status

Every transition should record who or what made it, the evidence used, and the pipeline version.

### Radio-Specific Features

- Narrowband width relative to instrumental resolution
- Drift rate and drift curvature in topocentric and celestial frames
- Signal persistence and duty cycle
- On/off cadence consistency
- Multi-beam localization and sidelobe response
- Harmonic spacing and algebraic frequency relationships
- Coincidence with protected, allocated, or commonly contaminated bands
- Polarization stability
- Dispersion and propagation consistency
- Cross-epoch and cross-observatory recurrence

### Optical and Photometric Features

- Dip depth, duration, symmetry, and periodicity
- Wavelength dependence of dimming
- Infrared excess and spectral-energy-distribution consistency
- Stellar variability and activity indicators
- Detector position, pixel-neighbor behavior, and aperture sensitivity
- Comparison-star and field-wide correlations
- Persistence across instruments, surveys, and reduction pipelines

### Validation and Testing

- Inject synthetic signals before detection and measure recovery across realistic conditions.
- Maintain labeled interference and artifact challenge sets, including difficult examples such as BLC1-like drift.
- Use time-separated and instrument-separated validation data to expose leakage and domain shift.
- Run ablation tests to determine which evidence actually drives rankings.
- Measure false-discovery rate, missed-detection rate, calibration error, and follow-up yield.
- Test degraded and missing-metadata scenarios explicitly.
- Reprocess historically important cases as regression tests when data rights and formats allow.
- Require reproducible candidate packets that another analyst can inspect without private pipeline state.

### Operational Safeguards

- Preserve raw data or lossless candidate neighborhoods according to a documented retention policy.
- Log all transformations and checks with machine-readable provenance.
- Freeze the candidate evidence package before public interpretation changes the analysis.
- Separate detection, verification, and external-communication permissions.
- Define escalation gates before a high-profile candidate appears.
- Use neutral language such as *candidate*, *unresolved*, and *unconfirmed* until evidence warrants stronger wording.
- Never automate public alerts, scientific claims, or authority-facing submissions from an anomaly score alone.

## Minimum Evidence Package for Escalation

Before a candidate is described as a serious technosignature candidate, its evidence package should include:

1. Verified data integrity and instrument health.
2. Reproducible detection in preserved data.
3. Quantified search volume and false-discovery context.
4. Full-band and time-adjacent RFI analysis.
5. Hardware, satellite, and transmitter cross-checks.
6. On/off, multi-beam, or equivalent localization evidence.
7. Comparison against relevant astrophysical models.
8. Repeat observation or a documented, time-bounded follow-up attempt.
9. Independent analysis and, ideally, independent-telescope confirmation.
10. A review record that states remaining conventional explanations and limitations.

## Core Takeaway

The central engineering lesson from Tabby's Star, BLC1, the Wow! Signal, HD 164595, and the Ross 128 burst is that anomaly detection and technosignature verification are different problems. Unusual events are expected in large, imperfect, interference-rich data sets. A credible system must devote at least as much effort to provenance, false-positive rejection, calibrated uncertainty, follow-up, and reproducibility as it does to detection sensitivity.

The correct default is not to dismiss anomalies, nor to treat them as artificial. It is to preserve the evidence, test increasingly demanding conventional explanations, record what remains unresolved, and escalate only when independent observations support the same conclusion.

## Works Cited

Boyajian, Tabetha S., et al. “Planet Hunters IX. KIC 8462852—Where’s the Flux?” *Monthly Notices of the Royal Astronomical Society*, vol. 457, no. 4, 2016, pp. 3988–4004. *Oxford Academic*, [https://doi.org/10.1093/mnras/stw218](https://doi.org/10.1093/mnras/stw218).

Boyajian, Tabetha S., et al. “The First Post-Kepler Brightness Dips of KIC 8462852.” *The Astrophysical Journal Letters*, vol. 853, no. 1, 2018, article L8. [https://doi.org/10.3847/2041-8213/aaa405](https://doi.org/10.3847/2041-8213/aaa405).

Croft, Steve, et al. “Breakthrough Listen Follow-up of a Transient Signal from the RATAN-600 Telescope in the Direction of HD 164595.” *Berkeley SETI Research Center*, 2016, [https://seti.berkeley.edu/HD164595.pdf](https://seti.berkeley.edu/HD164595.pdf). Accessed 14 July 2026.

Enriquez, J. Emilio, et al. “Breakthrough Listen Follow-up of the Reported Transient Signal Observed at the Arecibo Telescope in the Direction of Ross 128.” *International Journal of Astrobiology*, vol. 18, no. 1, 2019, pp. 33–39. *Cambridge University Press*, [https://doi.org/10.1017/S1473550417000465](https://doi.org/10.1017/S1473550417000465).

Gray, Robert H., and Kevin B. Marvel. “A VLA Search for the Ohio State ‘Wow.’” *The Astrophysical Journal*, vol. 546, no. 2, 2001, pp. 1171–77. [https://doi.org/10.1086/318272](https://doi.org/10.1086/318272).

Harp, G. R., et al. “Radio SETI Observations of the Anomalous Star KIC 8462852.” *The Astrophysical Journal*, vol. 825, no. 2, 2016, article 155. [https://doi.org/10.3847/0004-637X/825/2/155](https://doi.org/10.3847/0004-637X/825/2/155).

Sheikh, Sofia Z., et al. “Analysis of the Breakthrough Listen Signal of Interest BLC1 with a Technosignature Verification Framework.” *Nature Astronomy*, vol. 5, 2021, pp. 1153–62. [https://doi.org/10.1038/s41550-021-01508-8](https://doi.org/10.1038/s41550-021-01508-8).

Smith, Shane, et al. “A Radio Technosignature Search towards Proxima Centauri Resulting in a Signal of Interest.” *Nature Astronomy*, vol. 5, 2021, pp. 1148–52. [https://doi.org/10.1038/s41550-021-01479-w](https://doi.org/10.1038/s41550-021-01479-w).

## Source Note

This document was prepared from the user-provided referenced conversation and reorganized for use by a coding agent. The citation markers embedded in that conversation were not resolvable source links, so the Works Cited section was reconstructed from primary research papers and institutional records. Scientific status statements should still be checked against the latest primary literature before publication or use in a current research claim.

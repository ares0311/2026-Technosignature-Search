# Fermi Paradox and Technosignature Search Strategy

Last updated: 2026-06-27

Target project: `2026 Technosignatures`

## Purpose

This brief translates the Fermi paradox literature into practical guidance for a technosignature coding agent. The goal is not to solve the paradox. The goal is to map proposed solutions onto searchable observables, data products, priors, null-result interpretation, and pipeline design.

The core lesson: do not build a technosignature project around one assumed signal type. Different Fermi paradox solutions predict different evidence: narrowband radio, optical pulses, waste heat, atmospheric industry, anomalous light curves, solar-system artifacts, lunar/regolith debris, probes, or no detectable signature at all.

## The Fermi Paradox in One Operational Sentence

If technological civilizations are common, long-lived, expansion-capable, and detectable, then the absence of accepted evidence is surprising; therefore at least one of those assumptions is wrong, or our searches are still too shallow, too narrow, or pointed at the wrong observables.

Important caution: Robert Gray argues the so-called paradox is historically and logically overstated: Fermi did not publish the argument usually attributed to him, and “they are not here, therefore they do not exist” is closer to Hart/Tipler-style reasoning than to Fermi's original question. For a coding agent, this matters because the project should treat the paradox as a hypothesis generator, not as a theorem.

Source: Gray, “The Fermi Paradox is Neither Fermi's Nor a Paradox” https://arxiv.org/abs/1605.09187

## Paul Davies: Why He Matters for This Project

Paul Davies is a physicist and astrobiologist associated with Arizona State University and the BEYOND Center. He chaired the SETI Post-Detection Science and Technology Taskgroup of the International Academy of Astronautics and has written extensively about SETI, astrobiology, post-detection questions, and the limitations of radio-only search strategies.

Davies is especially useful for this technosignatures project because he pushes the search beyond “listen for a deliberate radio message” into low-cost forensic searches for technological traces in existing data.

### Davies-Style Search Principles

| Davies idea | Meaning | Coding implication |
|---|---|---|
| Widen SETI beyond deliberate radio beacons | A civilization may not be transmitting to us, but its technology may leave indirect traces. | Support multi-modal technosignature classes: radio, optical, infrared, surface artifacts, biological/genomic anomalies, atmospheric industry. |
| Search existing databases cheaply | SETI has low probability but high impact; existing astronomy, planetary, biology, and Earth-science databases can be searched at low marginal cost. | Prefer archive-first pipelines: MAST, IRSA, Gaia, WISE, LRO, Breakthrough Listen open data, public spectra, citizen-science products. |
| Look for artifacts on the Moon | The Moon's surface is stable, airless, and heavily imaged; LRO imagery enables searches for non-human artifacts. | Add a solar-system artifact module or future backlog item: lunar image anomaly detection with strict false-positive controls. |
| “Footprints of alien technology” | Technology alters environments; signatures may persist after the civilization disappears. | Include long-lived evidence, not just live signals: waste heat, debris, probes, altered surfaces, unusual isotopic/chemical signatures. |
| Genomic SETI is low-cost but speculative | If genomes are already sequenced, one could search for artificial patterns, while recognizing mutation/noise issues. | Keep as a speculative, low-priority module unless project scope expands into bioinformatics. Mark high false-positive risk. |
| Post-biological intelligence | Advanced civilizations may become machine-based, computational, inward-facing, or hard to recognize. | Do not assume human-like radio behavior, planetary residence, biological timescales, or expansion aesthetics. |
| Post-detection discipline | Candidate discovery has governance, communication, and verification consequences. | Candidate pipeline must enforce evidence packets, reproducibility, non-alarmist language, and independent follow-up gates. |

### Key Davies Sources

- Paul Davies biography/context: https://en.wikipedia.org/wiki/Paul_Davies
- `The Eerie Silence` overview: https://en.wikipedia.org/wiki/The_Eerie_Silence
- Davies, “Footprints of alien technology,” Acta Astronautica 2012: https://ui.adsabs.harvard.edu/abs/2012AcAau..73..250D
- Davies & Wagner, “Searching for alien artifacts on the moon,” Acta Astronautica 2013: https://asu.elsevierpure.com/en/publications/searching-for-alien-artifacts-on-the-moon/
- IAA SETI post-detection context: https://www.setileague.org/iaaseti/postdet.htm

## Taxonomy of Fermi Paradox Solutions

Use this taxonomy as a schema. Each solution family should be represented in code as:

- `hypothesis_id`
- `claim`
- `expected_observables`
- `best_datasets`
- `search_methods`
- `null_result_interpretation`
- `testability`
- `priority`

### 1. We Have Not Searched Enough

Claim: SETI has sampled only a tiny fraction of the possible search space.

Observable implication: null results in narrowband radio do not strongly constrain other signal types, times, sky positions, bandwidths, polarizations, cadences, or non-radio technosignatures.

Search guidance:

- Maintain a “cosmic haystack coverage” module.
- Record frequency, sky area, time-on-target, bandwidth, sensitivity, polarization, drift-rate range, signal class, and repetition criteria.
- Prefer incremental coverage metrics over binary “searched/not searched.”

Key source: Wright et al., “How Much SETI Has Been Done? Finding Needles in the n-Dimensional Cosmic Haystack” https://arxiv.org/abs/1809.07252

### 2. Life Is Rare

Claim: abiogenesis may be rare, even if habitable planets are common.

Observable implication: biosignatures and technosignatures both sparse; absence of technosignatures is unsurprising.

Search guidance:

- Couple technosignature target selection to astrobiology priors: rocky planets, stable climates, stellar age, metallicity, low flare environments, biosignature plausibility.
- Do not over-prioritize raw planet count; rank by long-term habitability and detectability.

Best datasets:

- NASA Exoplanet Archive
- Gaia stellar ages/kinematics
- TESS/Kepler planet catalogs
- JWST/exoplanet spectra where available

### 3. Complex Life or Intelligence Is Rare

Claim: microbial life may be common, but eukaryotes, multicellularity, intelligence, language, or tool use may require rare transitions.

Observable implication: biosignatures may be more common than technosignatures.

Search guidance:

- Track biosignature context separately from technosignature context.
- Do not assume biosignature-positive planets are near-term technosignature targets.
- Add `evolutionary_complexity_prior` fields but keep uncertainty high.

Sources:

- Forgan, “Numerical Testing of the Rare Earth Hypothesis” https://arxiv.org/abs/1001.1680
- Forgan, “A Numerical Testbed for Hypotheses of Extraterrestrial Life and Intelligence” https://arxiv.org/abs/0810.2222
- Mills et al., hard-steps reassessment: https://pmc.ncbi.nlm.nih.gov/articles/PMC11827626/
- Haqq-Misra et al., observational constraints on the Great Filter: https://arxiv.org/pdf/2002.08776

### 4. The Great Filter

Claim: one or more low-probability transitions prevent life from becoming galaxy-spanning technological civilization.

Possible filters:

- abiogenesis
- eukaryogenesis
- multicellularity
- intelligence
- technological civilization
- long-term stability
- interstellar expansion
- AI/self-destruction
- ecological collapse
- demographic collapse
- failure to become autonomous machine civilization

Observable implication: the location of the filter changes what we should expect to find.

| Filter location | Search expectation |
|---|---|
| Before life | few/no biosignatures, few/no technosignatures |
| Between life and intelligence | possible biosignatures, rare technosignatures |
| After technology | transient technosignatures, ruins, waste, artifacts, dead probes |
| After expansion capability | local/planetary technosignatures but no galactic engineering |

Search guidance:

- Build searches for extinct or transient technologies, not just active beacons.
- Prioritize long-lived artifacts and waste signatures because they reduce the need for temporal overlap.
- Include civilization-lifetime priors in detection simulations.

Sources:

- Bailey, “Could AI be the Great Filter?” https://arxiv.org/abs/2305.05653
- Dougan, “The Great Filter hypothesis -- a new Great Filter?” https://arxiv.org/abs/2602.08188
- Jiang et al., “Extraterrestrial Life and Humanity's Future in the Universe” https://arxiv.org/pdf/2210.10582

### 5. Civilizations Are Short-Lived or Radio-Loud Only Briefly

Claim: technological phases may be brief, and radio leakage may fade as societies move to fiber, tight beams, spread-spectrum, or other less detectable systems.

Observable implication: classical radio leakage has low duty cycle.

Search guidance:

- Search for intentional beacons and high-power leakage separately.
- Add time-domain recurrence logic: a signal's non-repeatability may reflect duty cycle, not only false positive.
- Expand into technosignatures less dependent on synchronized timing: artifacts, waste heat, atmospheric industry, debris.

### 6. Interstellar Travel or Expansion Is Hard

Claim: physical, economic, biological, or sociological barriers prevent large-scale expansion.

Observable implication: no solar-system artifacts and no Kardashev III engineering may coexist with remote civilizations.

Search guidance:

- Do not let absence of probes suppress remote technosignature searches too much.
- Still search for local artifacts because the cost is low and the temporal baseline is excellent.

Sources:

- Gray's Hart/Tipler critique: https://arxiv.org/abs/1605.09187
- Cotta & Morales, probe exploration simulations: https://arxiv.org/pdf/0907.0345

### 7. Self-Replicating Probes Should Exist

Claim: if any civilization builds self-replicating probes, the Galaxy could be explored quickly relative to Galactic age.

Observable implication: absence of probes in our Solar System is informative only if we have searched enough, which we have not.

Search guidance:

- Search stable locations: Moon, Earth-Moon Lagrange points, co-orbitals, Trojan populations, asteroid belt, Kuiper belt, long-lived lunar/regolith records.
- Build anomaly detection for surface imagery, unusual orbital objects, artificial spectra, non-natural shapes, repeated glints, thermal anomalies.
- Maintain extreme false-positive controls because natural geology and human spacecraft/debris dominate.

Sources:

- Wiley, “The Fermi Paradox, Self-Replicating Probes, and the Interstellar Transportation Bandwidth” https://arxiv.org/abs/1111.6131
- Ellery, “Technosignatures of Self-Replicating Probes in the Solar System” https://arxiv.org/abs/2510.00082
- Haqq-Misra & Kopparapu, “On the likelihood of non-terrestrial artifacts in the Solar System” https://arxiv.org/pdf/1111.1212
- Davies & Wagner, lunar artifacts: https://asu.elsevierpure.com/en/publications/searching-for-alien-artifacts-on-the-moon/

### 8. They Are Here, But Hidden, Dormant, Small, or Unrecognized

Claim: probes/artifacts could exist but be physically small, inactive, camouflaged, buried, in unsearched locations, or not recognized as artificial.

Observable implication: solar-system artifact searches need coverage accounting.

Search guidance:

- Store negative-search metadata: searched area, resolution, illumination, object-size sensitivity, spectral bands, artifact classes.
- For lunar/planetary imagery, use multi-scale anomaly detection and compare to known human artifacts as positive controls.
- Avoid open-ended “anything weird” classification; define artifact templates and anomaly classes.

### 9. Zoo, Interdict, or Deliberate Non-Interference

Claim: civilizations know about us but avoid contact.

Observable implication: deliberate signals may be absent; accidental or legacy artifacts may still exist.

Search guidance:

- This is hard to test directly.
- Indirect tests: look for leakage, waste heat, old artifacts, or solar-system probes that do not communicate.
- Avoid building priors that require aliens to be socially uniform; treat as low-testability.

### 10. Dark Forest / Deliberate Silence

Claim: civilizations hide because transmitting is dangerous.

Observable implication: beacons and leakage are rare; stealthy or passive technosignatures may be more likely than messages.

Search guidance:

- Prioritize non-communicative signatures: waste heat, atmospheric pollutants, industrial nightside lights, probes, mining debris.
- Do not make METI assumptions part of the default search.
- Keep candidate-publication discipline because false public alarm around “hostile aliens” is unhelpful.

### 11. They Use Channels We Are Not Searching

Claim: advanced communication may use optical lasers, neutrinos, gravitational waves, quantum-like protocols, directed tight beams, or unknown physics.

Observable implication: radio null results weakly constrain ETI.

Search guidance:

- Keep signal-type abstraction clean.
- Pipeline should support `radio_narrowband`, `radio_broadband`, `optical_pulse`, `infrared_excess`, `atmospheric_spectral`, `artifact_image`, `orbital_anomaly`, `lunar_regolith_debris`.
- For radio, account for Doppler drift, scattering, stellar wind effects, and signal broadening.

Recent direction:

- Space weather may broaden radio technosignals and make narrowband assumptions too strict. Treat stellar environment as part of signal morphology modeling.

Source: Gajjar/Brown space-weather discussion summarized in 2026 reporting: https://www.livescience.com/space/extraterrestrial-life/something-in-space-may-be-changing-alien-signals-before-they-can-reach-earth-scientists-have-a-solution

### 12. They Are Post-Biological or Computationally Inward

Claim: advanced civilizations may become machine intelligences, optimize computation, reduce outward waste, migrate to cold environments, or become hard to distinguish from natural systems.

Observable implication: biological assumptions fail; signals may be low-power, intermittent, cold, or located far from habitable zones.

Search guidance:

- Include white dwarfs, outer-system bodies, cold environments, and low-temperature waste-heat searches in long-term backlog.
- Do not restrict targets to Earth-like planets.
- For Davies-style post-biological speculation, keep the project broad but evidence-driven.

Related source:

- Sandberg et al., “That is not dead which can eternal lie: the aestivation hypothesis” https://arxiv.org/abs/1705.03394

### 13. Aestivation Hypothesis

Claim: advanced civilizations may wait until the universe is colder to perform computation more efficiently.

Observable implication: large-scale active technosignatures may be absent now, but dormant infrastructure or stored resources may exist.

Search guidance:

- Look for dormant artifacts, unusual resource configurations, or engineered cold structures.
- Low current priority because observables are ambiguous; useful as a reminder not to require active broadcasting.

Source: Sandberg et al. https://arxiv.org/abs/1705.03394

### 14. Grabby Aliens / We Are Early

Claim: expansionist civilizations appear rarely, expand visibly, and prevent later independent civilizations in their future volume. We may be early because otherwise our region would already be occupied.

Observable implication: large expanding domains may exist far away or not yet reached us; nearby searches may fail even if the universe eventually becomes engineered.

Search guidance:

- Add extragalactic megastructure/waste-heat searches as a separate class.
- Search for large-scale galaxy anomalies, not just nearby stars.
- Treat non-detections of Kardashev III civilizations as constraints on expansionist models.

Source: Hanson et al., “If Loud Aliens Explain Human Earliness, Quiet Aliens Are Also Rare” https://arxiv.org/abs/2102.01522

### 15. Rare Earth / Galactic Habitability Constraints

Claim: many locations are hostile due to metallicity, supernovae, gamma-ray bursts, M-dwarf flares, tidal locking, ocean worlds, impacts, or unstable climates.

Observable implication: target ranking should use astrophysical habitability and stellar environment, not just planet occurrence.

Search guidance:

- Score targets by stellar age, metallicity, activity, flare rate, multiplicity, galactic environment, planet type, and long-term climate plausibility.
- For M dwarfs, radio SETI may be less favored if flaring and stellar wind disrupt local development or signal propagation; compensate with alternative methods.

Sources:

- Ćirković, “Fermi's Paradox - The Last Challenge for Copernicanism?” https://arxiv.org/abs/0907.3432
- Ćirković, M-dwarf habitability implications for SETI: https://arxiv.org/pdf/2007.12645
- Schleicher & Bovino, astrophysical/dynamical effects: https://arxiv.org/abs/2206.06967

### 16. Ocean Worlds / Subsurface Biospheres

Claim: life may often arise in subsurface oceans, isolated from fire, atmosphere, stars, and radio.

Observable implication: life can be common while technology is rare.

Search guidance:

- Do not confuse high astrobiological potential with high technosignature probability.
- Ocean worlds are excellent biosignature targets but weak technosignature targets unless there is surface access or industrial activity.

### 17. They Are Detectable But We Misclassify Them

Claim: some anomalous astronomical phenomena could be technological but are classified as natural or ignored.

Observable implication: anomaly detection matters, but false positives dominate.

Search guidance:

- Build anomaly pipelines with astrophysical veto modules.
- Every anomaly needs a “mundane explanation checklist.”
- Use human-readable evidence packets: cutouts, spectra, light curves, catalog flags, cross-matches, model residuals.

Sources:

- Long, “A Critical Review on the Assumptions of SETI” https://arxiv.org/pdf/1901.10551
- Project Hephaistos II: https://arxiv.org/abs/2405.02927
- Blain critique of WISE/Gaia Dyson candidates: https://arxiv.org/abs/2409.11447
- Ren et al., background contamination: https://arxiv.org/abs/2405.14921

### 18. Simulation, Planetarium, or Strong Zoo Variants

Claim: our observations are manipulated or constrained.

Observable implication: usually low or zero testability.

Search guidance:

- Do not prioritize in code.
- Record as philosophical context only unless a specific falsifiable observable is proposed.

### 19. The Paradox Dissolves Under Uncertainty

Claim: Drake-equation parameters are so uncertain that a silent universe should not surprise us.

Observable implication: null results shift priors but do not force exotic explanations.

Search guidance:

- Use probabilistic priors with huge uncertainty intervals.
- Avoid hard-coded assumptions like “N civilizations must be large.”
- Interpret null results as constraints on model families and search volumes.

Source: Sandberg, Drexler, Ord, “Dissolving the Fermi Paradox” https://arxiv.org/abs/1806.02404

## How Fermi Solutions Should Guide Technosignature Search

### Search Portfolio

| Search class | Fermi solution families addressed | Priority |
|---|---|---|
| Radio narrowband and drifting signals | active communicators, beacons, early radio civilizations | High but not exclusive |
| Optical/IR pulses | beacons using non-radio channels | Medium-high |
| WISE/Gaia/2MASS IR excess | waste heat, megastructures, post-biological industry | High |
| TESS/Kepler light-curve anomalies | transiting megastructures, unusual engineering, time-domain anomalies | High |
| Exoplanet atmosphere pollutants | industrial civilizations, terraforming, atmospheric engineering | Medium now, higher with better spectra |
| Solar-system artifact search | probes, past visitors, Davies-style footprints, self-replicating probes | Medium-high because of long temporal baseline |
| Lunar surface/regolith search | ancient artifacts, interstellar debris, low-cost archival forensic search | Medium |
| Extragalactic waste heat / galaxy anomalies | Kardashev III, grabby/loud aliens | Medium |
| Genomic SETI | Davies-style speculative terrestrial footprint | Low unless bioinformatics scope exists |

### Project Architecture Implications

Build around `technosignature_modalities`, not one pipeline.

Recommended schema:

```yaml
candidate:
  candidate_id:
  modality: radio_narrowband | optical_pulse | ir_excess | light_curve_anomaly | atmospheric_spectrum | surface_artifact | orbital_artifact | debris
  source_ids:
    gaia:
    tic:
    wise:
    two_mass:
  data_products:
  detection_method:
  detection_statistic:
  astrophysical_vetoes:
  instrumental_vetoes:
  contamination_risks:
  fermi_hypothesis_links:
  followup_needed:
  confidence_level:
  claim_language: anomaly | signal_of_interest | candidate | rejected
```

### Ranking Priors

Use multiple rankings, not one global score:

| Score | Meaning |
|---|---|
| `detectability_score` | Is this signal measurable with current data? |
| `ambiguity_score` | How many natural/instrumental mimics exist? Lower is better. |
| `longevity_score` | Could the signal persist without temporal overlap? |
| `coverage_value` | Does searching this class constrain a Fermi solution family? |
| `followup_feasibility` | Can another instrument test it? |
| `cost_to_search` | Archive query, GPU run, telescope proposal, lab sample, etc. |

### Null Result Handling

Every search should output:

- searched target count
- sky/frequency/wavelength/time coverage
- sensitivity limits
- artifact size limits where relevant
- false-positive rejection criteria
- model family constrained
- model family not constrained

Example: a WISE/Gaia null result constrains warm waste-heat megastructures for stars above detection thresholds. It does not constrain quiet radio transmitters, cold computation, hidden probes, ocean-world biology, or extinct civilizations without artifacts.

## Recommended Coding-Agent Backlog

### Phase 1: Literature and Hypothesis Encoding

1. Create `fermi_hypotheses.yaml` from the taxonomy above.
2. Add fields for testability, expected observables, datasets, and candidate modalities.
3. Link each technosignature candidate to one or more Fermi hypothesis families.

### Phase 2: Data and Search Modules

1. `wise_gaia_ir_excess_pipeline`
2. `tess_kepler_anomaly_pipeline`
3. `breakthrough_listen_radio_candidate_packet`
4. `solar_system_artifact_backlog`
5. `lunar_lro_artifact_backlog`
6. `atmospheric_industrial_gas_watchlist`

### Phase 3: Evidence Packet Standard

Every candidate packet should include:

- source identifiers and coordinates
- raw data references
- plots/cutouts/spectra/light curves
- detection statistic
- false-positive checklist
- Fermi hypothesis relevance
- follow-up observation recommendation
- status: `candidate`, `needs_followup`, `likely_artifact`, `rejected`, `published`

### Phase 4: Coverage Dashboard

Build a dashboard that answers:

- Which Fermi solution families have we meaningfully tested?
- Which signal modalities have zero coverage?
- Which datasets are searched but shallow?
- Which null results are actually informative?
- Which candidates require follow-up?

## Highest-Value Reading List

### Fermi Paradox Foundations and Reviews

- Ćirković, “Fermi's Paradox - The Last Challenge for Copernicanism?” https://arxiv.org/abs/0907.3432
- Gray, “The Fermi Paradox is Neither Fermi's Nor a Paradox” https://arxiv.org/abs/1605.09187
- Sandberg, Drexler, Ord, “Dissolving the Fermi Paradox” https://arxiv.org/abs/1806.02404
- Crawford, “Some Thoughts on the Future of Technosignature Searches: Constraining the Fermi Paradox” https://arxiv.org/abs/2606.00463

### Search Volume and SETI Strategy

- Wright et al., “How Much SETI Has Been Done?” https://arxiv.org/abs/1809.07252
- Wright et al., “The Case for Technosignatures” https://arxiv.org/abs/2203.10899
- NASA Technosignatures Workshop Report: https://arxiv.org/abs/1812.08681

### Probes, Artifacts, and Solar-System SETI

- Davies, “Footprints of alien technology” https://ui.adsabs.harvard.edu/abs/2012AcAau..73..250D
- Davies & Wagner, “Searching for alien artifacts on the moon” https://asu.elsevierpure.com/en/publications/searching-for-alien-artifacts-on-the-moon/
- Haqq-Misra & Kopparapu, “On the likelihood of non-terrestrial artifacts in the Solar System” https://arxiv.org/pdf/1111.1212
- Wiley, self-replicating probes: https://arxiv.org/abs/1111.6131
- Ellery, self-replicating probes in the Solar System: https://arxiv.org/abs/2510.00082

### Rare Earth, Great Filter, and Astrobiological Priors

- Forgan, Rare Earth numerical test: https://arxiv.org/abs/1001.1680
- Forgan, numerical testbed: https://arxiv.org/abs/0810.2222
- Haqq-Misra et al., Great Filter constraints: https://arxiv.org/pdf/2002.08776
- Bailey, AI as Great Filter: https://arxiv.org/abs/2305.05653
- Schleicher & Bovino, astrophysical processes: https://arxiv.org/abs/2206.06967

### Exotic or Speculative but Useful Hypothesis Generators

- Sandberg et al., aestivation: https://arxiv.org/abs/1705.03394
- Hanson et al., grabby aliens: https://arxiv.org/abs/2102.01522
- Wandel, contact era/probes after technosignatures: https://arxiv.org/abs/2211.16505
- Long, critical review of SETI assumptions: https://arxiv.org/pdf/1901.10551

### Candidate Vetting and Post-Detection

- SETI post-detection protocols update: https://arxiv.org/abs/2510.14506
- SETI post-detection futures: https://arxiv.org/abs/2507.11587
- IAA SETI post-detection context: https://www.setileague.org/iaaseti/postdet.htm

## Strong Recommendations for the Technosignatures Project

1. Treat Fermi paradox solutions as model families, not beliefs.
2. Keep the search multi-modal from the start.
3. Prioritize archival searches with low marginal cost and high reproducibility.
4. Separate “active signal” searches from “long-lived artifact” searches.
5. Build null-result accounting as a first-class output.
6. Add a Davies-inspired artifact-search backlog: Moon, solar-system objects, unusual orbital bodies, archival planetary imagery.
7. Add a “false positive first” culture: every candidate must try to defeat itself.
8. Do not restrict targets to Earth analogs; post-biological or artifact hypotheses may favor non-habitable environments.
9. Do not let radio SETI dominate the ontology, even if it remains scientifically important.
10. Encode follow-up needs directly into candidate objects.

## Bottom Line for the Coding Agent

The Fermi paradox should make this project broader, more Bayesian, more archival, and more disciplined. A good technosignature system should not ask only “is this an alien signal?” It should ask:

- Which Fermi-solution family would this observation support or constrain?
- What ordinary astrophysical or instrumental explanations have been ruled out?
- How much search volume did this result actually cover?
- What follow-up would make the candidate stronger or kill it?
- Is this a live signal, a persistent artifact, a waste product, an atmospheric signature, or a catalog anomaly?

That structure lets the project produce useful science even when it finds nothing.


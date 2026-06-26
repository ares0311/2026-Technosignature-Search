# Alien Technosignatures: Satellite, AI, and Literature Brief for Coding Agents

Last updated: 2026-06-26

## Mission Objective

Build software that searches for possible technosignature candidates in public astronomical data while being conservative about false positives. The field is low-base-rate and contamination-heavy. The coding agent should optimize for anomaly discovery, reproducibility, source cross-matching, astrophysical vetoes, and follow-up prioritization, not for declaring detections.

## Ranked Space Assets and Satellites

Ranking criteria: technosignature relevance, archive scale, anomaly-search value, wavelength coverage, cross-match utility, and practical data access.

| Rank | Asset | Status | Best Use | Why It Ranks Here | Data / Access |
|---:|---|---|---|---|---|
| 1 | WISE / NEOWISE | Completed; archival | Mid-infrared waste-heat searches, Dyson-sphere-style excesses | The most important space archive for waste-heat technosignature searches. WISE mid-IR bands are central to Dyson sphere / megastructure candidate pipelines. | IRSA WISE/NEOWISE. |
| 2 | Gaia | Archive continuing | Stellar distances, luminosities, colors, astrometric vetting, cross-match backbone | Gaia makes WISE excesses scientifically interpretable by giving distances, stellar properties, and contamination checks. Essential for Project Hephaistos-style searches. | ESA Gaia Archive via ADQL/TAP. |
| 3 | TESS | Active | Optical time-domain anomalies, SETI ellipsoid searches, unusual light curves | TESS gives large-scale, high-cadence light curves and continuous viewing zones. Useful for transits, pulses, synchronized-event searches, and anomaly detection. | MAST. |
| 4 | Kepler / K2 | Completed | High-precision long-baseline anomaly detection | Kepler remains the cleanest public archive for strange light curves, transit-like megastructure hypotheses, and anomaly-method benchmarking. | MAST. |
| 5 | JWST | Active | Follow-up spectroscopy of atmospheric or IR-excess candidates | Not a survey tool, but can test atmospheric technosignature gases or candidate SEDs if proposal time is awarded. | MAST public archive; proposals for new data. |
| 6 | Hubble | Active/legacy | UV/optical follow-up, archival spectra, candidate vetting | Useful for follow-up and host characterization, less central than WISE/Gaia/TESS for broad searches. | MAST. |
| 7 | Spitzer | Completed | Infrared legacy follow-up and SED constraints | Useful for older IR photometry and follow-up of excess sources. Lower scale than WISE for all-sky searches. | IRSA. |
| 8 | Roman | Future | Wide-field IR, microlensing/time-domain, coronagraph tech demo | Future value for anomaly searches and exoplanet context; not available as an archive yet. | NASA archive after launch. |
| 9 | Ariel | Future | Atmospheric population survey | Potentially relevant to atmospheric technosignatures such as industrial gases, but primarily an exoplanet atmosphere mission. | ESA archive after launch. |
| 10 | Habitable Worlds Observatory | Concept/development | Future direct imaging of habitable exoplanets | Long-term best platform for biosignature/technosignature atmospheric context, but not operational. | No archive yet. |
| 11 | IRAS | Completed legacy | Early all-sky infrared excess searches | Historically important but less capable than WISE. | IRSA. |

Important non-satellite context: Breakthrough Listen, Green Bank Telescope, Parkes/Murriyang, MeerKAT, FAST, VLA/VLASS, LOFAR, ATA, and VERITAS are central for radio/optical technosignatures. Satellite archives are strongest for indirect technosignatures: waste heat, anomalous light curves, atmospheric gases, and target selection.

## Credentials and Access Requirements

| Task | Credentials Needed | Notes |
|---|---|---|
| WISE/Gaia/2MASS cross-match searches | Usually none | IRSA and Gaia can be queried anonymously. Large async jobs benefit from accounts. |
| TESS/Kepler light-curve anomaly search | Usually none | MAST public archive is enough for most coding work. |
| Breakthrough Listen open data | Usually none for public datasets; HPC/storage needed | Data volume is large. Some collaboration products may require partnership. |
| New radio/optical observations | Telescope proposal or collaboration | Serious follow-up needs telescope time and domain-specific RFI handling. |
| JWST/Hubble follow-up | Peer-reviewed proposal | Technosignature framing must survive strong astrophysical false-positive scrutiny. |
| Claiming a candidate | No formal credential, but scientific burden is very high | Requires independent follow-up, contamination rejection, ordinary astrophysics exclusion, and cautious language. |

## Frontier AI and Computational Methods

| Method | Implementation Target | Why It Is Used | Key Sources |
|---|---|---|---|
| Unsupervised anomaly detection on light curves | Kepler, K2, TESS | Technosignatures are not expected to look like labeled training examples. Anomaly detection surfaces odd light curves for human/scientific vetting. | Martínez-Galarza et al. 2021: https://academic.oup.com/mnras/article/508/4/5734/6368852; Crake & Martínez-Galarza 2023: https://arxiv.org/abs/2301.10264 |
| Deep-learning radio technosignature search | Breakthrough Listen GBT/Parkes data | Learns signal morphologies and RFI rejection beyond traditional narrowband/drift-rate filters. | Ma et al. 2023: https://arxiv.org/abs/2301.12670; Berkeley SETI summary: https://seti.berkeley.edu/ml_gbt/ |
| Anomaly detection in radio spectra | Breakthrough Listen observations | Reduces dependence on a pre-defined signal template and can search broad candidate morphologies. | Pardo et al. 2025: https://arxiv.org/html/2505.03927v1 |
| Morphology-agnostic candidate search | Radio dynamic spectra | Attempts to find a wider range of possible signals while retaining sensitivity to classic narrowband drifting signals. | Painter et al. 2024/2025: https://arxiv.org/html/2412.05786v2 |
| SED modeling plus catalog filters | WISE + Gaia + 2MASS | Waste-heat searches require cross-matching, stellar modeling, IR-excess detection, and rejection of dust, galaxies, blends, and bad photometry. | Project Hephaistos II: https://arxiv.org/abs/2405.02927; Project Hephaistos I: https://arxiv.org/abs/2201.11123 |
| CNN confusion/blend detection | WISE image cutouts | WISE has large beams and contamination by background galaxies. CNNs help flag confused sources in candidate selection. | Project Hephaistos II: https://arxiv.org/abs/2405.02927; Blain critique: https://arxiv.org/abs/2409.11447 |
| SETI ellipsoid target selection | TESS + Gaia 3D positions | Uses a shared astrophysical event as a synchronization/Schelling point for possible transmissions or optical signals. | Cabrales et al. 2024: https://arxiv.org/abs/2402.11037 |
| Atmospheric technosignature forward modeling | JWST/Ariel/HWO-style spectra | Tests detectability of industrial gases or artificial greenhouse gases in exoplanet atmospheres. | Artificial greenhouse gases: https://arxiv.org/html/2405.11149v1 |

## Influential and Innovative arXiv Papers

| Paper | Why It Matters | Coding-Agent Takeaway |
|---|---|---|
| Wright et al., “The Case for Technosignatures” https://arxiv.org/abs/2203.10899 | Modern argument for treating technosignatures as a serious astrobiology search target. | Use cautious but non-dismissive priors; compare technosignatures and biosignatures as complementary searches. |
| Sheikh, “Nine axes of merit for technosignature searches” https://www.cambridge.org/core/journals/international-journal-of-astrobiology/article/nine-axes-of-merit-for-technosignature-searches/2F3C599B95AB00A0DF414F1389089D58 | Gives a framework for ranking technosignature strategies. | Encode candidate types by observability, ambiguity, duration, cost, and ancillary benefits. |
| NASA Technosignatures Workshop Report https://www.hou.usra.edu/meetings/technosignatures2018/agenda/Technosignature-Report.pdf | Community roadmap for data-driven technosignature searches. | Good cultural primer for why the field emphasizes false positives and multi-wavelength follow-up. |
| Ma et al., “A deep-learning search for technosignatures of 820 nearby stars” https://arxiv.org/abs/2301.12670 | Landmark deep-learning Breakthrough Listen search; found candidates for re-observation but no confirmed technosignature. | Treat ML hits as signals of interest requiring follow-up, not detections. |
| Suazo et al., “Project Hephaistos II” https://arxiv.org/abs/2405.02927 | High-profile WISE/Gaia/2MASS partial Dyson sphere search with CNN-assisted confusion rejection. | Good template for catalog filters, SED modeling, and candidate-vetting pipeline. |
| Suazo et al., “Project Hephaistos I” https://arxiv.org/abs/2201.11123 | Sets upper limits on partial Dyson spheres using Gaia + AllWISE. | Null results and upper limits are valid scientific outputs. |
| Blain, “Did WISE detect Dyson Spheres/Structures...” https://arxiv.org/abs/2409.11447 | Important critique emphasizing WISE confusion/background galaxies. | Any IR-excess pipeline must model contamination and source blending aggressively. |
| Cabrales et al., “Searching the SN 1987A SETI Ellipsoid with TESS” https://arxiv.org/abs/2402.11037 | Innovative target-selection strategy using Gaia distances and TESS light curves. | Combine astrophysical geometry with time-domain survey data. |
| Artificial greenhouse gases as technosignatures https://arxiv.org/html/2405.11149v1 | Modern atmospheric-technosignature detectability study. | Future JWST/Ariel/HWO-like spectra can be searched for non-biological industrial molecules. |
| Acharyya et al., “A VERITAS/Breakthrough Listen Search for Optical Technosignatures” https://arxiv.org/abs/2306.17680 | Optical pulse technosignature search with real instrument limits. | Encode upper limits, sensitivity, and null results as first-class outputs. |

## Citizen Candidate Vetting and Community Follow-up Best Practices

Goal: make a reproducible anomaly packet that professionals or organized projects can evaluate. Unlike NEO astrometry, there is no single official worldwide clearinghouse for citizen technosignature candidate submission. The best route depends on the candidate type: radio signal, optical light-curve anomaly, IR-excess source, atmospheric spectrum, or optical pulse.

### Best Submission Path

| Candidate Type | Best Path | Practical Notes |
|---|---|---|
| Radio narrowband/drifting signal in public data | Reproduce with open Breakthrough Listen/SETI tools if possible; package dynamic spectra and RFI checks; contact the relevant data/project team or submit a cautious preprint/data note | Must show ON/OFF behavior, Doppler drift plausibility, and RFI rejection. |
| WISE/Gaia/2MASS IR-excess candidate | Build a Project Hephaistos-style candidate packet; cross-check for background galaxies, WISE confusion, debris disks, YSOs, AGB stars; seek multi-wavelength follow-up | Background AGN/dusty galaxies can mimic Dyson-sphere-style excesses. |
| TESS/Kepler anomalous light curve | Check known variable-star classes, eclipsing binaries, instrumental artifacts, contamination, and repeated behavior; share machine-readable light curve plus vetting plots | “Weird” is not “technological.” Most anomalies are astrophysical or instrumental. |
| Optical pulse candidate | Require repeatability, timestamp precision, detector artifact rejection, and independent follow-up | VERITAS/Breakthrough Listen style pulse searches report sensitivity and null results carefully. |
| Atmospheric technosignature claim | Treat as a modeling hypothesis; require spectrum, retrieval assumptions, natural false-positive analysis, and independent observation | Current capabilities are limited; avoid public overclaiming. |

### Minimum Evidence Package

| Item | Required Practice |
|---|---|
| Raw data pointer | Archive URL, observation ID, file checksum, time/frequency/wavelength coverage. |
| Candidate coordinates | Gaia/TIC/2MASS/WISE IDs where applicable; epoch, proper motion handling, cross-match radius. |
| Detection statistic | SNR, anomaly score, model residual, likelihood ratio, or matched-filter score, with method details. |
| Null tests | Neighboring sources, OFF-target observations, other epochs, other frequencies/bands, alternate apertures. |
| Contamination checks | RFI databases/local transmitters for radio; WISE image blends; Gaia RUWE; background AGN/galaxies; dust/cirrus; known variables. |
| Reproducibility | Code, environment, query, model weights if ML, random seeds, and exact preprocessing. |
| Follow-up request | Specific observation needed: band, cadence, sensitivity, sky position, time window, and expected discriminant. |
| Language discipline | Use “candidate,” “anomaly,” or “signal of interest,” not “alien signal.” |

### Radio Technosignature Workflow

1. Confirm the signal appears in ON-target observations and disappears or weakens in OFF-target observations.
2. Check frequency occupancy, known transmitters, satellites, aircraft, observatory RFI logs, and persistent local interference.
3. Measure drift rate and verify whether it is physically plausible for relative acceleration.
4. Confirm it is not broadband impulsive noise, band-edge artifact, harmonic leakage, or known instrumental pattern.
5. Re-run detection with independent preprocessing parameters.
6. Package dynamic spectra, candidate tables, code, and exact data references.
7. Seek re-observation through Breakthrough Listen/SETI community contacts, telescope proposal channels, or a concise public data note.

### IR-Excess / Dyson-Style Workflow

1. Cross-match Gaia, 2MASS, WISE/AllWISE/NEOWISE, Pan-STARRS/SDSS/Legacy Survey where available.
2. Inspect WISE W3/W4 images manually; large WISE beams make blends common.
3. Check for offset radio/IR sources, AGN, dusty galaxies, YSOs, AGB stars, debris disks, and cirrus.
4. Fit ordinary stellar SED plus dust/debris-disk alternatives before invoking waste heat.
5. Use Gaia parallax/proper motion/RUWE to verify the source is a plausible star and not a bad astrometric solution.
6. Request high-resolution imaging or radio/IR follow-up if the candidate survives.

### Time-Domain Optical Workflow

1. Retrieve pixel-level TESS/Kepler data, not only pipeline light curves.
2. Test multiple apertures and contamination scenarios.
3. Check Gaia neighbors, eclipsing-binary catalogs, variable-star catalogs, flares, momentum dumps, scattered light, and background events.
4. Require recurrence or a physically motivated one-off geometry before escalating.
5. Publish a candidate packet with light curve, target-pixel movie/cutouts, diagnostics, and ordinary explanations tested.

### Quality Bar Before Asking for Community Follow-up

| Green Flag | Red Flag |
|---|---|
| Independent pipelines reproduce the anomaly | Appears only with one model/preprocessing path |
| Candidate survives obvious astrophysical/instrumental vetoes | Nearby contaminant or known variable explains it |
| Raw data and code are public | Only a screenshot, social post, or private notebook exists |
| Follow-up observation can discriminate hypotheses | Request is vague or unfalsifiable |
| Language remains cautious | Public claim jumps directly to extraterrestrial intelligence |

### What Not To Do

- Do not contact media before independent expert review.
- Do not publish sky coordinates without a reproducible data packet.
- Do not treat ML anomaly scores as discoveries.
- Do not ignore mundane explanations because the anomaly is interesting.
- Do not optimize a model on the same candidate and then present the score as independent evidence.

### Source Pointers

- NASA Technosignatures Workshop report: https://arxiv.org/abs/1812.08681
- Breakthrough Listen ML search summary: https://seti.berkeley.edu/ml_gbt/
- Ma et al., deep-learning Breakthrough Listen search: https://arxiv.org/abs/2301.12670
- Painter et al., morphology-broad Breakthrough Listen search: https://arxiv.org/html/2412.05786v2
- Pardo et al., anomaly detection in Breakthrough Listen observations: https://arxiv.org/html/2505.03927v1
- Project Hephaistos II: https://arxiv.org/abs/2405.02927
- Blain, WISE/Gaia/2MASS Dyson-candidate critique: https://arxiv.org/abs/2409.11447
- Ren et al., background contamination in Hephaistos candidates: https://arxiv.org/abs/2405.14921
- Ren et al., high-resolution imaging of a contaminated candidate: https://arxiv.org/abs/2501.05152

## Coding-Agent Guidance

1. Never optimize for “alien found.” Optimize for anomaly discovery, contamination rejection, and follow-up priority.
2. Every candidate record should include cross-match provenance: Gaia source ID, WISE source IDs, 2MASS, proper motion, parallax, RUWE, photometric quality flags, image-confusion score, and SED fit residuals.
3. Separate candidate classes: IR excess/waste heat, optical light-curve anomaly, radio dynamic-spectrum anomaly, optical pulses, atmospheric chemistry, and artificial illumination.
4. Build astrophysical veto modules: dusty young stars, AGB stars, background galaxies, blends, cirrus, debris disks, eclipsing binaries, flares, instrumental artifacts, and RFI.
5. Use human-readable evidence packets: plots, cutouts, SEDs, light curves, dynamic spectra, catalog flags, and why each mundane explanation was rejected or not rejected.

## Source URLs

- WISE/NEOWISE IRSA: https://irsa.ipac.caltech.edu/Missions/wise.html
- Gaia archive: https://gea.esac.esa.int/archive/
- Gaia programmatic access: https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access
- TESS MAST: https://archive.stsci.edu/missions-and-data/tess
- Kepler MAST: https://archive.stsci.edu/missions-and-data/kepler
- Breakthrough Listen data/context: https://breakthroughinitiatives.org/initiative/1
- Berkeley SETI ML search: https://seti.berkeley.edu/ml_gbt/
- NASA Technosignatures Workshop Report: https://www.hou.usra.edu/meetings/technosignatures2018/agenda/Technosignature-Report.pdf

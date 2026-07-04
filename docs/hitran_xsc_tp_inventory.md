# HITRAN Cross-section Temperature/Pressure Inventory for CF4, C2F6, C3F8, SF6, and NF3

Date checked: 2026-07-04

## Scope and source

This note inventories the HITRAN absorption cross-section metadata available from `https://hitran.org/xsc/` for the five project gases. It uses the live HITRAN metadata endpoint `https://hitran.org/xsc/get-meta?molecule_id=<ID>` and does not download any `.xsc` data files.

HITRAN describes the absorption cross-section search as the online path for selecting molecules and cross-section datasets, and its documentation states that cross-section headers include wavenumber range, number of points, temperature in K, and pressure in Torr ([HITRAN absorption cross-section search](https://hitran.org/xsc/), [HITRAN cross-section definitions](https://hitran.org/docs/cross-sections-definitions/)).

For the user-specified comparison, 1 millibar to 1 bar is approximately 0.75 to 750 Torr. This note does not infer physical suitability beyond that simple pressure comparison and the listed HITRAN temperatures.

## Executive summary

| Gas | HITRAN molecule ID | Already-downloaded dataset | Listed datasets found | Listed temperature range (K) | Listed pressure range (Torr) | Better pressure coverage than 760 Torr? | Any listed T >= 500 K? | Bottom line |
|---|---:|---:|---:|---:|---:|---|---|---|
| CF4 | 42 | 2827 | 106 | 180.4-323.15 | 0.0228-761.3 | Yes | No | Many alternatives exist, including low-pressure and very-low-pressure entries. Several entries are much closer in pressure to transmission-spectroscopy pressures than the 760 Torr room-temperature file, but all are cold/near-room temperature (180.4-323.15 K), not 500-2000 K. |
| C2F6 | 107 | 2885 | 92 | 180.6-323.15 | 0.0, 24.9-760.3 | Yes | No | Many alternatives exist. Pressures include 0.0 Torr entries and nonzero air-broadened entries from 24.9 Torr up to 760.3 Torr; these improve pressure coverage relative to 760 Torr for some spectral windows, but all temperatures are 180.6-323.15 K. |
| C3F8 | 401 | 2906 | 12 | 278.15-349.9 | 0.0 and 760.0 only | Partial: 0.0 Torr rows only | No | Only 12 entries were listed. Besides the 278/298/323 K, 760 Torr broad N2 files, HITRAN lists 301.3-349.9 K entries at 0.0 Torr over 640-1500 cm^-1. These are vacuum/zero-pressure-labeled rows, not nonzero 1 mbar-1 bar rows, and still far below 500 K. |
| SF6 | 30 | 3032 | 88 | 180-323.15 | 0.00768-760.2 | Yes | No | Many alternatives exist, including very-low-pressure entries around 0.008-0.017 Torr and 7.5 Torr entries for the 780-1100 cm^-1 region, plus broader air-pressure coverage. These are closer in pressure than 760 Torr, but all temperatures are 180.0-323.15 K. |
| NF3 | 55 | 2987 | 3 | 278.15-323.15 | 760-760 | No | No | Only the three broad N2 files are listed: 278.15, 298.15, and 323.15 K, all at 760 Torr. No lower-pressure NF3 cross-section dataset appeared in the HITRAN metadata returned for molecule ID 55. |

## Interpretation for exoplanet use

- None of the HITRAN cross-section datasets returned for these five molecules are in the stated 500-2000 K temperature range.
- CF4 and SF6 have the strongest lower-pressure metadata coverage, including very-low-pressure rows below 1 mbar-equivalent and multiple rows around 7.5 Torr, roughly 10 mbar.
- C2F6 has many lower-pressure rows, but the nonzero lower-pressure rows are mostly 24.9 Torr and above; HITRAN also lists 0.0 Torr rows for selected spectral windows.
- C3F8 has 0.0 Torr rows from 301.3 K to 349.9 K over 640-1500 cm^-1, plus only the broad 760 Torr N2 rows.
- NF3 has no lower-pressure alternatives in the returned metadata; it only has 278.15/298.15/323.15 K at 760 Torr.

## Assumption audit

- The dataset IDs, wavenumber ranges, temperatures, pressures, resolutions, point counts, and broadener labels below are parsed directly from HITRAN's live cross-section metadata table for each molecule ID.
- The note does not claim that any listed dataset is physically valid for a specific exoplanet atmosphere. It only reports available laboratory cross-section metadata and compares listed pressure values to the user-specified rough pressure range.
- The "1 millibar to 1 bar" comparison uses the unit conversion `1 mbar = 0.750061683 Torr`, so the comparison range is approximately `0.75-750 Torr`.
- Rows labeled `p=0.0 Torr` are reported exactly as HITRAN labels them. This note does not reinterpret them as a finite exoplanet pressure.
- Rows with pressures slightly above `750 Torr`, such as `760 Torr`, are not treated as inside the approximate 1-bar upper bound. They are still listed because HITRAN lists them.
- Temperatures are not extrapolated. Since every listed temperature is below 500 K, this note does not recommend any dataset as a hot-Jupiter-temperature match.
- No `.xsc` data file was downloaded while making this note; only metadata pages were queried.

## Recommended next actions for a coding agent

1. Use this note to select candidate dataset IDs. Do not infer unlisted temperature/pressure grids.
2. If lower-pressure coverage is the priority, start with:
   - CF4: low-pressure rows in the `1190.0-1336.0 cm^-1` region, especially dataset IDs `3376`, `3364`, `3380`, `3392`, `3386`, `3388`, `3381`, `3371`, `3365`.
   - SF6: low-pressure rows in the `780.0-1100.0 cm^-1` region, especially dataset IDs `3355`, `3341`, `3358`, `3346`, `3356`, `3351`, `3331`, `3350`, `3322`, `3329`, `3338`, `3353`, `3345`.
   - C2F6: lower nonzero pressure rows are mostly `24.9-75.3 Torr`; also note the `0.0 Torr` rows `2957`, `2958`, and `2959`.
   - C3F8: only the `0.0 Torr` rows `4754-4762` are lower-pressure alternatives; there are no nonzero low-pressure rows in the returned metadata.
   - NF3: no lower-pressure alternatives were found in the returned metadata.
3. Download only the selected dataset IDs after the user approves the exact list. Use the script in "Downloading selected datasets later" so filenames come from HITRAN instead of being guessed.
4. Store raw `.xsc` files with filenames exactly as HITRAN returns them. Also save a manifest containing molecule ID, dataset ID, URL, filename, byte count, and SHA-256 hash.
5. After download, parse each `.xsc` header and verify that the file header temperature, pressure, wavenumber range, and point count match this metadata table before using it in modeling.

## Full dataset inventory

### CF4 (HITRAN molecule ID 42)

Many alternatives exist, including low-pressure and very-low-pressure entries. Several entries are much closer in pressure to transmission-spectroscopy pressures than the 760 Torr room-temperature file, but all are cold/near-room temperature (180.4-323.15 K), not 500-2000 K.

| Dataset ID | Wavenumber range (cm^-1) | T (K) | Pressure (Torr) | Resolution | npts | Broadener |
|---:|---:|---:|---:|---:|---:|---|
| 2829 | 570.0 - 6500.0 | 278.15 | 760.0 | 0.112 cm-1 | 98401 | N2 |
| 2827 | 570.0 - 6500.0 | 298.15 | 760.0 | 0.112 cm-1 | 98401 | N2 |
| 2828 | 570.0 - 6500.0 | 323.15 | 760.0 | 0.112 cm-1 | 98401 | N2 |
| 4669 | 570.0 - 720.0 | 296.1 | 375.1 | 0.04 cm-1 | 8712 | air |
| 4676 | 570.0 - 720.0 | 296.1 | 748.8 | 0.04 cm-1 | 8712 | air |
| 4670 | 850.0 - 950.0 | 296.1 | 375.1 | 0.04 cm-1 | 5808 | air |
| 4677 | 850.0 - 937.0 | 296.1 | 748.8 | 0.04 cm-1 | 5054 | air |
| 4664 | 1020.0 - 1130.0 | 296.1 | 375.1 | 0.04 cm-1 | 6389 | air |
| 4671 | 1020.0 - 1130.0 | 296.1 | 748.8 | 0.04 cm-1 | 6389 | air |
| 4665 | 1130.0 - 1400.0 | 296.1 | 375.1 | 0.04 cm-1 | 15681 | air |
| 4672 | 1130.0 - 1400.0 | 296.1 | 748.8 | 0.04 cm-1 | 15681 | air |
| 3375 | 1190.0 - 1336.0 | 232.9 | 200.8 | 0.015 cm-1 | 58146 | air |
| 3370 | 1190.0 - 1336.0 | 251.0 | 300.9 | 0.015 cm-1 | 29074 | air |
| 3383 | 1190.0 - 1336.0 | 251.0 | 600.4 | 0.015 cm-1 | 29074 | air |
| 3387 | 1190.0 - 1336.0 | 273.1 | 761.3 | 0.03 cm-1 | 29074 | air |
| 3362 | 1190.0 - 1336.0 | 295.0 | 760.5 | 0.03 cm-1 | 29074 | air |
| 3378 | 1190.0 - 1336.0 | 215.7 | 200.3 | 0.015 cm-1 | 58146 | air |
| 3374 | 1190.0 - 1336.0 | 215.8 | 350.3 | 0.015 cm-1 | 58146 | air |
| 3389 | 1190.0 - 1336.0 | 233.1 | 400.1 | 0.015 cm-1 | 58146 | air |
| 3385 | 1190.0 - 1336.0 | 251.0 | 399.9 | 0.015 cm-1 | 58146 | air |
| 3367 | 1190.0 - 1336.0 | 250.9 | 204.0 | 0.015 cm-1 | 58145 | air |
| 3359 | 1190.0 - 1336.0 | 271.1 | 208.6 | 0.015 cm-1 | 58145 | air |
| 3382 | 1190.0 - 1336.0 | 273.1 | 460.7 | 0.015 cm-1 | 58145 | air |
| 3369 | 1190.0 - 1336.0 | 296.2 | 362.3 | 0.015 cm-1 | 58145 | air |
| 3360 | 1190.0 - 1336.0 | 190.0 | 196.9 | 0.015 cm-1 | 58145 | air |
| 3391 | 1190.0 - 1336.0 | 200.0 | 199.8 | 0.015 cm-1 | 58145 | air |
| 3377 | 1190.0 - 1336.0 | 200.0 | 303.5 | 0.015 cm-1 | 58145 | air |
| 3363 | 1190.0 - 1336.0 | 232.9 | 101.5 | 0.015 cm-1 | 116289 | air |
| 3379 | 1190.0 - 1336.0 | 189.7 | 100.1 | 0.015 cm-1 | 116289 | air |
| 3361 | 1190.0 - 1336.0 | 200.1 | 100.3 | 0.015 cm-1 | 116289 | air |
| 3366 | 1190.0 - 1336.0 | 215.7 | 102.1 | 0.015 cm-1 | 116289 | air |
| 3372 | 1190.0 - 1336.0 | 189.5 | 40.18 | 0.0075 cm-1 | 232576 | air |
| 3373 | 1190.0 - 1336.0 | 200.1 | 40.24 | 0.0075 cm-1 | 232576 | air |
| 3384 | 1190.0 - 1336.0 | 215.8 | 40.18 | 0.0075 cm-1 | 232576 | air |
| 3390 | 1190.0 - 1336.0 | 233.1 | 40.27 | 0.0075 cm-1 | 232576 | air |
| 3368 | 1190.0 - 1336.0 | 251.0 | 40.08 | 0.0075 cm-1 | 232576 | air |
| 3364 | 1190.0 - 1336.0 | 213.0 | 0.0382 | 0.0021 cm-1 | 930299 | -- |
| 3388 | 1190.0 - 1336.0 | 190.0 | 7.388 | 0.004 cm-1 | 465150 | air |
| 3371 | 1190.0 - 1336.0 | 213.1 | 7.508 | 0.004 cm-1 | 465150 | air |
| 3365 | 1190.0 - 1336.0 | 240.0 | 7.508 | 0.004 cm-1 | 465150 | air |
| 3381 | 1190.0 - 1336.0 | 270.2 | 7.493 | 0.004 cm-1 | 465150 | air |
| 3376 | 1190.0 - 1336.0 | 190.0 | 0.0228 | 0.0018 cm-1 | 930299 | -- |
| 3380 | 1190.0 - 1336.0 | 240.0 | 0.0519 | 0.0021 cm-1 | 930299 | -- |
| 3386 | 1190.0 - 1336.0 | 270.2 | 0.0675 | 0.0021 cm-1 | 930299 | -- |
| 3392 | 1190.0 - 1336.0 | 292.7 | 0.066 | 0.0021 cm-1 | 930299 | -- |
| 1664 | 1250.0 - 1290.0 | 180.4 | 22.7 | 0.01 cm-1 | 7634 | air |
| 1663 | 1250.0 - 1290.0 | 180.4 | 37.8 | 0.01 cm-1 | 7634 | air |
| 1662 | 1250.0 - 1290.0 | 180.4 | 75.3 | 0.01 cm-1 | 7634 | air |
| 1660 | 1250.0 - 1290.0 | 190.0 | 22.6 | 0.01 cm-1 | 7634 | air |
| 1659 | 1250.0 - 1290.0 | 190.0 | 38.0 | 0.01 cm-1 | 7634 | air |
| 1658 | 1250.0 - 1290.0 | 190.0 | 40.7 | 0.01 cm-1 | 7634 | air |
| 1657 | 1250.0 - 1290.0 | 190.0 | 75.7 | 0.01 cm-1 | 7634 | air |
| 1656 | 1250.0 - 1290.0 | 200.2 | 22.6 | 0.01 cm-1 | 7634 | air |
| 1655 | 1250.0 - 1290.0 | 200.2 | 37.6 | 0.01 cm-1 | 7634 | air |
| 1654 | 1250.0 - 1290.0 | 200.2 | 40.3 | 0.01 cm-1 | 7634 | air |
| 1653 | 1250.0 - 1290.0 | 200.2 | 70.5 | 0.01 cm-1 | 7634 | air |
| 1651 | 1250.0 - 1290.0 | 208.0 | 22.5 | 0.01 cm-1 | 7634 | air |
| 1650 | 1250.0 - 1290.0 | 208.0 | 38.7 | 0.01 cm-1 | 7634 | air |
| 1649 | 1250.0 - 1290.0 | 208.0 | 40.2 | 0.01 cm-1 | 7634 | air |
| 1648 | 1250.0 - 1290.0 | 208.0 | 75.8 | 0.01 cm-1 | 7634 | air |
| 1647 | 1250.0 - 1290.0 | 216.0 | 7.54 | 0.01 cm-1 | 7634 | air |
| 1646 | 1250.0 - 1290.0 | 216.0 | 23.1 | 0.01 cm-1 | 7634 | air |
| 1645 | 1250.0 - 1290.0 | 216.0 | 37.6 | 0.01 cm-1 | 7634 | air |
| 1644 | 1250.0 - 1290.0 | 216.0 | 40.0 | 0.01 cm-1 | 7634 | air |
| 1643 | 1250.0 - 1290.0 | 216.0 | 70.7 | 0.01 cm-1 | 7634 | air |
| 1642 | 1250.0 - 1290.0 | 216.0 | 100.2 | 0.01 cm-1 | 7634 | air |
| 1641 | 1250.0 - 1290.0 | 216.0 | 130.1 | 0.01 cm-1 | 7634 | air |
| 1640 | 1250.0 - 1290.0 | 216.0 | 170.3 | 0.01 cm-1 | 7634 | air |
| 1638 | 1250.0 - 1290.0 | 225.6 | 40.4 | 0.01 cm-1 | 7634 | air |
| 1637 | 1250.0 - 1290.0 | 225.6 | 70.8 | 0.01 cm-1 | 7634 | air |
| 1636 | 1250.0 - 1290.0 | 225.6 | 100.5 | 0.01 cm-1 | 7634 | air |
| 1635 | 1250.0 - 1290.0 | 225.6 | 141.2 | 0.01 cm-1 | 7634 | air |
| 1634 | 1250.0 - 1290.0 | 225.6 | 171.7 | 0.01 cm-1 | 7634 | air |
| 1633 | 1250.0 - 1290.0 | 233.0 | 7.56 | 0.01 cm-1 | 7634 | air |
| 1629 | 1250.0 - 1290.0 | 244.8 | 7.6 | 0.01 cm-1 | 7634 | air |
| 1625 | 1250.0 - 1290.0 | 260.3 | 7.57 | 0.01 cm-1 | 7634 | air |
| 1620 | 1250.0 - 1290.0 | 272.9 | 7.54 | 0.01 cm-1 | 7634 | air |
| 1612 | 1250.0 - 1290.0 | 296.2 | 633.5 | 0.01 cm-1 | 7634 | air |
| 1665 | 1250.0 - 1290.0 | 182.0 | 7.59 | 0.005 cm-1 | 15266 | air |
| 1661 | 1250.0 - 1290.0 | 192.0 | 8.04 | 0.005 cm-1 | 15266 | air |
| 1652 | 1250.0 - 1290.0 | 205.0 | 8.45 | 0.005 cm-1 | 15266 | air |
| 1639 | 1250.0 - 1290.0 | 225.5 | 8.2 | 0.005 cm-1 | 15266 | air |
| 1632 | 1250.0 - 1290.0 | 233.1 | 195.8 | 0.03 cm-1 | 3817 | air |
| 1631 | 1250.0 - 1290.0 | 233.1 | 255.4 | 0.03 cm-1 | 3817 | air |
| 1630 | 1250.0 - 1290.0 | 233.1 | 336.1 | 0.03 cm-1 | 3817 | air |
| 1628 | 1250.0 - 1290.0 | 245.4 | 288.6 | 0.03 cm-1 | 3817 | air |
| 1627 | 1250.0 - 1290.0 | 245.4 | 355.6 | 0.03 cm-1 | 3817 | air |
| 1626 | 1250.0 - 1290.0 | 245.4 | 445.4 | 0.03 cm-1 | 3817 | air |
| 1624 | 1250.0 - 1290.0 | 260.1 | 350.5 | 0.03 cm-1 | 3817 | air |
| 1623 | 1250.0 - 1290.0 | 260.1 | 450.4 | 0.03 cm-1 | 3817 | air |
| 1622 | 1250.0 - 1290.0 | 260.1 | 550.4 | 0.03 cm-1 | 3817 | air |
| 1621 | 1250.0 - 1290.0 | 260.1 | 651.0 | 0.03 cm-1 | 3817 | air |
| 1619 | 1250.0 - 1290.0 | 273.1 | 460.7 | 0.03 cm-1 | 3817 | air |
| 1618 | 1250.0 - 1290.0 | 273.1 | 551.9 | 0.03 cm-1 | 3817 | air |
| 1617 | 1250.0 - 1290.0 | 273.1 | 660.2 | 0.03 cm-1 | 3817 | air |
| 1616 | 1250.0 - 1290.0 | 273.1 | 760.4 | 0.03 cm-1 | 3817 | air |
| 1615 | 1250.0 - 1290.0 | 284.1 | 520.6 | 0.03 cm-1 | 3817 | air |
| 1614 | 1250.0 - 1290.0 | 284.1 | 600.8 | 0.03 cm-1 | 3817 | air |
| 1613 | 1250.0 - 1290.0 | 284.1 | 760.1 | 0.03 cm-1 | 3817 | air |
| 1611 | 1250.0 - 1290.0 | 296.5 | 761.0 | 0.03 cm-1 | 3817 | air |
| 4666 | 1400.0 - 1625.0 | 296.1 | 375.1 | 0.04 cm-1 | 13066 | air |
| 4673 | 1400.0 - 1625.0 | 296.1 | 748.8 | 0.04 cm-1 | 13067 | air |
| 4667 | 1620.0 - 1780.0 | 296.1 | 375.1 | 0.04 cm-1 | 9292 | air |
| 4674 | 1620.0 - 1780.0 | 296.1 | 748.8 | 0.04 cm-1 | 9292 | air |
| 4668 | 1825.0 - 1975.0 | 296.1 | 375.1 | 0.04 cm-1 | 8712 | air |
| 4675 | 1825.0 - 1975.0 | 296.1 | 748.8 | 0.04 cm-1 | 8712 | air |

### C2F6 (HITRAN molecule ID 107)

Many alternatives exist. Pressures include 0.0 Torr entries and nonzero air-broadened entries from 24.9 Torr up to 760.3 Torr; these improve pressure coverage relative to 760 Torr for some spectral windows, but all temperatures are 180.6-323.15 K.

| Dataset ID | Wavenumber range (cm^-1) | T (K) | Pressure (Torr) | Resolution | npts | Broadener |
|---:|---:|---:|---:|---:|---:|---|
| 2887 | 500.0 - 6500.0 | 278.15 | 760.0 | 0.112 cm-1 | 99562 | N2 |
| 2885 | 500.0 - 6500.0 | 298.15 | 760.0 | 0.112 cm-1 | 99562 | N2 |
| 2886 | 500.0 - 6500.0 | 323.15 | 760.0 | 0.112 cm-1 | 99562 | N2 |
| 2957 | 680.0 - 750.0 | 253.0 | 0.0 | 0.03 cm-1 | 4647 | -- |
| 1196 | 1061.0 - 1165.0 | 225.04 | 170.0 | 0.03 cm-1 | 8630 | air |
| 1197 | 1061.0 - 1165.0 | 225.08 | 140.4 | 0.03 cm-1 | 8630 | air |
| 1220 | 1061.0 - 1165.0 | 296.38 | 633.1 | 0.01 cm-1 | 8630 | air |
| 1219 | 1061.0 - 1165.0 | 296.4 | 760.3 | 0.01 cm-1 | 8630 | air |
| 1204 | 1061.0 - 1165.0 | 233.73 | 194.9 | 0.03 cm-1 | 8630 | air |
| 1203 | 1061.0 - 1165.0 | 233.9 | 255.2 | 0.03 cm-1 | 8630 | air |
| 1202 | 1061.0 - 1165.0 | 233.95 | 334.9 | 0.03 cm-1 | 8630 | air |
| 1207 | 1061.0 - 1165.0 | 245.36 | 290.5 | 0.03 cm-1 | 8630 | air |
| 1206 | 1061.0 - 1165.0 | 245.42 | 355.1 | 0.03 cm-1 | 8630 | air |
| 1205 | 1061.0 - 1165.0 | 245.49 | 445.3 | 0.03 cm-1 | 8630 | air |
| 1211 | 1061.0 - 1165.0 | 260.18 | 350.7 | 0.03 cm-1 | 8630 | air |
| 1210 | 1061.0 - 1165.0 | 260.2 | 450.5 | 0.03 cm-1 | 8630 | air |
| 1209 | 1061.0 - 1165.0 | 260.2 | 550.6 | 0.03 cm-1 | 8630 | air |
| 1208 | 1061.0 - 1165.0 | 260.27 | 650.4 | 0.03 cm-1 | 8630 | air |
| 1215 | 1061.0 - 1165.0 | 273.2 | 460.7 | 0.03 cm-1 | 8630 | air |
| 1214 | 1061.0 - 1165.0 | 273.2 | 550.2 | 0.03 cm-1 | 8630 | air |
| 1213 | 1061.0 - 1165.0 | 273.24 | 660.0 | 0.03 cm-1 | 8630 | air |
| 1212 | 1061.0 - 1165.0 | 273.29 | 760.2 | 0.03 cm-1 | 8630 | air |
| 1217 | 1061.0 - 1165.0 | 284.06 | 600.8 | 0.03 cm-1 | 8630 | air |
| 1216 | 1061.0 - 1165.0 | 284.06 | 759.8 | 0.03 cm-1 | 8630 | air |
| 1218 | 1061.0 - 1165.0 | 284.08 | 520.5 | 0.03 cm-1 | 8630 | air |
| 1178 | 1061.0 - 1165.0 | 180.6 | 75.3 | 0.01 cm-1 | 34516 | air |
| 1179 | 1061.0 - 1165.0 | 180.72 | 37.0 | 0.01 cm-1 | 34516 | air |
| 1180 | 1061.0 - 1165.0 | 180.75 | 25.1 | 0.01 cm-1 | 34516 | air |
| 1183 | 1061.0 - 1165.0 | 190.55 | 25.0 | 0.01 cm-1 | 34516 | air |
| 1181 | 1061.0 - 1165.0 | 190.9 | 75.0 | 0.01 cm-1 | 34516 | air |
| 1186 | 1061.0 - 1165.0 | 200.78 | 25.0 | 0.01 cm-1 | 34516 | air |
| 1198 | 1061.0 - 1165.0 | 224.95 | 100.2 | 0.01 cm-1 | 34516 | air |
| 1200 | 1061.0 - 1165.0 | 224.97 | 37.0 | 0.01 cm-1 | 34516 | air |
| 1201 | 1061.0 - 1165.0 | 224.99 | 25.0 | 0.01 cm-1 | 34516 | air |
| 1199 | 1061.0 - 1165.0 | 225.02 | 69.9 | 0.01 cm-1 | 34516 | air |
| 1182 | 1061.0 - 1165.0 | 191.0 | 37.1 | 0.01 cm-1 | 34515 | air |
| 1185 | 1061.0 - 1165.0 | 200.28 | 37.0 | 0.01 cm-1 | 34515 | air |
| 1184 | 1061.0 - 1165.0 | 200.5 | 75.2 | 0.01 cm-1 | 34515 | air |
| 1188 | 1061.0 - 1165.0 | 208.06 | 37.0 | 0.01 cm-1 | 34515 | air |
| 1187 | 1061.0 - 1165.0 | 208.06 | 75.0 | 0.01 cm-1 | 34515 | air |
| 1189 | 1061.0 - 1165.0 | 208.08 | 25.0 | 0.01 cm-1 | 34515 | air |
| 1190 | 1061.0 - 1165.0 | 215.41 | 170.3 | 0.01 cm-1 | 34515 | air |
| 1191 | 1061.0 - 1165.0 | 215.44 | 130.5 | 0.01 cm-1 | 34515 | air |
| 1192 | 1061.0 - 1165.0 | 215.5 | 101.7 | 0.01 cm-1 | 34515 | air |
| 1194 | 1061.0 - 1165.0 | 215.8 | 36.8 | 0.01 cm-1 | 34515 | air |
| 1193 | 1061.0 - 1165.0 | 215.9 | 75.1 | 0.01 cm-1 | 34515 | air |
| 1195 | 1061.0 - 1165.0 | 216.0 | 24.9 | 0.01 cm-1 | 34515 | air |
| 2958 | 1075.0 - 1165.0 | 253.0 | 0.0 | 0.03 cm-1 | 2988 | -- |
| 2959 | 1170.0 - 1380.0 | 253.0 | 0.0 | 0.03 cm-1 | 6970 | -- |
| 1239 | 1220.0 - 1285.0 | 225.04 | 170.0 | 0.03 cm-1 | 5394 | air |
| 1240 | 1220.0 - 1285.0 | 225.08 | 140.4 | 0.03 cm-1 | 5394 | air |
| 1263 | 1220.0 - 1285.0 | 296.38 | 633.1 | 0.01 cm-1 | 5394 | air |
| 1262 | 1220.0 - 1285.0 | 296.4 | 760.3 | 0.01 cm-1 | 5394 | air |
| 1247 | 1220.0 - 1285.0 | 233.73 | 194.9 | 0.03 cm-1 | 5394 | air |
| 1246 | 1220.0 - 1285.0 | 233.9 | 255.2 | 0.03 cm-1 | 5394 | air |
| 1245 | 1220.0 - 1285.0 | 233.95 | 334.9 | 0.03 cm-1 | 5394 | air |
| 1250 | 1220.0 - 1285.0 | 245.36 | 290.5 | 0.03 cm-1 | 5394 | air |
| 1249 | 1220.0 - 1285.0 | 245.42 | 355.1 | 0.03 cm-1 | 5394 | air |
| 1248 | 1220.0 - 1285.0 | 245.49 | 445.3 | 0.03 cm-1 | 5394 | air |
| 1254 | 1220.0 - 1285.0 | 260.18 | 350.7 | 0.03 cm-1 | 5394 | air |
| 1253 | 1220.0 - 1285.0 | 260.2 | 450.5 | 0.03 cm-1 | 5394 | air |
| 1252 | 1220.0 - 1285.0 | 260.2 | 550.6 | 0.03 cm-1 | 5394 | air |
| 1251 | 1220.0 - 1285.0 | 260.27 | 650.4 | 0.03 cm-1 | 5394 | air |
| 1258 | 1220.0 - 1285.0 | 273.2 | 460.7 | 0.03 cm-1 | 5394 | air |
| 1257 | 1220.0 - 1285.0 | 273.2 | 550.2 | 0.03 cm-1 | 5394 | air |
| 1256 | 1220.0 - 1285.0 | 273.24 | 660.0 | 0.03 cm-1 | 5394 | air |
| 1255 | 1220.0 - 1285.0 | 273.29 | 760.2 | 0.03 cm-1 | 5394 | air |
| 1260 | 1220.0 - 1285.0 | 284.06 | 600.8 | 0.03 cm-1 | 5394 | air |
| 1259 | 1220.0 - 1285.0 | 284.06 | 759.8 | 0.03 cm-1 | 5394 | air |
| 1261 | 1220.0 - 1285.0 | 284.08 | 520.5 | 0.03 cm-1 | 5394 | air |
| 1225 | 1220.0 - 1285.0 | 191.0 | 37.1 | 0.01 cm-1 | 21573 | air |
| 1228 | 1220.0 - 1285.0 | 200.28 | 37.0 | 0.01 cm-1 | 21573 | air |
| 1227 | 1220.0 - 1285.0 | 200.5 | 75.2 | 0.01 cm-1 | 21573 | air |
| 1231 | 1220.0 - 1285.0 | 208.06 | 37.0 | 0.01 cm-1 | 21573 | air |
| 1230 | 1220.0 - 1285.0 | 208.06 | 75.0 | 0.01 cm-1 | 21573 | air |
| 1232 | 1220.0 - 1285.0 | 208.08 | 25.0 | 0.01 cm-1 | 21573 | air |
| 1233 | 1220.0 - 1285.0 | 215.41 | 170.3 | 0.01 cm-1 | 21573 | air |
| 1234 | 1220.0 - 1285.0 | 215.44 | 130.5 | 0.01 cm-1 | 21573 | air |
| 1235 | 1220.0 - 1285.0 | 215.5 | 101.7 | 0.01 cm-1 | 21573 | air |
| 1237 | 1220.0 - 1285.0 | 215.8 | 36.8 | 0.01 cm-1 | 21573 | air |
| 1236 | 1220.0 - 1285.0 | 215.9 | 75.1 | 0.01 cm-1 | 21573 | air |
| 1238 | 1220.0 - 1285.0 | 216.0 | 24.9 | 0.01 cm-1 | 21573 | air |
| 1221 | 1220.0 - 1285.0 | 180.6 | 75.3 | 0.01 cm-1 | 21572 | air |
| 1222 | 1220.0 - 1285.0 | 180.72 | 37.0 | 0.01 cm-1 | 21572 | air |
| 1223 | 1220.0 - 1285.0 | 180.75 | 25.1 | 0.01 cm-1 | 21572 | air |
| 1226 | 1220.0 - 1285.0 | 190.55 | 25.0 | 0.01 cm-1 | 21572 | air |
| 1224 | 1220.0 - 1285.0 | 190.9 | 75.0 | 0.01 cm-1 | 21572 | air |
| 1229 | 1220.0 - 1285.0 | 200.78 | 25.0 | 0.01 cm-1 | 21572 | air |
| 1241 | 1220.0 - 1285.0 | 224.95 | 100.2 | 0.01 cm-1 | 21572 | air |
| 1243 | 1220.0 - 1285.0 | 224.97 | 37.0 | 0.01 cm-1 | 21572 | air |
| 1244 | 1220.0 - 1285.0 | 224.99 | 25.0 | 0.01 cm-1 | 21572 | air |
| 1242 | 1220.0 - 1285.0 | 225.02 | 69.9 | 0.01 cm-1 | 21572 | air |

### C3F8 (HITRAN molecule ID 401)

Only 12 entries were listed. Besides the 278/298/323 K, 760 Torr broad N2 files, HITRAN lists 301.3-349.9 K entries at 0.0 Torr over 640-1500 cm^-1. These are vacuum/zero-pressure-labeled rows, not nonzero 1 mbar-1 bar rows, and still far below 500 K.

| Dataset ID | Wavenumber range (cm^-1) | T (K) | Pressure (Torr) | Resolution | npts | Broadener |
|---:|---:|---:|---:|---:|---:|---|
| 2908 | 600.0 - 6500.0 | 278.15 | 760.0 | 0.112 cm-1 | 97902 | N2 |
| 2906 | 600.0 - 6500.0 | 298.15 | 760.0 | 0.112 cm-1 | 97902 | N2 |
| 2907 | 600.0 - 6500.0 | 323.15 | 760.0 | 0.112 cm-1 | 97902 | N2 |
| 4754 | 640.0 - 1500.0 | 301.3 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4755 | 640.0 - 1500.0 | 305.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4756 | 640.0 - 1500.0 | 310.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4757 | 640.0 - 1500.0 | 320.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4758 | 640.0 - 1500.0 | 330.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4759 | 640.0 - 1500.0 | 335.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4760 | 640.0 - 1500.0 | 340.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4761 | 640.0 - 1500.0 | 345.0 | 0.0 | 0.1 cm-1 | 28541 | -- |
| 4762 | 640.0 - 1500.0 | 349.9 | 0.0 | 0.1 cm-1 | 28541 | -- |

### SF6 (HITRAN molecule ID 30)

Many alternatives exist, including very-low-pressure entries around 0.008-0.017 Torr and 7.5 Torr entries for the 780-1100 cm^-1 region, plus broader air-pressure coverage. These are closer in pressure than 760 Torr, but all temperatures are 180.0-323.15 K.

| Dataset ID | Wavenumber range (cm^-1) | T (K) | Pressure (Torr) | Resolution | npts | Broadener |
|---:|---:|---:|---:|---:|---:|---|
| 3034 | 560.0 - 6500.0 | 278.15 | 760.0 | 0.112 cm-1 | 98566 | N2 |
| 3032 | 560.0 - 6500.0 | 298.15 | 760.0 | 0.112 cm-1 | 98566 | N2 |
| 3033 | 560.0 - 6500.0 | 323.15 | 760.0 | 0.112 cm-1 | 98566 | N2 |
| 4654 | 570.0 - 700.0 | 296.1 | 225.5 | 0.04 cm-1 | 7551 | air |
| 4662 | 575.0 - 675.0 | 296.1 | 745.7 | 0.04 cm-1 | 5808 | air |
| 3344 | 780.0 - 1100.0 | 273.9 | 209.2 | 0.0225 cm-1 | 127439 | air |
| 3324 | 780.0 - 1100.0 | 273.9 | 381.3 | 0.03 cm-1 | 127439 | air |
| 3323 | 780.0 - 1100.0 | 273.9 | 750.4 | 0.03 cm-1 | 127439 | air |
| 3330 | 780.0 - 1100.0 | 216.4 | 50.64 | 0.015 cm-1 | 254877 | air |
| 3352 | 780.0 - 1100.0 | 216.4 | 102.0 | 0.015 cm-1 | 254877 | air |
| 3348 | 780.0 - 1100.0 | 216.4 | 360.5 | 0.03 cm-1 | 127439 | air |
| 3327 | 780.0 - 1100.0 | 216.5 | 202.5 | 0.0225 cm-1 | 127439 | air |
| 3339 | 780.0 - 1100.0 | 232.5 | 49.9 | 0.015 cm-1 | 254877 | air |
| 3342 | 780.0 - 1100.0 | 232.5 | 99.81 | 0.015 cm-1 | 254877 | air |
| 3354 | 780.0 - 1100.0 | 232.5 | 201.6 | 0.0225 cm-1 | 127439 | air |
| 3336 | 780.0 - 1100.0 | 232.5 | 404.2 | 0.03 cm-1 | 127439 | air |
| 3328 | 780.0 - 1100.0 | 252.3 | 50.34 | 0.015 cm-1 | 254877 | air |
| 3337 | 780.0 - 1100.0 | 252.3 | 200.8 | 0.0225 cm-1 | 127439 | air |
| 3334 | 780.0 - 1100.0 | 252.3 | 400.6 | 0.03 cm-1 | 127439 | air |
| 3343 | 780.0 - 1100.0 | 252.3 | 600.9 | 0.03 cm-1 | 127439 | air |
| 3326 | 780.0 - 1100.0 | 189.2 | 50.4 | 0.015 cm-1 | 254877 | air |
| 3335 | 780.0 - 1100.0 | 189.2 | 99.92 | 0.015 cm-1 | 254877 | air |
| 3347 | 780.0 - 1100.0 | 189.2 | 201.4 | 0.0225 cm-1 | 127439 | air |
| 3325 | 780.0 - 1100.0 | 202.3 | 51.29 | 0.015 cm-1 | 254877 | air |
| 3333 | 780.0 - 1100.0 | 202.3 | 103.1 | 0.015 cm-1 | 254877 | air |
| 3332 | 780.0 - 1100.0 | 202.3 | 299.8 | 0.03 cm-1 | 127439 | air |
| 3340 | 780.0 - 1100.0 | 202.4 | 200.3 | 0.0225 cm-1 | 127439 | air |
| 3353 | 780.0 - 1100.0 | 252.3 | 7.512 | 0.0045 cm-1 | 1019505 | air |
| 3345 | 780.0 - 1100.0 | 274.0 | 7.522 | 0.0045 cm-1 | 1019505 | air |
| 3329 | 780.0 - 1100.0 | 216.4 | 7.501 | 0.0045 cm-1 | 1019505 | air |
| 3338 | 780.0 - 1100.0 | 232.5 | 7.502 | 0.0045 cm-1 | 1019505 | air |
| 3349 | 780.0 - 1100.0 | 293.0 | 385.0 | 0.03 cm-1 | 127439 | air |
| 3357 | 780.0 - 1100.0 | 293.0 | 750.9 | 0.03 cm-1 | 127439 | air |
| 3350 | 780.0 - 1100.0 | 189.4 | 7.501 | 0.0045 cm-1 | 1019505 | air |
| 3322 | 780.0 - 1100.0 | 202.1 | 7.503 | 0.0045 cm-1 | 1019505 | air |
| 3351 | 780.0 - 1100.0 | 273.7 | 0.01391 | 0.002 cm-1 | 2039009 | -- |
| 3331 | 780.0 - 1100.0 | 294.0 | 0.01694 | 0.002 cm-1 | 2039009 | -- |
| 3341 | 780.0 - 1100.0 | 190.1 | 0.00872 | 0.002 cm-1 | 2039008 | -- |
| 3355 | 780.0 - 1100.0 | 202.1 | 0.00768 | 0.002 cm-1 | 2039008 | -- |
| 3358 | 780.0 - 1100.0 | 216.2 | 0.00935 | 0.002 cm-1 | 2039008 | -- |
| 3346 | 780.0 - 1100.0 | 232.7 | 0.01117 | 0.002 cm-1 | 2039008 | -- |
| 3356 | 780.0 - 1100.0 | 252.3 | 0.01175 | 0.002 cm-1 | 2039008 | -- |
| 4655 | 800.0 - 1100.0 | 296.1 | 225.5 | 0.04 cm-1 | 17423 | air |
| 4663 | 800.0 - 1075.0 | 296.1 | 745.7 | 0.04 cm-1 | 15971 | air |
| 2144 | 925.0 - 955.0 | 245.0 | 287.4 | 0.03 cm-1 | 2739 | air |
| 2156 | 925.0 - 955.0 | 216.0 | 100.1 | 0.03 cm-1 | 2739 | air |
| 2155 | 925.0 - 955.0 | 216.0 | 140.3 | 0.03 cm-1 | 2739 | air |
| 2154 | 925.0 - 955.0 | 216.0 | 170.2 | 0.03 cm-1 | 2739 | air |
| 2150 | 925.0 - 955.0 | 225.0 | 100.7 | 0.03 cm-1 | 2739 | air |
| 2149 | 925.0 - 955.0 | 225.0 | 133.8 | 0.03 cm-1 | 2739 | air |
| 2148 | 925.0 - 955.0 | 225.0 | 170.9 | 0.03 cm-1 | 2739 | air |
| 2147 | 925.0 - 955.0 | 233.0 | 190.1 | 0.03 cm-1 | 2739 | air |
| 2146 | 925.0 - 955.0 | 233.0 | 255.3 | 0.03 cm-1 | 2739 | air |
| 2145 | 925.0 - 955.0 | 233.0 | 331.3 | 0.03 cm-1 | 2739 | air |
| 2143 | 925.0 - 955.0 | 245.0 | 355.1 | 0.03 cm-1 | 2739 | air |
| 2142 | 925.0 - 955.0 | 245.0 | 452.7 | 0.03 cm-1 | 2739 | air |
| 2171 | 925.0 - 955.0 | 180.0 | 20.3 | 0.01 cm-1 | 5477 | air |
| 2170 | 925.0 - 955.0 | 180.0 | 35.6 | 0.01 cm-1 | 5477 | air |
| 2169 | 925.0 - 955.0 | 180.0 | 75.3 | 0.01 cm-1 | 5477 | air |
| 2168 | 925.0 - 955.0 | 190.0 | 25.4 | 0.01 cm-1 | 5477 | air |
| 2167 | 925.0 - 955.0 | 190.0 | 40.5 | 0.01 cm-1 | 5477 | air |
| 2166 | 925.0 - 955.0 | 190.0 | 75.2 | 0.01 cm-1 | 5477 | air |
| 2165 | 925.0 - 955.0 | 200.0 | 21.0 | 0.01 cm-1 | 5477 | air |
| 2164 | 925.0 - 955.0 | 200.0 | 40.2 | 0.01 cm-1 | 5477 | air |
| 2163 | 925.0 - 955.0 | 200.0 | 75.5 | 0.01 cm-1 | 5477 | air |
| 2161 | 925.0 - 955.0 | 215.9 | 25.3 | 0.03 cm-1 | 2988 | -- |
| 2159 | 925.0 - 955.0 | 215.9 | 47.6 | 0.03 cm-1 | 2988 | -- |
| 2157 | 925.0 - 955.0 | 215.9 | 90.0 | 0.03 cm-1 | 2988 | -- |
| 2162 | 925.0 - 955.0 | 216.0 | 20.2 | 0.01 cm-1 | 5477 | air |
| 2160 | 925.0 - 955.0 | 216.0 | 40.5 | 0.01 cm-1 | 5477 | air |
| 2158 | 925.0 - 955.0 | 216.0 | 75.2 | 0.01 cm-1 | 5477 | air |
| 2153 | 925.0 - 955.0 | 225.0 | 20.6 | 0.01 cm-1 | 5477 | air |
| 2152 | 925.0 - 955.0 | 225.0 | 41.1 | 0.01 cm-1 | 5477 | air |
| 2151 | 925.0 - 955.0 | 225.0 | 78.1 | 0.01 cm-1 | 5477 | air |
| 2141 | 925.0 - 955.0 | 273.0 | 550.1 | 0.03 cm-1 | 2988 | air |
| 2140 | 925.0 - 955.0 | 295.0 | 760.2 | 0.03 cm-1 | 2988 | air |
| 4648 | 1100.0 - 1160.0 | 296.1 | 225.5 | 0.04 cm-1 | 3485 | air |
| 4656 | 1100.0 - 1160.0 | 296.1 | 745.7 | 0.04 cm-1 | 3485 | air |
| 4649 | 1220.0 - 1290.0 | 296.1 | 225.5 | 0.04 cm-1 | 4065 | air |
| 4657 | 1220.0 - 1290.0 | 296.1 | 745.7 | 0.04 cm-1 | 4065 | air |
| 4650 | 1340.0 - 1430.0 | 296.1 | 225.5 | 0.04 cm-1 | 5227 | air |
| 4658 | 1340.0 - 1430.0 | 296.1 | 745.7 | 0.04 cm-1 | 5227 | air |
| 4651 | 1420.0 - 1490.0 | 296.1 | 225.5 | 0.04 cm-1 | 4065 | air |
| 4659 | 1420.0 - 1490.0 | 296.1 | 745.7 | 0.04 cm-1 | 4065 | air |
| 4652 | 1515.0 - 1680.0 | 296.1 | 225.5 | 0.04 cm-1 | 9583 | air |
| 4660 | 1515.0 - 1680.0 | 296.1 | 745.7 | 0.04 cm-1 | 9583 | air |
| 4653 | 1670.0 - 1780.0 | 296.1 | 225.5 | 0.04 cm-1 | 6389 | air |
| 4661 | 1670.0 - 1800.0 | 296.1 | 745.7 | 0.04 cm-1 | 7550 | air |

### NF3 (HITRAN molecule ID 55)

Only the three broad N2 files are listed: 278.15, 298.15, and 323.15 K, all at 760 Torr. No lower-pressure NF3 cross-section dataset appeared in the HITRAN metadata returned for molecule ID 55.

| Dataset ID | Wavenumber range (cm^-1) | T (K) | Pressure (Torr) | Resolution | npts | Broadener |
|---:|---:|---:|---:|---:|---:|---|
| 2989 | 600.0 - 6500.0 | 278.15 | 760.0 | 0.112 cm-1 | 97903 | N2 |
| 2987 | 600.0 - 6500.0 | 298.15 | 760.0 | 0.112 cm-1 | 97903 | N2 |
| 2988 | 600.0 - 6500.0 | 323.15 | 760.0 | 0.112 cm-1 | 97903 | N2 |

## Reproduction

This uses only Python standard-library modules and reads metadata only. It does not download any `.xsc` cross-section files.

```bash
python - <<'PY'
import json, re
from html.parser import HTMLParser
from urllib.request import urlopen, Request
from urllib.parse import urlencode

class RowParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.in_tr = False
        self.in_td = False
        self.current = []
        self.buf = []
        self.tr_class = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.in_tr = True
            self.current = []
            self.tr_class = attrs.get("class", "")
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.buf = []
        elif tag == "input" and self.in_td:
            name = attrs.get("name")
            if name:
                self.buf.append(name)

    def handle_data(self, data):
        if self.in_td:
            self.buf.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_td:
            text = " ".join("".join(self.buf).split())
            self.current.append(text)
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            if self.tr_class.startswith("xsec-") and self.current:
                match = re.search(r"xsec-(\d+)", self.tr_class)
                dataset_id = match.group(1) if match else self.current[0]
                self.rows.append((dataset_id, self.current))
            self.in_tr = False

molecules = {"CF4": 42, "C2F6": 107, "C3F8": 401, "SF6": 30, "NF3": 55}

for gas, molecule_id in molecules.items():
    url = "https://hitran.org/xsc/get-meta?" + urlencode({"molecule_id": molecule_id})
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    parser = RowParser()
    parser.feed(payload["html"])

    print(f"\n## {gas} molecule_id={molecule_id}; datasets={len(parser.rows)}")
    for dataset_id, cells in parser.rows:
        print({
            "dataset_id": dataset_id,
            "nu_range_cm-1": cells[1] if len(cells) > 1 else "",
            "T_K": cells[2] if len(cells) > 2 else "",
            "p_Torr": cells[3] if len(cells) > 3 else "",
            "resolution": cells[4] if len(cells) > 4 else "",
            "npts": cells[5] if len(cells) > 5 else "",
            "broadener": cells[6] if len(cells) > 6 else "",
        })
PY
```

## Downloading selected datasets later

The inventory above is enough to choose dataset IDs. To retrieve actual `.xsc` files later, do not guess filenames. HITRAN's step-2 page for a selected dataset exposes the concrete `.xsc` download link. The following script logs in with user-provided HITRAN credentials, requests one selected dataset ID at a time, discovers the `.xsc` link on the returned page, downloads it, and writes a manifest with SHA-256 hashes.

Credential handling:

- Do not hard-code credentials in source files.
- Set credentials in environment variables only for the command invocation:
  - `HITRAN_EMAIL`
  - `HITRAN_PASSWORD`
- The script below exits if either variable is missing.

Example:

```bash
python -m pip install requests beautifulsoup4

HITRAN_EMAIL='you@example.com' \
HITRAN_PASSWORD='your-password' \
python download_selected_hitran_xsc.py 3376 3364 3380 3355 3341
```

Save this as `download_selected_hitran_xsc.py`:

```python
import csv
import hashlib
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://hitran.org"
OUTDIR = Path("hitran_xsc_selected")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def login(session: requests.Session, email: str, password: str) -> None:
    login_url = f"{BASE}/login/"
    response = session.get(login_url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if csrf_input is None or not csrf_input.get("value"):
        raise RuntimeError("Could not find HITRAN login CSRF token")

    payload = {
        "csrfmiddlewaretoken": csrf_input["value"],
        "email": email,
        "password": password,
    }
    response = session.post(
        login_url,
        data=payload,
        headers={"Referer": login_url},
        timeout=30,
    )
    response.raise_for_status()

    if "/login/" in response.url:
        raise RuntimeError("HITRAN login did not complete; check credentials")


def discover_xsc_links(session: requests.Session, dataset_id: str) -> list[str]:
    response = session.get(
        f"{BASE}/xsc/2",
        params={dataset_id: "on"},
        headers={"Referer": f"{BASE}/xsc/"},
        timeout=60,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".xsc") and "/data/xsec/" in href:
            links.append(urljoin(BASE, href))

    if not links:
        raise RuntimeError(f"No .xsc download link found for dataset ID {dataset_id}")

    return sorted(set(links))


def download(session: requests.Session, url: str, outdir: Path) -> tuple[str, int, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    filename = url.rsplit("/", 1)[-1]
    path = outdir / filename

    response = session.get(url, timeout=120)
    response.raise_for_status()
    data = response.content
    path.write_bytes(data)

    sha256 = hashlib.sha256(data).hexdigest()
    return str(path), len(data), sha256


def main() -> None:
    dataset_ids = sys.argv[1:]
    if not dataset_ids:
        raise SystemExit("Usage: python download_selected_hitran_xsc.py <dataset_id> [<dataset_id> ...]")

    email = require_env("HITRAN_EMAIL")
    password = require_env("HITRAN_PASSWORD")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    login(session, email, password)

    manifest_rows = []
    for dataset_id in dataset_ids:
        links = discover_xsc_links(session, dataset_id)
        for url in links:
            path, byte_count, sha256 = download(session, url, OUTDIR)
            manifest_rows.append({
                "dataset_id": dataset_id,
                "url": url,
                "path": path,
                "bytes": byte_count,
                "sha256": sha256,
            })
            print(f"{dataset_id}: downloaded {path} ({byte_count} bytes)")

    manifest_path = OUTDIR / "manifest.csv"
    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset_id", "url", "path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
```

## Post-download verification

After downloading, verify every `.xsc` file before modeling. The first line of each HITRAN `.xsc` file is the header described in HITRAN's cross-section definitions: molecule, minimum wavenumber, maximum wavenumber, number of points, temperature, pressure, maximum cross-section, resolution, common name, broadener, and reference index. The coding agent should compare that header against the selected row in this Markdown table.

Minimum validation checklist:

- Dataset ID selected intentionally from this note.
- Download URL discovered from HITRAN, not guessed.
- File extension is `.xsc`.
- Header molecule matches the intended gas.
- Header temperature and pressure match the selected HITRAN metadata row.
- Header wavenumber range and `npts` match the selected HITRAN metadata row.
- Parsed cross-section value count equals header `npts`.
- SHA-256 hash and byte count recorded in `manifest.csv`.

- `rule1 = 0.5`, `smallChange = 1.0`
- `rule2 = 0.5`, `mediumChange = 3.0`
- `rule3 = 0.0`, `bigChange = 5.0`
- Hasil:
  ```
  throttleChangeValue = (0.5 * 1.0 + 0.5 * 3.0 + 0.0 * 5.0) / (0.5 + 0.5 + 0.0 + 0.001) = 2.0
  ```

- **Reduksi Perubahan**:
- Jika `rule4 > 0`, maka:
  ```
  throttleChangeValue = throttleChangeValue * (1.0 - rule4 * reduceFactor)
  ```
- Dalam contoh ini, `rule4 = 0.0`, sehingga tidak ada reduksi.

- **Arah Perubahan**:
- Jika `error < 0` (RPM terlalu tinggi), maka `throttleChange = -throttleChange`.

### Hasil Akhir:
- `throttleChange = round(2.0) = 2`
- Karena `error = 200` (positif, RPM terlalu rendah), throttle ditambah sebesar `2`.

---

## 5. Ringkasan Proses Fuzzy Logic
| **Langkah**         | **Input/Proses**                          | **Output**                     |
|----------------------|-------------------------------------------|--------------------------------|
| **Fuzzifikasi**      | `error = 200`, `errorChange = 50`         | `smallError = 0.5`, `mediumError = 0.5`, `smallDelta = 1.0` |
| **Inferensi**        | Rule 1: `0.5`, Rule 2: `0.5`, Rule 3: `0.0` | `throttleChangeValue = 2.0`    |
| **Defuzzifikasi**    | Weighted average, arah perubahan          | `throttleChange = +2`          |

---

## 6. Contoh Lain
### Kasus:
- `error = 500` (kategori **big** dengan `bigError = 1.0`)
- `errorChange = 200` (kategori **medium** dengan `mediumDelta = 0.5`)

| **Langkah**         | **Input/Proses**                          | **Output**                     |
|----------------------|-------------------------------------------|--------------------------------|
| **Fuzzifikasi**      | `error = 500`, `errorChange = 200`        | `bigError = 1.0`, `mediumDelta = 0.5` |
| **Inferensi**        | Rule 3: `1.0`, Rule 4: `0.5`              | `throttleChangeValue = 5.0`    |
| **Defuzzifikasi**    | Reduksi: `5.0 * (1.0 - 0.5 * 0.5) = 3.75` | `throttleChange = +4`          |

---

Dengan tabel ini, proses fuzzy logic dapat dipahami secara visual dan sistematis.
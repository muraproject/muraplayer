# Fuzzy Logic untuk Kontrol RPM Motor BLDC

Program ini menggunakan fuzzy logic untuk mengontrol RPM motor BLDC. Berikut adalah penjelasan langkah-langkahnya:

---

## 1. Fuzzifikasi
Fuzzifikasi mengubah input numerik (error dan perubahan error) menjadi derajat keanggotaan (membership value) dalam kategori fuzzy.

### Kategori untuk Error (`rpmError`)
| **Error (absError)** | **Small Error** | **Medium Error** | **Big Error** |
|-----------------------|-----------------|------------------|---------------|
| `<= 100`             | 1.0             | 0.0              | 0.0           |
| `100 < error <= 300` | Menurun (1.0 → 0.0) | Meningkat (0.0 → 1.0) | 0.0           |
| `300 < error <= 700` | 0.0             | Menurun (1.0 → 0.0) | Meningkat (0.0 → 1.0) |
| `> 700`              | 0.0             | 0.0              | 1.0           |

### Kategori untuk Perubahan Error (`rpmErrorChange`)
| **Perubahan Error (absErrorChange)** | **Small Delta** | **Medium Delta** | **Big Delta** |
|--------------------------------------|-----------------|------------------|---------------|
| `<= 50`                              | 1.0             | 0.0              | 0.0           |
| `50 < errorChange <= 150`            | Menurun (1.0 → 0.0) | Meningkat (0.0 → 1.0) | 0.0           |
| `150 < errorChange <= 300`           | 0.0             | Menurun (1.0 → 0.0) | Meningkat (0.0 → 1.0) |
| `> 300`                              | 0.0             | 0.0              | 1.0           |

---

## 2. Aturan Fuzzy (Fuzzy Rules)
Aturan fuzzy digunakan untuk menentukan perubahan throttle berdasarkan kombinasi error dan perubahan error.

| **Rule** | **Error**       | **Perubahan Error** | **Output (Throttle Change)** |
|----------|-----------------|---------------------|------------------------------|
| 1        | Small           | Small               | Small Change (+1.0)          |
| 2        | Medium          | Small               | Medium Change (+3.0)         |
| 3        | Big             | -                   | Big Change (+5.0)            |
| 4        | -               | Big                 | Reduce Change (×0.5)         |

---

## 3. Inferensi
Inferensi menghitung kekuatan setiap aturan berdasarkan derajat keanggotaan input.

### Contoh Kasus:
- `error = 200` (kategori **medium** dengan `mediumError = 0.5`)
- `errorChange = 50` (kategori **small** dengan `smallDelta = 1.0`)

| **Rule** | **Error**       | **Perubahan Error** | **Strength (min)** | **Output**         |
|----------|-----------------|---------------------|--------------------|--------------------|
| 1        | Small (0.5)     | Small (1.0)         | `min(0.5, 1.0) = 0.5` | Small Change (+1.0) |
| 2        | Medium (0.5)    | Small (1.0)         | `min(0.5, 1.0) = 0.5` | Medium Change (+3.0) |
| 3        | Big (0.0)       | -                   | `0.0`              | Big Change (+5.0)  |
| 4        | -               | Big (0.0)           | `0.0`              | Reduce Change (×0.5) |

---

## 4. Defuzzifikasi
Defuzzifikasi mengubah output fuzzy menjadi nilai numerik menggunakan metode **weighted average**.

### Perhitungan:
- **Weighted Average**:
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

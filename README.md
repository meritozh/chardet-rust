# chardet-rs

A pure Rust implementation of universal character encoding detection. Ported from the Python `chardet` library.

## Features

- Detect encoding from byte streams
- Support for 60+ encodings including UTF-8/16/32, ISO-8859 series, Windows codepages, EBCDIC, and legacy encodings
- Multi-stage detection pipeline: BOM → structural → statistical analysis
- Configurable encoding era filters (modern web, legacy, etc.)
- Zero dependencies on Python - pure Rust implementation

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
chardet-rs = "0.1"
```

## Quick Start

```rust
use chardet_rs::{detect_bytes, EncodingEra};

// Detect encoding from bytes
let result = detect_bytes(b"Hello world", EncodingEra::All, 200_000);

println!("Encoding: {:?}", result.encoding);  // Some("ascii")
println!("Confidence: {:.2}", result.confidence);  // 1.00
```

## API Reference

### Core Functions

#### `detect_bytes`

Detect the most likely encoding of a byte slice.

```rust
use chardet_rs::{detect_bytes, EncodingEra};

let result = detect_bytes(
    b"\xef\xbb\xbfHello",  // UTF-8 with BOM
    EncodingEra::All,      // Consider all encoding eras
    200_000                // Max bytes to analyze
);

assert_eq!(result.encoding, Some("utf-8-sig".to_string()));
assert_eq!(result.confidence, 1.0);  // BOM = absolute confidence
```

**Parameters:**
- `data: &[u8]` - Byte slice to analyze
- `encoding_era: EncodingEra` - Filter for encoding categories (see below)
- `max_bytes: usize` - Maximum bytes to analyze (default: 200KB)

**Returns:** `DetectionResult` with:
- `encoding: Option<String>` - Detected encoding name, or `None` for binary
- `confidence: f64` - Score from 0.0 to 1.0
- `language: Option<String>` - ISO 639-1 language code if detected

#### `detect_all_bytes`

Get all candidate encodings sorted by confidence.

```rust
use chardet_rs::{detect_all_bytes, EncodingEra};

let results = detect_all_bytes(
    b"Héllo wörld café",
    EncodingEra::All,
    200_000,
    false  // Filter results below 20% confidence threshold
);

for result in &results {
    println!("{}: {:.2}%", 
        result.encoding.as_deref().unwrap_or("binary"),
        result.confidence * 100.0
    );
}
```

**Parameters:**
- `data: &[u8]` - Byte slice to analyze
- `encoding_era: EncodingEra` - Encoding category filter
- `max_bytes: usize` - Maximum bytes to analyze
- `ignore_threshold: bool` - If `false`, exclude results with confidence < 0.20

**Returns:** `Vec<DetectionResult>` sorted by confidence (highest first)

### Encoding Era Filter

Control which encoding categories to consider:

```rust
use chardet_rs::EncodingEra;

// Modern web encodings only (UTF-8, Windows-1252, etc.)
detect_bytes(data, EncodingEra::ModernWeb, max_bytes);

// Include legacy ISO encodings
detect_bytes(data, EncodingEra::ModernWeb | EncodingEra::LegacyIso, max_bytes);

// All encodings (default)
detect_bytes(data, EncodingEra::All, max_bytes);
```

**Available Eras:**

| Era | Description | Examples |
|-----|-------------|----------|
| `ModernWeb` | Modern browser-supported | UTF-8, Windows-1252 |
| `LegacyIso` | ISO-8859 series | ISO-8859-1, ISO-8859-5 |
| `LegacyMac` | Classic Mac encodings | MacRoman, MacCyrillic |
| `LegacyRegional` | Regional legacy | UTF-7, HZ-GB-2312 |
| `Dos` | DOS codepages | CP437, CP850 |
| `Mainframe` | EBCDIC | CP273, CP500 |
| `All` | All encodings | Default, all above |

### DetectionResult

```rust
pub struct DetectionResult {
    pub encoding: Option<String>,  // Encoding name or None for binary
    pub confidence: f64,           // 0.0 to 1.0
    pub language: Option<String>,  // ISO 639-1 code (e.g., "en", "ru")
}
```

**Confidence Levels:**
- `1.0` - Absolute confidence (BOM detection)
- `0.95` - High confidence (structural detection)
- `0.50-0.95` - Good confidence (statistical match)
- `<0.20` - Low confidence (filtered out by default)

## Examples

### UTF-8 Detection

```rust
use chardet_rs::{detect_bytes, EncodingEra};

// UTF-8 with multibyte characters
let text = "Héllo wörld café".as_bytes();
let result = detect_bytes(text, EncodingEra::All, 200_000);
assert_eq!(result.encoding, Some("utf-8".to_string()));

// UTF-8 with BOM
let result = detect_bytes(b"\xef\xbb\xbfHello", EncodingEra::All, 200_000);
assert_eq!(result.encoding, Some("utf-8-sig".to_string()));
assert_eq!(result.confidence, 1.0);
```

### Legacy Encoding Detection

```rust
use chardet_rs::{detect_bytes, EncodingEra};

// UTF-7 (requires LegacyRegional era)
let utf7_data = b"Hello, +ZeVnLIqe-!";
let result = detect_bytes(utf7_data, EncodingEra::All, 200_000);
assert_eq!(result.encoding, Some("utf-7".to_string()));

// Won't detect UTF-7 with ModernWeb filter (deprecated in browsers)
let result = detect_bytes(utf7_data, EncodingEra::ModernWeb, 200_000);
assert_ne!(result.encoding, Some("utf-7".to_string()));
```

### Binary Detection

```rust
use chardet_rs::{detect_bytes, EncodingEra};

let binary_data = &[0x00, 0xFF, 0xFE, 0x00, 0x01, 0x02];
let result = detect_bytes(binary_data, EncodingEra::All, 200_000);

assert_eq!(result.encoding, None);  // Binary content
```

### Encoding from File

```rust
use std::fs::File;
use std::io::Read;
use chardet_rs::{detect_bytes, EncodingEra};

let mut file = File::open("document.txt")?;
let mut buffer = Vec::new();
file.read_to_end(&mut buffer)?;

let result = detect_bytes(&buffer, EncodingEra::All, 200_000);
println!("Detected: {:?}", result.encoding);
```

### Large Files

For large files, limit analysis to first N bytes:

```rust
use chardet_rs::{detect_bytes, EncodingEra};

// Only analyze first 50KB (faster for large files)
let result = detect_bytes(&large_data, EncodingEra::All, 50_000);
```

## Detection Pipeline

The library uses a multi-stage detection pipeline:

1. **Stage 0: Deterministic Detection**
   - BOM detection (UTF-8/16/32)
   - UTF-16/32 pattern detection
   - Binary detection
   - Escape sequence encodings (ISO-2022, HZ-GB-2312, UTF-7)

2. **Stage 1: Markup & Basic**
   - HTML/XML charset extraction
   - ASCII detection
   - UTF-8 validation

3. **Stage 2: Structural Analysis**
   - Byte validity filtering
   - CJK multi-byte structural probing

4. **Stage 3: Statistical Analysis**
   - Bigram model scoring
   - Confusion group resolution

Most detections complete at early stages for efficiency.

## Supported Encodings

- **Unicode:** UTF-8, UTF-8-SIG, UTF-16, UTF-16BE, UTF-16LE, UTF-32, UTF-32BE, UTF-32LE
- **Western:** ISO-8859-1, ISO-8859-15, Windows-1252
- **Eastern European:** ISO-8859-2, Windows-1250
- **Russian:** ISO-8859-5, Windows-1251, KOI8-R, MacCyrillic
- **Greek:** ISO-8859-7, Windows-1253
- **Turkish:** ISO-8859-9, Windows-1254
- **Chinese:** GB2312, GB18030, Big5, HZ-GB-2312
- **Japanese:** Shift_JIS, EUC-JP, ISO-2022-JP
- **Korean:** EUC-KR, ISO-2022-KR
- **Legacy:** UTF-7, MacRoman, CP437, EBCDIC variants

## License

0BSD - Free for any use. No restrictions.

## Credits

Ported from Python `chardet` library. Original implementation by Dan Blanchard.
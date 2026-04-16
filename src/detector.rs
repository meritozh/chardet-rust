//! Core detection APIs.

use crate::enums::EncodingEra;
use crate::pipeline::orchestrator::run_pipeline;
use crate::pipeline::{DetectionResult, MINIMUM_THRESHOLD};

/// Detect the encoding of a byte string.
///
/// Returns the most likely encoding with confidence score.
///
/// # Arguments
///
/// * `data` - Byte slice to analyze
/// * `encoding_era` - Filter for which encoding categories to consider
/// * `max_bytes` - Maximum bytes to analyze (large values may impact performance)
///
/// # Returns
///
/// A `DetectionResult` with encoding name, confidence, and optional language.
///
/// # Examples
///
/// ```
/// use chardet_rs::{detect_bytes, EncodingEra};
///
/// // Detect UTF-8 with BOM
/// let result = detect_bytes(b"\xef\xbb\xbfHello", EncodingEra::All, 200_000);
/// assert_eq!(result.encoding, Some("utf-8-sig".to_string()));
///
/// // Detect ASCII
/// let result = detect_bytes(b"Hello world", EncodingEra::All, 200_000);
/// assert!(result.confidence > 0.0);
/// ```
pub fn detect_bytes(data: &[u8], encoding_era: EncodingEra, max_bytes: usize) -> DetectionResult {
    run_pipeline(data, encoding_era, max_bytes)
        .into_iter()
        .next()
        .unwrap_or_default()
}

/// Detect all possible encodings of the given byte string.
///
/// Returns all candidate encodings sorted by confidence (highest first).
///
/// # Arguments
///
/// * `data` - Byte slice to analyze
/// * `encoding_era` - Filter for which encoding categories to consider
/// * `max_bytes` - Maximum bytes to analyze
/// * `ignore_threshold` - If false, filter out results below MINIMUM_THRESHOLD (0.20)
///
/// # Returns
///
/// A vector of `DetectionResult` sorted by confidence.
///
/// # Examples
///
/// ```
/// use chardet_rs::{detect_all_bytes, EncodingEra};
///
/// let results = detect_all_bytes(b"Hello world", EncodingEra::All, 200_000, true);
/// assert!(!results.is_empty());
///
/// // Results are sorted by confidence (highest first)
/// for result in &results {
///     println!("{}: {:.2}", result.encoding.as_deref().unwrap_or("binary"), result.confidence);
/// }
/// ```
pub fn detect_all_bytes(
    data: &[u8],
    encoding_era: EncodingEra,
    max_bytes: usize,
    ignore_threshold: bool,
) -> Vec<DetectionResult> {
    let results = run_pipeline(data, encoding_era, max_bytes);

    if !ignore_threshold {
        let filtered: Vec<_> = results
            .iter()
            .filter(|r| r.confidence > MINIMUM_THRESHOLD)
            .cloned()
            .collect();

        if !filtered.is_empty() {
            return filtered;
        }
    }

    results
}
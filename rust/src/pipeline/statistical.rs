//! Stage 3: Statistical bigram scoring.

use crate::pipeline::DetectionResult;
use crate::registry::EncodingInfo;

/// Score all candidates and return results sorted by confidence descending.
pub fn score_candidates(
    data: &[u8],
    candidates: &[&EncodingInfo],
) -> Vec<DetectionResult> {
    if data.is_empty() || candidates.is_empty() {
        return vec![];
    }
    
    let mut scores: Vec<(String, f64, Option<String>)> = Vec::new();
    
    // Create a simple frequency profile of the data
    let profile = create_byte_profile(data);
    
    for enc in candidates {
        let score = score_encoding(data, enc, &profile);
        if score > 0.0 {
            // Infer language for single-language encodings
            let language = if enc.languages.len() == 1 {
                Some(enc.languages[0].to_string())
            } else {
                None
            };
            scores.push((enc.name.to_string(), score, language));
        }
    }
    
    // Sort by confidence descending
    scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    
    scores.into_iter()
        .map(|(name, conf, lang)| DetectionResult::new(
            Some(&name),
            conf.min(1.0),
            lang.as_deref(),
        ))
        .collect()
}

/// A simple byte frequency profile.
pub struct ByteProfile {
    /// Byte frequencies (0-255)
    pub frequencies: [u32; 256],
    /// Bigram frequencies (simplified - just first 65536 slots)
    pub bigrams: std::collections::HashMap<u16, u32>,
    /// Total byte count
    pub total: usize,
}

impl Default for ByteProfile {
    fn default() -> Self {
        Self {
            frequencies: [0; 256],
            bigrams: std::collections::HashMap::new(),
            total: 0,
        }
    }
}

fn create_byte_profile(data: &[u8]) -> ByteProfile {
    let mut profile = ByteProfile::default();
    profile.total = data.len();
    
    for &b in data {
        profile.frequencies[b as usize] += 1;
    }
    
    // Create bigrams
    for window in data.windows(2) {
        let bigram = ((window[0] as u16) << 8) | (window[1] as u16);
        *profile.bigrams.entry(bigram).or_insert(0) += 1;
    }
    
    profile
}

fn score_encoding(_data: &[u8], enc: &EncodingInfo, profile: &ByteProfile) -> f64 {
    // Simplified scoring based on byte distribution patterns
    // In the full implementation, this would use pre-trained bigram models
    
    let non_ascii_count: u32 = profile.frequencies[128..].iter().sum();
    let total_bytes = profile.total as f64;
    
    if total_bytes == 0.0 {
        return 0.0;
    }
    
    // Base score on ASCII vs non-ASCII ratio
    let ascii_ratio = (profile.total as u32 - non_ascii_count) as f64 / total_bytes;
    
    match enc.name {
        // Encodings that are mostly ASCII-compatible
        "utf-8" | "ascii" => {
            // High ASCII ratio is good, but some multi-byte is expected for UTF-8
            if enc.name == "utf-8" && non_ascii_count > 0 {
                0.95
            } else if enc.name == "ascii" && non_ascii_count == 0 {
                1.0
            } else {
                0.0
            }
        }
        // Single-byte encodings typically have high non-ASCII usage
        _ if !enc.is_multibyte => {
            if non_ascii_count > 0 {
                // Score based on distribution characteristics
                let high_byte_entropy = calculate_entropy(&profile.frequencies[128..]);
                // Most single-byte encodings have fairly uniform distribution of high bytes
                0.5 + high_byte_entropy * 0.5
            } else {
                // Pure ASCII - could be any single-byte encoding
                0.3
            }
        }
        // Multi-byte encodings
        _ => {
            if non_ascii_count > 0 {
                // Check for valid multi-byte patterns
                score_multibyte_patterns(enc.name, profile)
            } else {
                0.0
            }
        }
    }
}

fn score_multibyte_patterns(name: &str, profile: &ByteProfile) -> f64 {
    // Check byte patterns characteristic of specific encodings
    match name {
        "shift_jis_2004" | "cp932" => {
            // Look for common Shift_JIS patterns
            let lead_range_1: u32 = profile.frequencies[0x81..=0x9F].iter().sum();
            let lead_range_2: u32 = profile.frequencies[0xE0..=0xEF].iter().sum();
            let has_valid_leads = lead_range_1 + lead_range_2 > 0;
            if has_valid_leads { 0.85 } else { 0.1 }
        }
        "euc-jis-2004" | "euc-jp" => {
            // EUC-JP uses 0xA1-0xFE for both bytes
            let high_range: u32 = profile.frequencies[0xA1..=0xFE].iter().sum();
            if high_range > 0 { 0.85 } else { 0.1 }
        }
        "euc-kr" | "cp949" => {
            // EUC-KR uses 0xA1-0xFE
            let high_range: u32 = profile.frequencies[0xA1..=0xFE].iter().sum();
            if high_range > 0 { 0.85 } else { 0.1 }
        }
        "gb18030" | "gb2312" => {
            // GB uses 0xA1-0xFE for GB2312, 0x81-0xFE for GBK
            let high_range: u32 = profile.frequencies[0x81..=0xFE].iter().sum();
            if high_range > 0 { 0.85 } else { 0.1 }
        }
        "big5hkscs" | "big5" => {
            // Big5 uses 0xA1-0xF9 for first byte
            let lead_range: u32 = profile.frequencies[0xA1..=0xF9].iter().sum();
            if lead_range > 0 { 0.85 } else { 0.1 }
        }
        _ => 0.5, // Unknown multi-byte encoding
    }
}

fn calculate_entropy(frequencies: &[u32]) -> f64 {
    let total: u32 = frequencies.iter().sum();
    if total == 0 {
        return 0.0;
    }
    
    let total_f = total as f64;
    let mut entropy = 0.0;
    
    for &count in frequencies {
        if count > 0 {
            let p = count as f64 / total_f;
            entropy -= p * p.log2();
        }
    }
    
    // Normalize to 0-1 range (max entropy for 128 values is log2(128) = 7)
    entropy / 7.0
}
